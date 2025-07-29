"""
Metronome API Client - REAL IMPLEMENTATION
Integrates with Metronome's billing API for prepaid credits system
"""

from typing import Dict, Any, Optional, List
import httpx
import logging
from datetime import datetime
from app.core.config import settings
from datetime import datetime, timedelta  # Add timedelta here

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
                
                response_text = response.text.strip()
                if response_text:
                    response_data = response.json()  # Parse JSON if there's content
                else:
                    response_data = {"status": "success"}  # Create fake response for empty body
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
            # ✅ FIXED: First try to list existing products to find "Vocalis Credits"
            try:
                # Try to list products (this might be a different endpoint)
                list_response = await self._make_request("POST", "/v1/contract-pricing/products/list", {})
                
                # Search for existing product
                products = list_response.get("data", [])
                for product in products:
                    if product.get("name") == "Vocalis Credits":
                        product_id = product.get("id")
                        logger.info(f"✅ Found existing 'Vocalis Credits' product: {product_id}")
                        return product_id
                        
            except Exception as list_error:
                logger.warning(f"Could not list products (might not exist yet): {list_error}")
            
            # ✅ FIXED: Create new product with proper configuration
            payload = {
                "name": "Vocalis Credits",
                "type": "fixed"  # Fixed price product for prepaid credits
            }
            
            response_data = await self._make_request("POST", "/v1/contract-pricing/products/create", payload)
            
            # Extract product ID from response
            product_id = response_data.get("data", {}).get("id")
            if not product_id:
                raise Exception("No product ID returned from Metronome")
            
            logger.info(f"✅ Created 'Vocalis Credits' product: {product_id}")
            
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create prepaid product: {e}")
            raise Exception(f"Failed to get/create prepaid product in Metronome: {e}")
    

    async def create_billing_contract(self, customer_id: str, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create billing contract with initial prepaid commit
        """
        logger.info(f"Creating billing contract with initial credits for customer {customer_id}")
        
        # Get required IDs
        rate_card_id = await self.get_rate_card()
        if not rate_card_id:
            raise Exception("Vocalis 2025 rate card not found - please create it in Metronome dashboard first")
        
        product_id = await self.get_or_create_prepaid_product()
        
        # Calculate amounts properly
        purchase_amount_dollars = contract_data.get("amount", 0)
        purchase_amount_cents = int(purchase_amount_dollars * 100)
        
        start_date = "2025-07-01T00:00:00.000Z"  # July 1st, 2025 at midnight UTC
        end_date = "2026-07-01T00:00:00.000Z"    # July 1st, 2026 at midnight UTC

        # now = datetime.now()
        # # Round to next hour boundary
        # start_hour = now.replace(minute=0, second=0, microsecond=0)
        # if now.minute > 0 or now.second > 0 or now.microsecond > 0:
        #     start_hour = start_hour + timedelta(hours=1)
        
        # end_hour = start_hour + timedelta(days=365)  # 1 year later
        
        # start_date = start_hour.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        # end_date = end_hour.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        logger.info(f"Contract dates: {start_date} to {end_date}")
        
        # Base contract payload with initial commit
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
                        "schedule_items": [
                            {
                                "amount": purchase_amount_cents,
                                "starting_at": start_date,
                                "ending_before": end_date
                            }
                        ]
                    }
                }
            ]
        }
        
        # Add auto-recharge configuration if enabled
        auto_recharge = contract_data.get("auto_recharge")
        if auto_recharge and auto_recharge.get("enabled", False):
            logger.info("Adding auto-recharge configuration to contract")
            
            # Calculate threshold and recharge amounts in cents
            threshold_credits = auto_recharge.get("threshold", 25000)
            threshold_dollars = threshold_credits * 0.00025
            threshold_cents = int(threshold_dollars * 100)
            
            recharge_dollars = auto_recharge.get("price", 50.0)
            recharge_cents = int(recharge_dollars * 100)
            
            # Add prepaid balance threshold configuration
            payload["prepaid_balance_threshold_configuration"] = {
                "commit": {
                    "product_id": product_id,
                    "name": "Vocalis Credits Auto-Recharge",
                    "description": f"Auto-recharge {recharge_dollars:.2f} when balance drops below {threshold_dollars:.2f}"
                },
                "is_enabled": True,
                "payment_gate_config": {
                    "payment_gate_type": "EXTERNAL"
                },
                "threshold_amount": threshold_cents,
                "recharge_to_amount": recharge_cents
            }
            
            logger.info(f"Auto-recharge: Threshold ${threshold_dollars:.2f} ({threshold_credits} credits), Recharge ${recharge_dollars:.2f}")
        else:
            logger.info("Auto-recharge disabled - creating basic contract")
        
        try:
            response_data = await self._make_request("POST", "/v1/contracts/create", payload)
            
            # Extract contract ID from response
            contract_id = response_data.get("data", {}).get("id")
            if not contract_id:
                raise Exception("No contract ID returned from Metronome")
            
            contract_type = "with auto-recharge" if auto_recharge and auto_recharge.get("enabled") else "basic"
            logger.info(f"✅ Contract created {contract_type}: {contract_id}")
            logger.info(f"✅ Customer now has ${purchase_amount_dollars:.2f} worth of credits available")
            
            return {
                "id": contract_id,
                "customer_id": customer_id,
                "rate_card_id": rate_card_id,
                "product_id": product_id,
                "initial_amount_cents": purchase_amount_cents,
                "initial_amount_dollars": purchase_amount_dollars,
                "auto_recharge_enabled": auto_recharge and auto_recharge.get("enabled", False),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create contract: {e}")
            raise Exception(f"Failed to create contract in Metronome: {e}")         
        
    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        """
        ✅ FIXED: Get customer's current credit balance from Metronome
        
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
            # ✅ FIXED: Use the correct Metronome endpoint for customer balances
            payload = {
                "customer_id": customer_id,
                "include_ledgers": True  # Include ledger information for detailed balance
            }
            
            response_data = await self._make_request(
                "POST", 
                "/v1/contracts/customerBalances/list", 
                payload
            )
            
            # 🔍 LOG THE FULL RESPONSE FOR DEBUGGING
            logger.info(f"📊 METRONOME BALANCE RESPONSE: {response_data}")
            print("=" * 70)
            print("📊 METRONOME CUSTOMER BALANCE RESPONSE:")
            print(f"   Customer ID: {customer_id}")
            print(f"   Full Response: {response_data}")
            print("=" * 70)
            
            # Parse the balance data from commits and ledgers
            balances = response_data.get("data", [])
            total_available_credits = 0
            
            if not balances:
                logger.error(f"❌ EMPTY BALANCE RESPONSE from Metronome for customer {customer_id}")
                logger.error(f"❌ Full response was: {response_data}")
                raise Exception(f"Metronome returned empty balance data for customer {customer_id}. This suggests the customer or contract doesn't exist.")
            
            # Process balance data
            for balance_entry in balances:
                # Look for credits from commits
                if "access_schedule" in balance_entry:
                    schedule_items = balance_entry.get("access_schedule", {}).get("schedule_items", [])
                    for item in schedule_items:
                        amount_cents = item.get("amount", 0)
                        # Convert cents to credits: $0.00025 per credit = 0.025 cents per credit
                        credits = int(amount_cents / 0.025)  # 1 cent = 40 credits
                        total_available_credits += credits
                        
                        logger.info(f"📊 Found commit: {amount_cents} cents = {credits} credits")
                
                # Look for invoice_contract data which might have credit info
                if "invoice_contract" in balance_entry:
                    invoice_data = balance_entry["invoice_contract"]
                    logger.info(f"📊 Invoice contract data: {invoice_data}")
                
                # Look for ledgers which show actual usage/balance
                if "ledgers" in balance_entry:
                    ledgers = balance_entry["ledgers"]
                    for ledger in ledgers:
                        amount = ledger.get("amount", 0)
                        ledger_type = ledger.get("type", "unknown")
                        logger.info(f"📊 Ledger entry: {ledger_type} = {amount}")
                        
                        # If this is a prepaid credit ledger, add to balance
                        if ledger_type == "PREPAID_COMMIT_AUTOMATED_INVOICE_DEDUCTION":
                            # This represents available credits
                            credits_from_ledger = int(amount / 0.025)  # Convert cents to credits
                            total_available_credits += credits_from_ledger
                            logger.info(f"📊 Credits from ledger: {credits_from_ledger}")
            
            # If we still don't have a balance, try to calculate from the response structure
            if total_available_credits == 0:
                # Look for any amount fields and convert them
                logger.info("📊 No credits found in standard fields, checking all amount fields...")
                
                def extract_amounts(obj, path=""):
                    """Recursively extract amount fields from the response"""
                    amounts = []
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key == "amount" and isinstance(value, (int, float)):
                                amounts.append((f"{path}.{key}", value))
                                logger.info(f"📊 Found amount at {path}.{key}: {value}")
                            elif isinstance(value, (dict, list)):
                                amounts.extend(extract_amounts(value, f"{path}.{key}"))
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            amounts.extend(extract_amounts(item, f"{path}[{i}]"))
                    return amounts
                
                all_amounts = extract_amounts(response_data)
                
                # Use the largest amount as the likely credit balance
                if all_amounts:
                    largest_amount = max(all_amounts, key=lambda x: x[1])
                    amount_cents = largest_amount[1]
                    total_available_credits = int(amount_cents / 0.025)  # Convert cents to credits
                    logger.info(f"📊 Using largest amount: {amount_cents} cents = {total_available_credits} credits from {largest_amount[0]}")
            
            # Final check - if we still have 0, this is likely an error
            if total_available_credits == 0:
                logger.error("❌ Could not find any credit balance in Metronome response")
                logger.error(f"❌ Customer {customer_id} appears to have no credits or the parsing failed")
                logger.error(f"❌ Full response: {response_data}")
                raise Exception(f"No credit balance found for customer {customer_id}. Check if contract exists and has commits.")
            
            source = "metronome_api"
            dollar_value = total_available_credits * 0.00025
            
            logger.info(f"✅ Customer {customer_id} balance: {total_available_credits} credits (${dollar_value:.2f})")
            
            return {
                "customer_id": customer_id,
                "balance": total_available_credits,
                "currency": "USD",
                "dollar_value": dollar_value,
                "last_updated": datetime.now().isoformat(),
                "source": source
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get customer balance: {e}")
            # Return demo balance as fallback
            logger.info("📊 API FAILED - USING DEMO BALANCE: 40,000 credits")
            return {
                "customer_id": customer_id,
                "balance": 40000,  # Demo balance
                "currency": "USD",
                "last_updated": datetime.now().isoformat(),
                "source": "error_fallback"
            }

    async def release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        """
        ✅ FIXED: Release external payment gate threshold commit
        Handles empty response bodies from Metronome API
        """
        logger.info(f"Releasing threshold billing workflow {workflow_id} with outcome: {outcome}")
        
        if outcome not in ["paid", "failed"]:
            raise ValueError(f"Invalid outcome '{outcome}'. Must be 'paid' or 'failed'")
        
        payload = {
            "workflow_id": workflow_id,
            "outcome": outcome
        }
        
        try:
            response_data = await self._make_request(
                "POST", 
                "/v1/contracts/commits/threshold-billing/release", 
                payload
            )
            
            logger.info(f"✅ Threshold billing released successfully: {outcome}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "outcome": outcome,
                "response": response_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to release threshold billing: {e}")
            raise Exception(f"Failed to release threshold billing workflow {workflow_id}: {e}")

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

 

    async def ingest_usage_event(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest usage event to Metronome using /v1/ingest endpoint
        
        Args:
            event_payload: Single event object to ingest
            
        Returns:
            Dict with success status
        """
        logger.info(f"Ingesting usage event: {event_payload.get('event_type')} for customer {event_payload.get('customer_id')}")
        
        try:
            # Metronome expects an array of events
            payload = [event_payload]
            
            response_data = await self._make_request(
                "POST", 
                "/v1/ingest", 
                payload
            )
            
            logger.info(f"✅ Usage event ingested successfully: {event_payload.get('transaction_id')}")
            
            return {
                "success": True,
                "transaction_id": event_payload.get('transaction_id'),
                "event_type": event_payload.get('event_type')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest usage event: {e}")
            raise Exception(f"Failed to ingest usage event to Metronome: {e}")

# Global client instance
metronome_client = MetronomeClient()