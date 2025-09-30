"""
SDK-backed Metronome client adapter.
This adapter mirrors the interface used by the API layer and delegates
to the official Metronome Python SDK where available.

Note: SDK-first implementation. For one missing endpoint (threshold
billing release), this client makes a minimal direct HTTP call using the
same bearer token and base URL as the SDK. Replace with the official SDK
method when available.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timezone

from app.core.config import settings


logger = logging.getLogger(__name__)


class SdkMetronomeClient:
    def __init__(self) -> None:
        try:
            # Official SDK import
            from metronome import AsyncMetronome  # type: ignore
        except Exception as e:  # ImportError
            raise RuntimeError(
                "Metronome SDK not installed. Please `pip install metronome-sdk`."
            ) from e

        bearer = settings.METRONOME_API_KEY
        base_url = settings.METRONOME_API_URL
        if not bearer:
            raise ValueError("METRONOME_API_KEY not configured in environment")

        try:
            # The SDK expects 'bearer_token' and optional 'base_url'
            self._sdk = AsyncMetronome(bearer_token=bearer, base_url=base_url)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Metronome SDK client: {e}")

        logger.info("Initialized SdkMetronomeClient (Async)")

    # ---- Customers ----
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Placeholder mapping; adjust to SDK's shape
            resp = await self._sdk.v1.customers.create(  # type: ignore[attr-defined]
                name=customer_data["name"],
                ingest_aliases=[customer_data["external_id"]],
            )
            # Response type: CustomerCreateResponse with .data.id
            data = getattr(resp, "data", None) or resp
            customer_id = getattr(data, "id", None)
            if not customer_id:
                raise RuntimeError("SDK did not return a customer id")
            return {
                "id": customer_id,
                "external_id": customer_data["external_id"],
                "name": customer_data["name"],
                "email": customer_data.get("email"),
                "ingest_aliases": [customer_data["external_id"]],
            }
        except Exception as e:
            raise RuntimeError(f"SDK create_customer failed: {e}")

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        try:
            resp = await self._sdk.v1.customers.retrieve(customer_id=customer_id)  # type: ignore[attr-defined]
            data = getattr(resp, "data", None)
            # SDK BaseModel exposes model_dump(); fallback to dict-like
            if hasattr(data, "model_dump"):
                return data.model_dump()
            return {"id": customer_id}
        except Exception as e:
            raise RuntimeError(f"SDK get_customer failed: {e}")

    async def set_customer_aliases(self, customer_id: str, aliases: List[str]) -> Dict[str, Any]:
        try:
            await self._sdk.v1.customers.set_ingest_aliases(customer_id=customer_id, ingest_aliases=aliases)  # type: ignore[attr-defined]
            return {"success": True, "customer_id": customer_id, "aliases": aliases}
        except Exception as e:
            raise RuntimeError(f"SDK set_customer_aliases failed: {e}")

    # ---- Contract Pricing ----
    async def get_rate_card(self, rate_card_name: Optional[str] = None) -> Optional[str]:
        try:
            rc_name = rate_card_name or settings.METRONOME_RATE_CARD_NAME
            if not rc_name:
                raise ValueError("METRONOME_RATE_CARD_NAME is not set in environment")
            target = rc_name.strip().lower()
            page = await self._sdk.v1.contracts.rate_cards.list(body={})  # type: ignore[attr-defined]
            cards = getattr(page, "data", []) or []
            for rc in cards:
                name = getattr(rc, "name", "") or ""
                if name.strip().lower() == target:
                    return getattr(rc, "id", None)
            return None
        except Exception as e:
            raise RuntimeError(f"SDK get_rate_card failed: {e}")

    async def get_or_create_prepaid_product(self) -> str:
        try:
            page = await self._sdk.v1.contracts.products.list()  # type: ignore[attr-defined]
            products = getattr(page, "data", []) or []
            for p in products:
                current = getattr(p, "current", None)
                name = getattr(current, "name", "") if current is not None else ""
                if name == "Vocalis Credits":
                    return getattr(p, "id", None)
        except Exception as e:
            logger.warning(f"SDK products.list failed (will try create): {e}")

        try:
            create_resp = await self._sdk.v1.contracts.products.create(  # type: ignore[attr-defined]
                name="Vocalis Credits",
                type="FIXED",
            )
            data = getattr(create_resp, "data", None) or create_resp
            return getattr(data, "id", None)
        except Exception as e:
            raise RuntimeError(f"SDK get_or_create_prepaid_product failed: {e}")

    async def list_products_readonly(self) -> List[Any]:
        """Read-only list of products via SDK. Returns the page data list.

        Used by health checks to verify presence without creating anything.
        """
        try:
            page = await self._sdk.v1.contracts.products.list()  # type: ignore[attr-defined]
            return getattr(page, "data", []) or []
        except Exception as e:
            raise RuntimeError(f"SDK list_products_readonly failed: {e}")

    # ---- Contracts ----
    async def create_billing_contract(self, customer_id: str, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rate_card_id = await self.get_rate_card(None)
            if not rate_card_id:
                raise RuntimeError(
                    f"Rate card not found by name '{settings.METRONOME_RATE_CARD_NAME}'. Configure METRONOME_RATE_CARD_NAME correctly in your environment."
                )
            product_id = await self.get_or_create_prepaid_product()

            credits_to_purchase = int(contract_data.get("credits", 0))
            start_date = contract_data.get("start_date") or "2025-07-01T00:00:00.000Z"
            end_date = contract_data.get("end_date") or "2026-07-01T00:00:00.000Z"

            payload = {
                "customer_id": customer_id,
                "rate_card_id": rate_card_id,
                "starting_at": start_date,
                "name": "Vocalis Credit Contract",
                "commits": [
                    {
                        "product_id": product_id,
                        "type": "prepaid",
                        "access_schedule": {
                            "credit_type_id": settings.VOCALIS_CREDIT_TYPE_ID,
                            "schedule_items": [
                                {
                                    "amount": credits_to_purchase,
                                    "starting_at": start_date,
                                    "ending_before": end_date,
                                }
                            ],
                        },
                    }
                ],
            }

            auto_recharge = contract_data.get("auto_recharge") or {}
            if auto_recharge.get("enabled"):
                threshold_credits = auto_recharge.get("threshold", 25000)
                recharge_credits = auto_recharge.get("amount", 200000)
                payload["prepaid_balance_threshold_configuration"] = {
                    "commit": {
                        "product_id": product_id,
                        "name": "Vocalis Credits Auto-Recharge",
                        "description": f"Auto-recharge {recharge_credits:,} VC",
                    },
                    "is_enabled": True,
                    "payment_gate_config": {"payment_gate_type": "EXTERNAL"},
                    "threshold_amount": threshold_credits,
                    "recharge_to_amount": recharge_credits,
                    "custom_credit_type_id": settings.VOCALIS_CREDIT_TYPE_ID,
                }

            # Build optional kwargs only when auto-recharge is enabled to avoid sending nulls
            kwargs: Dict[str, Any] = {}
            if payload.get("prepaid_balance_threshold_configuration"):
                kwargs["prepaid_balance_threshold_configuration"] = payload["prepaid_balance_threshold_configuration"]

            resp = await self._sdk.v1.contracts.create(  # type: ignore[attr-defined]
                customer_id=customer_id,
                starting_at=start_date,
                ending_before=end_date,
                name="Vocalis Credit Contract",
                rate_card_id=rate_card_id,
                commits=[
                    {
                        "product_id": product_id,
                        "type": "PREPAID",
                        "access_schedule": {
                            "credit_type_id": settings.VOCALIS_CREDIT_TYPE_ID,
                            "schedule_items": [
                                {
                                    "amount": credits_to_purchase,
                                    "starting_at": start_date,
                                    "ending_before": end_date,
                                }
                            ],
                        },
                    }
                ],
                **kwargs,
            )
            data = getattr(resp, "data", None) or resp
            contract_id = getattr(data, "id", None)
            if not contract_id:
                raise RuntimeError("SDK did not return a contract id")
            return {
                "id": contract_id,
                "customer_id": customer_id,
                "rate_card_id": rate_card_id,
                "product_id": product_id,
                "initial_amount_credits": credits_to_purchase,
                "auto_recharge_enabled": bool(auto_recharge.get("enabled")),
                "status": "created",
            }
        except Exception as e:
            raise RuntimeError(f"SDK create_billing_contract failed: {e}")

    # ---- Balances ----
    async def list_customer_balances(self, customer_id: str) -> Dict[str, Any]:
        try:
            payload = {
                "customer_id": customer_id,
                "include_balance": True,
                "include_contract_balances": True,
                "include_ledgers": False,
            }
            page = await self._sdk.v1.contracts.list_balances(**payload)  # type: ignore[attr-defined]
            # Normalize to dict
            return {"data": getattr(page, "data", [])}
        except Exception as e:
            raise RuntimeError(f"SDK list_customer_balances failed: {e}")

    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        try:
            payload = {
                "customer_id": customer_id,
                "include_balance": True,
                "include_ledgers": True,
                "include_contract_balances": True,
            }
            page = await self._sdk.v1.contracts.list_balances(**payload)  # type: ignore[attr-defined]
            data = getattr(page, "data", [])

            # Normalize to the same shape as the HTTP client
            total_vc = 0
            found_vc = False
            usd_cents = 0
            for entry in data or []:
                # SDK returns typed models (Commit or Credit). Use attribute access.
                ctid = None
                raw_balance = 0
                try:
                    sched = getattr(entry, "access_schedule", None)
                    ctype = getattr(sched, "credit_type", None) if sched is not None else None
                    ctid = getattr(ctype, "id", None)
                    raw_balance = getattr(entry, "balance", 0) or 0
                except Exception:
                    # Fallback for any dict-like responses
                    ctid = (entry or {}).get("access_schedule", {}).get("credit_type", {}).get("id")  # type: ignore[attr-defined]
                    raw_balance = (entry or {}).get("balance", 0) or 0  # type: ignore[attr-defined]

                if ctid == settings.VOCALIS_CREDIT_TYPE_ID:
                    found_vc = True
                    total_vc += int(raw_balance)
                elif ctid == "2714e483-4ff1-48e4-9e25-ac732e8f24f2":  # USD cents credit type
                    usd_cents += int(raw_balance)

            if found_vc:
                balance = total_vc
                currency = "VC"
                dollar_value = balance * 0.00025
            else:
                balance = int(usd_cents / 0.025) if usd_cents > 0 else 0
                currency = "USD"
                dollar_value = usd_cents / 100

            return {
                "customer_id": customer_id,
                "balance": balance,
                "currency": currency,
                "dollar_value": dollar_value,
                "last_updated": datetime.now().isoformat(),
                "source": "metronome_sdk",
                "credit_type_id": settings.VOCALIS_CREDIT_TYPE_ID if found_vc else "2714e483-4ff1-48e4-9e25-ac732e8f24f2",
                "debug_info": {
                    "found_vocalis_credits": found_vc,
                    "vocalis_balance": total_vc,
                    "usd_balance_cents": usd_cents,
                    "balance_entries_count": len(data or []),
                },
            }
        except Exception as e:
            raise RuntimeError(f"SDK get_customer_balance failed: {e}")

    # ---- Usage ----
    async def ingest_usage_event(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # SDK typically expects an array for ingest
            await self._sdk.v1.usage.ingest(usage=[event_payload])  # type: ignore[attr-defined]
            return {"success": True, "transaction_id": event_payload.get("transaction_id"), "event_type": event_payload.get("event_type")}
        except Exception as e:
            raise RuntimeError(f"SDK ingest_usage_event failed: {e}")

    async def record_usage_event(self, customer_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # If the SDK has a dedicated usage events API; otherwise fallback to ingest
            properties = event_data.get("properties", {})
            timestamp = event_data.get("timestamp") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            payload = {
                "customer_id": customer_id,
                "event_name": event_data.get("event_name") or event_data.get("event_type"),
                "timestamp": timestamp,
                "properties": properties,
            }
            # SDK doesn't expose a separate usage events resource; prefer ingest
            return await self.ingest_usage_event({
                "customer_id": customer_id,
                "event_type": event_data.get("event_name") or event_data.get("event_type"),
                "timestamp": timestamp,
                "transaction_id": event_data.get("transaction_id"),
                "properties": properties,
            })
        except Exception:
            # Fallback: attempt ingest
            return await self.ingest_usage_event({
                "customer_id": customer_id,
                "event_type": event_data.get("event_name") or event_data.get("event_type"),
                "timestamp": event_data.get("timestamp") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "transaction_id": event_data.get("transaction_id"),
                "properties": event_data.get("properties", {}),
            })

    # ---- Threshold Billing ----
    async def release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        """
        Temporary shim: call the threshold-billing release endpoint directly
        using the same bearer/base_url as the SDK client.
        """
        import httpx
        url = f"{settings.METRONOME_API_URL.rstrip('/')}/v1/contracts/commits/threshold-billing/release"
        headers = {
            "Authorization": f"Bearer {settings.METRONOME_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"workflow_id": workflow_id, "outcome": outcome}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code not in (200, 201, 202):
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
                data = resp.json() if resp.text.strip() else {"status": "success"}
                return {"success": True, "response": data}
        except Exception as e:
            raise RuntimeError(f"Threshold billing release failed: {e}")

    async def safe_release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        try:
            return await self.release_threshold_billing(workflow_id, outcome)
        except Exception as e:
            msg = str(e)
            if "not in COMMITTING state" in msg or "already in state COMMITTED" in msg:
                return {"success": True, "already_committed": True}
            raise
