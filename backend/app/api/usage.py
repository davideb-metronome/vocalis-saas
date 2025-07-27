"""
Usage API Routes
Voice generation and usage tracking
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from app.services.metronome import metronome_client

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
    message: str

@router.post("/generate-voice")
async def generate_voice(
    request: VoiceGenerationRequest,
    customer_id: str = Query(..., description="Customer ID from session")
) -> VoiceGenerationResponse:
    """
    Generate voice and record usage in Metronome
    FAILS if Metronome integration is not working
    """
    try:
        # First check if customer has sufficient balance
        balance_data = await metronome_client.get_customer_balance(customer_id)
        current_balance = balance_data.get("balance", 0)
        
        if current_balance < request.estimated_credits:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits: need {request.estimated_credits}, have {current_balance}"
            )
        
        # TODO: Implement actual voice generation service call
        # For now, simulate successful generation
        credits_consumed = request.estimated_credits
        
        # Record usage event in Metronome - WILL FAIL until implemented
        usage_event = {
            "customer_id": customer_id,
            "event_name": "voice_generation",
            "properties": {
                "voice_type": request.voice_type,
                "voice_name": request.voice_name,
                "character_count": request.character_count,
                "credits_consumed": credits_consumed
            },
            "timestamp": "2025-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
        
        await metronome_client.record_usage_event(customer_id, usage_event)
        
        return VoiceGenerationResponse(
            success=True,
            credits_consumed=credits_consumed,
            message="Voice generated successfully"
        )
        
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Metronome integration not implemented: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}"
        )
