"""
Usage API Routes
Voice generation and usage tracking with real Metronome ingest
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import logging

from app.services.metronome import metronome_client

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

class VoiceGenerationRequest(BaseModel):
    text: str
    voice_name: str
    voice_type: str
    character_count: int
    estimated_credits: int

class VoiceGenerationResponse(BaseModel):
    success: bool
    credits_consumed: int
    new_balance: Optional[int] = None
    voice_type: Optional[str] = None
    transaction_id: Optional[str] = None
    message: str

def build_voice_generation_event(request: VoiceGenerationRequest, customer_id: str) -> Dict[str, Any]:
    """
    Build voice generation event for Metronome ingest
    
    Args:
        request: Voice generation request data
        customer_id: Metronome customer ID
        
    Returns:
        Formatted event payload for Metronome
    """
    return {
        "customer_id": customer_id,
        "event_type": "voice_generation",
        "timestamp": datetime.now().isoformat() + "Z",
        "transaction_id": str(uuid.uuid4()),
        "properties": {
            "voice_type": request.voice_type,  # "standard" or "premium"
            "text_length": request.character_count
        }
    }

def build_voice_cloning_event(request: VoiceGenerationRequest, customer_id: str) -> Dict[str, Any]:
    """
    Build voice cloning event for Metronome ingest
    
    Args:
        request: Voice generation request data  
        customer_id: Metronome customer ID
        
    Returns:
        Formatted event payload for Metronome
    """
    return {
        "customer_id": customer_id,
        "event_type": "voice_cloning",
        "timestamp": datetime.now().isoformat() + "Z",
        "transaction_id": str(uuid.uuid4()),
        "properties": {
            "voice_id": 1  # Could be dynamic based on user preferences
        }
    }

def calculate_credits_needed(request: VoiceGenerationRequest) -> int:
    """
    Calculate credits needed based on voice type and content
    
    Args:
        request: Voice generation request data
        
    Returns:
        Number of credits needed
    """
    if request.voice_type == "standard":
        return request.character_count * 1  # 1 credit per character
    elif request.voice_type == "premium": 
        return request.character_count * 2  # 2 credits per character
    elif request.voice_type == "clone":
        return 25000  # One-time setup cost
    else:
        raise ValueError(f"Unknown voice type: {request.voice_type}")

@router.post("/generate-voice")
async def generate_voice(
    request: VoiceGenerationRequest,
    customer_id: str = Query(..., description="Customer ID from session")
) -> VoiceGenerationResponse:
    """
    Generate voice and record usage in Metronome via ingest
    ✅ ENHANCED: Now actually records usage and deducts credits
    """
    try:
        logger.info(f"Processing voice generation: {request.voice_type} for customer {customer_id}")
        print(f"🎵 VOICE GENERATION REQUEST:")
        print(f"   Customer: {customer_id}")
        print(f"   Voice Type: {request.voice_type}")
        print(f"   Text Length: {request.character_count} characters")
        print(f"   Estimated Credits: {request.estimated_credits}")
        
        # 1. Get current balance to validate sufficient credits
        balance_data = await metronome_client.get_customer_balance(customer_id)
        current_balance = balance_data.get("balance", 0)
        
        # 2. Calculate credits needed
        credits_needed = calculate_credits_needed(request)
        
        logger.info(f"Credits needed: {credits_needed}, Current balance: {current_balance}")
        print(f"💰 BALANCE CHECK:")
        print(f"   Current Balance: {current_balance} credits")
        print(f"   Credits Needed: {credits_needed} credits")
        print(f"   Sufficient Funds: {current_balance >= credits_needed}")
        
        # 3. Validate sufficient balance
        if current_balance < credits_needed:
            error_msg = f"Insufficient credits: need {credits_needed}, have {current_balance}"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # 4. Build appropriate event based on voice type
        if request.voice_type in ["standard", "premium"]:
            event_payload = build_voice_generation_event(request, customer_id)
            print(f"🎯 Built voice generation event")
        elif request.voice_type == "clone":
            event_payload = build_voice_cloning_event(request, customer_id)
            print(f"🎯 Built voice cloning event")
        else:
            error_msg = f"Invalid voice type: {request.voice_type}"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        print(f"📦 EVENT PAYLOAD:")
        print(f"   Event Type: {event_payload.get('event_type')}")
        print(f"   Transaction ID: {event_payload.get('transaction_id')}")
        print(f"   Properties: {event_payload.get('properties')}")
        
        # 5. Ingest usage event to Metronome
        print(f"📡 Sending usage event to Metronome...")
        ingest_result = await metronome_client.ingest_usage_event(event_payload)
        
        if not ingest_result.get('success'):
            error_msg = "Failed to record usage in Metronome"
            print(f"❌ {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        
        print(f"✅ Usage event recorded successfully in Metronome")
        
        # 6. Get updated balance after usage
        print(f"📊 Getting updated balance...")
        updated_balance_data = await metronome_client.get_customer_balance(customer_id)
        new_balance = updated_balance_data.get("balance", current_balance - credits_needed)
        
        print(f"💰 BALANCE UPDATE:")
        print(f"   Previous Balance: {current_balance} credits")
        print(f"   Credits Used: {credits_needed} credits")
        print(f"   New Balance: {new_balance} credits")
        
        logger.info(f"✅ Voice generation complete: {credits_needed} credits used, new balance: {new_balance}")
        
        # 7. Return success with actual usage data
        response = VoiceGenerationResponse(
            success=True,
            credits_consumed=credits_needed,
            new_balance=new_balance,
            voice_type=request.voice_type,
            transaction_id=event_payload.get('transaction_id'),
            message=f"{request.voice_type.title()} voice generated successfully"
        )
        
        print(f"🎉 VOICE GENERATION SUCCESS:")
        print(f"   Voice Type: {response.voice_type}")
        print(f"   Credits Consumed: {response.credits_consumed}")
        print(f"   New Balance: {response.new_balance}")
        print(f"   Transaction ID: {response.transaction_id}")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Voice generation failed: {e}")
        print(f"❌ VOICE GENERATION ERROR: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}"
        )