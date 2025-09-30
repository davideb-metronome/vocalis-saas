"""
Billing API Routes
Credit purchases, auto-recharge, and plan selection
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.services.metronome import metronome_client
from app.core.config import settings

router = APIRouter()

# Local logger for this module
logger = logging.getLogger(__name__)

class AutoRechargeConfig(BaseModel):
    enabled: bool
    threshold: int
    amount: int
    price: float

class CreditPurchaseRequest(BaseModel):
    billing_type: str
    credits: int
    amount: float
    auto_recharge: Optional[AutoRechargeConfig] = None

class CreditPurchaseResponse(BaseModel):
    success: bool
    contract_id: str
    message: str

@router.post("/credits/purchase")
async def purchase_credits(
    request: CreditPurchaseRequest,
    customer_id: str = Query(..., description="Customer ID from session")
) -> CreditPurchaseResponse:
    """
    Purchase credits and setup billing contract
    FAILS if Metronome integration is not working
    """
    try:
        # Prepare contract data for Metronome
        contract_data = {
            "customer_id": customer_id,
            "billing_type": "prepaid_credits",
            "credits": request.credits,
            # "amount": request.amount,
            "auto_recharge": request.auto_recharge.dict() if request.auto_recharge else None
        }
        
        credits_to_purchase = contract_data.get("credits", 0)  # Get credits directly!
        print(f"CREDITS TO PURCHASE RETRIEVED FROM FRONTEND: {credits_to_purchase}")

        # Create billing contract in Metronome 
        # contract_data = {
        #     "auto_recharge": request.auto_recharge.dict() if request.auto_recharge else None,
        #     # "amount": request.amount
        #     credits:request.credits
        # }
       
        contract = await metronome_client.create_billing_contract(customer_id, contract_data)

        
        contract_id = contract.get("id")
        if not contract_id:
            raise HTTPException(status_code=500, detail="Failed to create billing contract")
        
        return CreditPurchaseResponse(
            success=True,
            contract_id=contract_id,
            message="Credits purchased successfully"
        )
        
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Metronome integration not implemented: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Credit purchase failed: {str(e)}"
        )

from datetime import datetime

# ----------------------
# Plans API (catalog + selection)
# ----------------------

CREDITS_PER_DOLLAR = 4000

class PlanCatalogItem(BaseModel):
    id: str
    name: str
    price_usd: Optional[int] = None
    monthly_credits: Optional[int] = None
    trial_days: Optional[int] = None

class PlanSelectRequest(BaseModel):
    plan: str  # 'trial' | 'creator' | 'pro' | 'enterprise'

class PlanSelectResponse(BaseModel):
    success: bool
    plan: str
    contract_id: Optional[str] = None
    message: str


@router.get("/plans")
async def get_plans() -> Dict[str, Any]:
    """Return available plans and derived monthly credits."""
    # Fixed round numbers for the demo UI
    creator_credits = 250_000
    pro_credits = 1_000_000

    plans = [
        PlanCatalogItem(
            id="trial",
            name="Free Trial",
            price_usd=0,
            monthly_credits=settings.METRONOME_TRIAL_CREDITS,
            trial_days=settings.METRONOME_TRIAL_DAYS,
        ),
        PlanCatalogItem(
            id="creator",
            name="Creator",
            price_usd=settings.METRONOME_PLAN_CREATOR_DOLLARS,
            monthly_credits=creator_credits,
        ),
        PlanCatalogItem(
            id="pro",
            name="Pro",
            price_usd=settings.METRONOME_PLAN_PRO_DOLLARS,
            monthly_credits=pro_credits,
        ),
        PlanCatalogItem(id="enterprise", name="Enterprise"),
    ]

    return {
        "plans": [p.model_dump() for p in plans],
        "credits_per_dollar": CREDITS_PER_DOLLAR,
        "credit_type_id": settings.VOCALIS_CREDIT_TYPE_ID,
        "rate_card_name": settings.METRONOME_RATE_CARD_NAME,
    }


@router.post("/plan/select")
async def select_plan(
    request: PlanSelectRequest,
    customer_id: str = Query(..., description="Metronome customer ID from session")
) -> PlanSelectResponse:
    """
    Select a billing plan and create the corresponding Metronome contract.
    - trial: one-time 10k credits (default) valid for N days
    - creator/pro: initial allocation + threshold auto-recharge to monthly credits
    - enterprise: placeholder (no contract creation)
    """
    plan = request.plan.lower().strip()
    logger.info(f"Plan selection requested: {plan} for customer {customer_id}")

    try:
        if plan == "trial":
            # Trial window: start at current hour boundary, end at boundary N days later (UTC)
            from datetime import datetime, timedelta, timezone

            def floor_to_hour(dt: datetime) -> datetime:
                return dt.replace(minute=0, second=0, microsecond=0)

            now = datetime.now(timezone.utc)
            # Start at previous hour boundary to absorb clock skew/latency
            start_dt = floor_to_hour(now) - timedelta(hours=1)
            end_dt = start_dt + timedelta(days=settings.METRONOME_TRIAL_DAYS)
            start_iso = start_dt.isoformat().replace("+00:00", "Z")
            end_iso = end_dt.isoformat().replace("+00:00", "Z")

            contract = await metronome_client.create_billing_contract(
                customer_id,
                {
                    "credits": settings.METRONOME_TRIAL_CREDITS,
                    "start_date": start_iso,
                    "end_date": end_iso,
                    "auto_recharge": None,
                },
            )
            return PlanSelectResponse(
                success=True,
                plan=plan,
                contract_id=contract.get("id"),
                message=f"Trial started: {settings.METRONOME_TRIAL_CREDITS:,} credits for {settings.METRONOME_TRIAL_DAYS} days",
            )

        elif plan in ("creator", "pro"):
            # Grant fixed plan credits immediately (no thresholds/recurrence for demo)
            monthly_credits = 250_000 if plan == "creator" else 1_000_000

            from datetime import datetime, timedelta, timezone

            def floor_to_hour(dt: datetime) -> datetime:
                return dt.replace(minute=0, second=0, microsecond=0)

            now = datetime.now(timezone.utc)
            start_dt = floor_to_hour(now)
            end_dt = start_dt + timedelta(days=365)
            start_iso = start_dt.isoformat().replace("+00:00", "Z")
            end_iso = end_dt.isoformat().replace("+00:00", "Z")

            contract = await metronome_client.create_billing_contract(
                customer_id,
                {
                    "credits": monthly_credits,
                    "start_date": start_iso,
                    "end_date": end_iso,
                    "auto_recharge": None,
                },
            )
            return PlanSelectResponse(
                success=True,
                plan=plan,
                contract_id=contract.get("id"),
                message=f"{plan.title()} plan activated: {monthly_credits:,} credits/month",
            )

        elif plan == "enterprise":
            return PlanSelectResponse(
                success=True,
                plan=plan,
                message="Enterprise plan: our team will reach out to tailor your contract.",
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")

    except Exception as e:
        logger.error(f"Plan selection failed for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Plan selection failed: {str(e)}")



# Update this in backend/app/api/billing.py

@router.get("/credits/balance/{customer_id}")
async def get_credit_balance(customer_id: str):
    """
    Get current credit balance from Metronome - NO FALLBACKS
    """
    try:
        print("=" * 70)
        print(f"🔍 BALANCE REQUEST:")
        print(f"   Customer ID: {customer_id}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Call Metronome API - let it fail if it fails
        balance_data = await metronome_client.get_customer_balance(customer_id)
        
        print("=" * 70)
        print(f"✅ BALANCE SUCCESS:")
        print(f"   Balance: {balance_data.get('balance', 0)} credits")
        print(f"   Dollar Value: ${balance_data.get('dollar_value', 0):.2f}")
        print(f"   Source: {balance_data.get('source', 'unknown')}")
        print("=" * 70)
        
        return balance_data
        
    except Exception as e:
        print("=" * 70)
        print(f"❌ BALANCE API ERROR:")
        print(f"   Customer ID: {customer_id}")
        print(f"   Error: {str(e)}")
        print("=" * 70)
        
        logger.error(f"Failed to get customer balance for {customer_id}: {e}")
        
        # Return the actual error to help debug - NO FALLBACKS
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve balance from Metronome: {str(e)}"
        )
# Trial status endpoint: compute days_left from balances
@router.get("/trial-status")
async def trial_status(customer_id: str = Query(...)) -> Dict[str, Any]:
    try:
        from datetime import datetime, timezone
        balances = await metronome_client.list_customer_balances(customer_id)  # type: ignore
        items = balances.get('data', [])
        end_dt = None
        for entry in items:
            etype = getattr(entry, 'type', None)
            if etype == 'PREPAID':
                sched = getattr(entry, 'access_schedule', None)
                schedule_items = getattr(sched, 'schedule_items', []) if sched is not None else []
                if schedule_items:
                    end_dt = getattr(schedule_items[0], 'ending_before', None)
                    break
        if not end_dt:
            return {"is_trial": False}
        # Parse and compute days left (ceil)
        now = datetime.now(timezone.utc)
        # end_dt may be naive; assume UTC if so
        if end_dt.tzinfo is None:
            from datetime import timezone as _tz
            end_dt = end_dt.replace(tzinfo=_tz.utc)
        seconds_left = max(0, (end_dt - now).total_seconds())
        days_left = int((seconds_left + 86399) // 86400)  # ceil
        return {
            "is_trial": True,
            "end_at_utc": end_dt.strftime('%b %d, %Y %H:%M UTC'),
            "days_left": days_left,
        }
    except Exception as e:
        logger.error(f"trial-status failed: {e}")
        return {"is_trial": False}
