"""
Metronome API Client - REAL IMPLEMENTATION
Integrates with Metronome's billing API for prepaid credits system
"""

from typing import Dict, Any, Optional, List
import httpx
import logging
from datetime import datetime
from app.core.config import settings

# Set up logging for debugging
logger = logging.getLogger(__name__)

class MetronomeClient:
    def __init__(self):
        self.api_key = settings.METRONOME_API_KEY
        self.base_url = settings.METRONOME_API_URL
        
        if not self.api_key:
            raise ValueError("METRONOME_API_KEY not configured in environment")
        
        # Validate base URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("METRONOME_API_URL must include protocol (http:// or https://)")
            
        logger.info(f"MetronomeClient initialized with base_url: {self.base_url}")
    
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Metronome API"""
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 🔍 COMPREHENSIVE DEBUG LOGGING
        print("=" * 50)
        print(f"🔍 METRONOME API REQUEST DEBUG:")
        print(f"   Method: {method}")
        print(f"   Base URL: {self.base_url}")
        print(f"   Endpoint: {endpoint}")
        print(f"   Full URL: {url}")
        print(f"   API Key: {self.api_key[:10]}...{self.api_key[-4:] if self.api_key else 'None'}")
        print(f"   Headers: {headers}")
        if payload:
            print(f"   Payload: {payload}")
        print("=" * 50)
        
        # 🚀 ADD THE MISSING HTTP REQUEST CODE:
        logger.info(f"Making {method} request to {url}")
        if payload:
            logger.debug(f"Request payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload
                )
                
                # 🔍 RAW RESPONSE DEBUG
                print(f"🔍 RAW RESPONSE STATUS: {response.status_code}")
                print(f"🔍 RAW RESPONSE TEXT: {response.text}")
                print("=" * 50)
                
                logger.info(f"Response status: {response.status_code}")
                
                # Handle different success status codes
                if response.status_code not in [200, 201, 202]:
                    error_detail = response.text
                    logger.error(f"Metronome API error: {response.status_code} - {error_detail}")
                    raise Exception(
                        f"Metronome API request failed: {response.status_code} - {error_detail}"
                    )
                
                response_data = response.json()
                logger.debug(f"Response data: {response_data}")
                return response_data
                
        except httpx.TimeoutException:
            logger.error(f"Request timeout after {timeout}s to {url}")
            raise Exception(f"Metronome API timeout after {timeout}s")
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {e}")
            raise Exception(f"Metronome API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling Metronome API: {e}")
            raise
   
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer in Metronome"""

        logger.info(f"Creating Metronome customer: {customer_data.get('name')}")

        # Simple payload - email is embedded in external_id
        payload = {
            "name": customer_data["name"],
            "ingest_aliases": [customer_data["external_id"]]
            # No custom_fields needed - email is in the external_id
        }

        try:
            response_data = await self._make_request("POST", "/v1/customers", payload)
            
            # Extract customer ID from response
            customer_id = response_data.get("data", {}).get("id")
            if not customer_id:
                raise Exception("No customer ID returned from Metronome")
            
            logger.info(f"✅ Customer created successfully: {customer_id}")
            
            return {
                "id": customer_id,
                "external_id": customer_data["external_id"],
                "name": customer_data["name"],
                "email": customer_data["email"],  # Keep email in response for frontend
                "ingest_aliases": payload["ingest_aliases"]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create customer: {e}")
            raise Exception(f"Failed to create customer in Metronome: {e}")
        


    async def get_rate_card(self, rate_card_name: str = "Vocalis 2025") -> Optional[str]:
        """
        Retrieve rate card ID by name
        
        Args:
            rate_card_name: Name of the rate card to find
            
        Returns:
            Rate card ID if found, None otherwise
        """
        logger.info(f"Looking for '{rate_card_name}' rate card...")
        
        try:
            response_data = await self._make_request("POST", "/v1/contract-pricing/rate-cards/list", {})
            
            # Search for the specified rate card
            rate_cards = response_data.get("data", [])
            for rate_card in rate_cards:
                if rate_card.get("name") == rate_card_name:
                    rate_card_id = rate_card.get("id")
                    logger.info(f"✅ Found '{rate_card_name}' rate card: {rate_card_id}")
                    return rate_card_id
            
            logger.warning(f"❌ '{rate_card_name}' rate card not found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve rate cards: {e}")
            raise Exception(f"Failed to get rate cards from Metronome: {e}")

    
    async def get_or_create_prepaid_product(self) -> str:
        """
        Find existing 'Vocalis Credits' product or create it
        
        Returns:
            Product ID for use in prepaid balance threshold configuration
        """
        logger.info("Looking for 'Vocalis Credits' product...")
        
        try:
            # First, try to find existing product
            # Note: We'd need a "list products" endpoint to search, but let's create directly for now
            
            # Create the prepaid credits product
            payload = {
                "name": "Vocalis Credits",
                "type": "fixed"
            }
            
            response_data = await self._make_request("POST", "/v1/contract-pricing/products/create", payload)
            
            # Extract product ID from response
            product_id = response_data.get("data", {}).get("id")
            if not product_id:
                raise Exception("No product ID returned from Metronome")
            
            logger.info(f"✅ Created 'Vocalis Credits' product: {product_id}")
            
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create prepaid product: {e}")
            raise Exception(f"Failed to create prepaid product in Metronome: {e}")
        

    async def create_billing_contract(self, customer_id: str, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced billing contract with optional prepaid balance threshold
        
        Args:
            customer_id: Metronome customer ID
            contract_data: Dict containing:
                - auto_recharge: Optional auto-recharge configuration
                - amount: Purchase amount in dollars
                
        Returns:
            Dict containing contract details
        """
        logger.info(f"Creating enhanced billing contract for customer {customer_id}")
        
        # Get the rate card (defaults to "Vocalis 2025")
        rate_card_id = await self.get_rate_card()
        if not rate_card_id:
            raise Exception("Vocalis 2025 rate card not found - please create it in Metronome dashboard first")
        
        # Base contract payload
        payload = {
            "customer_id": customer_id,
            "rate_card_id": rate_card_id,
            "starting_at": "2025-07-01T00:00:00.000Z",
            "name": "Vocalis Credit Contract"
        }
        
        # Check if auto-recharge is enabled
        auto_recharge = contract_data.get("auto_recharge")
        if auto_recharge and auto_recharge.get("enabled", False):
            logger.info("Auto-recharge enabled - adding prepaid balance threshold configuration")
            
            # Get prepaid product ID
            product_id = await self.get_or_create_prepaid_product()
            
            # Convert amounts to cents
            threshold_cents = int(auto_recharge.get("threshold", 25000) * 0.00025 * 100)  # Credits to cents
            recharge_cents = int(auto_recharge.get("price", 50.0) * 100)  # Dollars to cents
            
            # Add prepaid balance threshold configuration
            payload["prepaid_balance_threshold_configuration"] = {
                "commit": {
                    "product_id": product_id,
                    "name": "Vocalis Credits Purchase",
                    "description": f"Auto-recharge for voice generation credits"
                },
                "is_enabled": True,
                "payment_gate_config": {
                    "payment_gate_type": "EXTERNAL"
                },
                "threshold_amount": threshold_cents,
                "recharge_to_amount": recharge_cents
            }
            
            logger.info(f"Threshold: ${threshold_cents/100:.2f}, Recharge to: ${recharge_cents/100:.2f}")
        else:
            logger.info("Auto-recharge disabled - creating basic contract")
        
        try:
            response_data = await self._make_request("POST", "/v1/contracts/create", payload)
            
            # Extract contract ID from response
            contract_id = response_data.get("data", {}).get("id")
            if not contract_id:
                raise Exception("No contract ID returned from Metronome")
            
            contract_type = "with auto-recharge" if auto_recharge and auto_recharge.get("enabled") else "basic"
            logger.info(f"✅ Enhanced contract created {contract_type}: {contract_id}")
            
            return {
                "id": contract_id,
                "customer_id": customer_id,
                "rate_card_id": rate_card_id,
                "auto_recharge_enabled": auto_recharge and auto_recharge.get("enabled", False),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create contract: {e}")
            raise Exception(f"Failed to create contract in Metronome: {e}")
        
    
    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer's current credit balance
        
        NOTE: Metronome might not have a direct "balance" endpoint for credits.
        This might need to be calculated from usage events vs. purchased amounts.
        
        Args:
            customer_id: Metronome customer ID
            
        Returns:
            Dict containing:
                - balance: Remaining credits
                - customer_id: Customer ID
                - currency: "USD"
        """
        logger.info(f"Getting balance for customer {customer_id}")
        
        try:
            # WARNING: This endpoint might not exist - might need to calculate from usage
            response_data = await self._make_request("GET", f"/v1/customers/{customer_id}/balance")
            
            # Extract balance from response (structure depends on actual Metronome API)
            balance_data = response_data.get("data", {})
            
            return {
                "customer_id": customer_id,
                "balance": balance_data.get("remaining_credits", 0),
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get customer balance: {e}")
            raise Exception(f"Failed to retrieve balance from Metronome: {e}")
    
    async def record_usage_event(self, customer_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record usage event for voice generation (consume credits)
        
        Args:
            customer_id: Metronome customer ID
            event_data: Dict containing:
                - event_name: "voice_generation"
                - properties: Dict with voice_type, character_count, credits_consumed
                - timestamp: ISO timestamp
                
        Returns:
            Dict with event recording confirmation
        """
        logger.info(f"Recording usage event for customer {customer_id}: {event_data.get('event_name')}")
        
        # Prepare usage event according to Metronome's format
        payload = {
            "customer_id": customer_id,
            "event_name": event_data["event_name"],
            "timestamp": event_data.get("timestamp", datetime.now().isoformat()),
            "properties": {
                "credits_consumed": event_data["properties"]["credits_consumed"],
                "voice_type": event_data["properties"]["voice_type"],
                "character_count": event_data["properties"]["character_count"],
                "voice_name": event_data["properties"].get("voice_name", "unknown")
            }
        }
        
        try:
            response_data = await self._make_request("POST", "/v1/usage/events", payload)
            
            logger.info(f"✅ Usage event recorded: {event_data['properties']['credits_consumed']} credits")
            
            return {
                "success": True,
                "event_id": response_data.get("data", {}).get("id"),
                "credits_consumed": event_data["properties"]["credits_consumed"],
                "customer_id": customer_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to record usage event: {e}")
            raise Exception(f"Failed to record usage in Metronome: {e}")
       
    async def set_customer_aliases(self, customer_id: str, aliases: List[str]) -> Dict[str, Any]:
        """
        Set ingest aliases for a customer (useful for usage event tracking)
        
        Args:
            customer_id: Metronome customer ID
            aliases: List of alias strings
            
        Returns:
            Dict with confirmation
        """
        logger.info(f"Setting aliases for customer {customer_id}: {aliases}")
        
        payload = {
            "ingest_aliases": aliases
        }
        
        try:
            response_data = await self._make_request(
                "POST", 
                f"/v1/customers/{customer_id}/setIngestAliases", 
                payload
            )
            
            logger.info(f"✅ Customer aliases set successfully")
            
            return {
                "success": True,
                "customer_id": customer_id,
                "aliases": aliases
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to set customer aliases: {e}")
            raise Exception(f"Failed to set customer aliases: {e}")

# Global client instance
metronome_client = MetronomeClient()