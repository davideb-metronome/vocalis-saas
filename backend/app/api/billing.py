"""
Billing API Routes
Credit purchases and auto-recharge management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.metronome import metronome_client

router = APIRouter()

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
            "amount": request.amount,
            "auto_recharge": request.auto_recharge.dict() if request.auto_recharge else None
        }
        
        # Create billing contract in Metronome 
        contract_data = {
            "auto_recharge": request.auto_recharge.dict() if request.auto_recharge else None,
            "amount": request.amount
        }
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

@router.get("/credits/balance/{customer_id}")
async def get_credit_balance(customer_id: str):
    """
    Get current credit balance from Metronome
    FAILS if Metronome integration is not working
    """
    try:
        balance_data = await metronome_client.get_customer_balance(customer_id)
        return balance_data
        
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Metronome integration not implemented: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve balance: {str(e)}"
        )
