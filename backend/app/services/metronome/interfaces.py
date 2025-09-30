"""
Metronome client interface contract.
Defines the surface area used by the API layer so we can swap
between the existing HTTP client and the SDK-backed client.
"""

from __future__ import annotations

from typing import Protocol, Dict, Any, List, Optional


class IMetronomeClient(Protocol):
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def get_rate_card(self, rate_card_name: Optional[str] = None) -> Optional[str]:
        ...

    async def get_or_create_prepaid_product(self) -> str:
        ...

    async def create_billing_contract(self, customer_id: str, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        ...

    async def list_customer_balances(self, customer_id: str) -> Dict[str, Any]:
        ...

    async def ingest_usage_event(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def record_usage_event(self, customer_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        ...

    async def release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        ...

    async def safe_release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        ...

    async def set_customer_aliases(self, customer_id: str, aliases: List[str]) -> Dict[str, Any]:
        ...

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        ...

