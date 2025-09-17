"""
Authentication API Routes
User signup and authentication management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from app.services.metronome import metronome_client
from app.utils import user_store

router = APIRouter()

# Ensure local user store exists
user_store.init_db()

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    email: EmailStr
    password: str

class SignupResponse(BaseModel):
    success: bool
    customer_id: str
    message: str

@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """
    Create new user account and Metronome customer
    FAILS if Metronome integration is not working
    """
    try:
        # Prepare customer data for Metronome
        # Store email in our external_id/ingest_alias for later resolution in webhooks
        customer_data = {
            "name": request.full_name,
            "email": request.email,
            "external_id": f"vocalis_{request.email}",
        }
        
        # Create customer in Metronome - WILL FAIL until implemented
        metronome_customer = await metronome_client.create_customer(customer_data)
        
        # Extract customer ID from Metronome response
        customer_id = metronome_customer.get("id")
        if not customer_id:
            raise HTTPException(status_code=500, detail="Failed to create customer in Metronome")
        
        # Persist user profile locally for webhook personalization
        try:
            user_store.upsert_user(
                customer_id=customer_id,
                email=request.email,
                first_name=request.first_name,
                full_name=request.full_name,
            )
        except Exception:
            # Do not block signup on local store errors
            pass
        
        return SignupResponse(
            success=True,
            customer_id=customer_id,
            message="Account created successfully"
        )
        
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501, 
            detail=f"Metronome integration not implemented: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Account creation failed: {str(e)}"
        )
