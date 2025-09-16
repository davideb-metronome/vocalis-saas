"""
Health and Integration Self-Check Endpoints
Read-only probes to validate Metronome configuration
"""

from fastapi import APIRouter
from typing import Dict, Any
from app.core.config import settings
from app.services.metronome import metronome_client

router = APIRouter()


@router.get("/integrations")
async def integrations_health() -> Dict[str, Any]:
    """
    Read-only self-check for Metronome integration.
    - Validates API credentials reach Metronome
    - Resolves configured rate card by name
    - Verifies the prepaid product exists (no create)
    """
    checks: Dict[str, Any] = {
        "metronome": {
            "base_url": settings.METRONOME_API_URL,
            "rate_card_name": getattr(settings, "METRONOME_RATE_CARD_NAME", None),
        }
    }

    # Check 1: Credentials present
    creds_ok = bool(settings.METRONOME_API_KEY)
    checks["metronome"]["credentials_present"] = creds_ok

    # Early return if missing creds
    if not creds_ok:
        return {
            "status": "error",
            "summary": "Missing METRONOME_API_KEY",
            "checks": checks,
        }

    # Check 2: Reachability via a lightweight list call (rate cards)
    try:
        rate_cards_resp = await metronome_client._make_request(  # type: ignore
            "POST", "/v1/contract-pricing/rate-cards/list", {}
        )
        checks["metronome"]["reachability"] = {
            "ok": True,
            "count": len(rate_cards_resp.get("data", [])),
        }
    except Exception as e:
        checks["metronome"]["reachability"] = {"ok": False, "error": str(e)}
        return {
            "status": "error",
            "summary": "Unable to call Metronome API",
            "checks": checks,
        }

    # Check 3: Resolve configured rate card
    rate_card_id = None
    rc_name = getattr(settings, "METRONOME_RATE_CARD_NAME", None)
    try:
        if rc_name:
            rc_list = rate_cards_resp.get("data", [])
            target = rc_name.strip().lower()
            for rc in rc_list:
                if rc.get("name", "").strip().lower() == target:
                    rate_card_id = rc.get("id")
                    break
        checks["metronome"]["rate_card_resolved"] = {
            "ok": bool(rate_card_id),
            "id": rate_card_id,
            "name": rc_name,
        }
    except Exception as e:
        checks["metronome"]["rate_card_resolved"] = {"ok": False, "error": str(e)}

    # Check 4: Product presence (read-only list)
    product_id = None
    try:
        products_resp = await metronome_client._make_request(  # type: ignore
            "POST", "/v1/contract-pricing/products/list", {}
        )
        products = products_resp.get("data", [])
        for p in products:
            if p.get("name") == "Vocalis Credits":
                product_id = p.get("id")
                break
        checks["metronome"]["product_present"] = {
            "ok": bool(product_id),
            "id": product_id,
            "name": "Vocalis Credits",
        }
    except Exception as e:
        checks["metronome"]["product_present"] = {"ok": False, "error": str(e)}

    overall_ok = (
        checks["metronome"].get("reachability", {}).get("ok")
        and checks["metronome"].get("rate_card_resolved", {}).get("ok")
        and checks["metronome"].get("product_present", {}).get("ok")
    )

    return {
        "status": "ok" if overall_ok else "warn",
        "summary": "Metronome reachable; see checks for details" if overall_ok else "Some checks failed",
        "checks": checks,
    }

