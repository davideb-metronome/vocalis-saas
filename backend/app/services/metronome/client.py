"""
Metronome API Client - STUB IMPLEMENTATION
Real integration to be implemented later
"""

from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

class MetronomeClient:
    def __init__(self):
        self.api_key = settings.METRONOME_API_KEY
        self.base_url = settings.METRONOME_API_URL
        
        if not self.api_key:
            raise ValueError("METRONOME_API_KEY not configured")
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer in Metronome - STUB"""
        # TODO: Implement actual Metronome API call
        raise NotImplementedError("Metronome customer creation not yet implemented")
    
    async def create_billing_contract(self, customer_id: str, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create billing contract for prepaid credits - STUB"""
        # TODO: Implement actual Metronome API call
        raise NotImplementedError("Metronome billing contract creation not yet implemented")
    
    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        """Get customer credit balance - STUB"""
        # TODO: Implement actual Metronome API call
        raise NotImplementedError("Metronome balance retrieval not yet implemented")
    
    async def record_usage_event(self, customer_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record usage event for voice generation - STUB"""
        # TODO: Implement actual Metronome API call
        raise NotImplementedError("Metronome usage tracking not yet implemented")
    
    async def setup_auto_recharge(self, customer_id: str, recharge_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup auto-recharge configuration - STUB"""
        # TODO: Implement actual Metronome API call
        raise NotImplementedError("Metronome auto-recharge setup not yet implemented")

# Global client instance
metronome_client = MetronomeClient()
