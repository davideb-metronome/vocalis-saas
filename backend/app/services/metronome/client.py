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
import json

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
        # purchase_amount_dollars = contract_data.get("amount", 0)
        # purchase_amount_cents = int(purchase_amount_dollars * 100)

        credits_to_purchase = contract_data.get("credits", 0)  # Get credits directly!
        logger.info(f"CREDITS TO PURCHASE IN CLIENT PY FILE. PAYLOAD FOR CREATE CONTRACT {credits_to_purchase}")
        
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
                        "credit_type_id": "b45eb30b-547f-4e11-91c0-400c0be3370a",
                        "schedule_items": [
                            {
                                # "amount": purchase_amount_cents,
                                "amount": credits_to_purchase, 
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
            
            # # Calculate threshold and recharge amounts in cents
            # threshold_credits = auto_recharge.get("threshold", 25000)
            # threshold_dollars = threshold_credits * 0.00025
            # threshold_cents = int(threshold_dollars * 100)
            
            # recharge_dollars = auto_recharge.get("price", 50.0)
            # recharge_cents = int(recharge_dollars * 100)

            # Calculate threshold and recharge amounts in credits
            threshold_credits = auto_recharge.get("threshold", 25000)
            recharge_credits = auto_recharge.get("amount", 200000)
            
            # Add prepaid balance threshold configuration
            payload["prepaid_balance_threshold_configuration"] = {
                "commit": {
                    "product_id": product_id,
                    "name": "Vocalis Credits Auto-Recharge",
                    "description": f"Auto-recharge {recharge_credits:,} VC"
                    # "description": f"Auto-recharge {recharge_dollars:.2f} when balance drops below {threshold_dollars:.2f}"
                },
                "is_enabled": True,
                "payment_gate_config": {
                    "payment_gate_type": "EXTERNAL"
                },
                # "threshold_amount": threshold_cents,
                # "recharge_to_amount": recharge_cents
                 "threshold_amount": threshold_credits,
                "recharge_to_amount": recharge_credits,
                "custom_credit_type_id": "b45eb30b-547f-4e11-91c0-400c0be3370a"
            }
            
            logger.info(f"Auto-recharge: Threshold ${threshold_credits:.2f} ({threshold_credits} credits), Recharge ${recharge_credits:.2f}")
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
            # logger.info(f"✅ Customer now has ${purchase_amount_dollars:.2f} worth of credits available")
            logger.info(f"✅ Customer now has ${credits_to_purchase:.2f} worth of credits available")
            
            
            return {
                "id": contract_id,
                "customer_id": customer_id,
                "rate_card_id": rate_card_id,
                "product_id": product_id,
                # "initial_amount_cents": purchase_amount_cents,
                # "initial_amount_dollars": purchase_amount_dollars,
                "initial_amount_credits": credits_to_purchase, 
                "auto_recharge_enabled": auto_recharge and auto_recharge.get("enabled", False),
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create contract: {e}")
            raise Exception(f"Failed to create contract in Metronome: {e}")   
              
        
    # async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
    #     """
    #     Get customer's current credit balance from Metronome
    #     SIMPLIFIED VERSION - Trust the balance field from API
        
    #     Args:
    #         customer_id: Metronome customer ID
            
    #     Returns:
    #         Dict containing balance info
            
    #     Raises:
    #         Exception: If API fails or balance cannot be determined
    #     """
    #     logger.info(f"Getting balance for customer {customer_id}")
        
    #     payload = {
    #         "customer_id": customer_id,
    #         "include_balance": True,          # CRITICAL: Gets the calculated balance
    #         "include_ledgers": False,         # We don't need ledgers for balance calculation
    #         "include_contract_balances": True # Include contract-specific balances if needed
    #     }
        
    #     response_data = await self._make_request(
    #         "POST", 
    #         "/v1/contracts/customerBalances/list", 
    #         payload
    #     )
        
    #     # Log the response for debugging
    #     logger.info(f"📊 METRONOME BALANCE RESPONSE: {response_data}")
    #     print("=" * 70)
    #     print("📊 METRONOME CUSTOMER BALANCE RESPONSE:")
    #     print(f"   Customer ID: {customer_id}")
    #     print(f"   Full Response: {response_data}")
    #     print("=" * 70)
        
    #     # Get the balance entries
    #     balances = response_data.get("data", [])
        
    #     if not balances:
    #         raise Exception(f"No balance data found for customer {customer_id}. Customer or contract may not exist.")
        
    #     # Sum all balance fields - Metronome already calculated these
    #     total_balance_cents = 0
    #     for balance_entry in balances:
    #         balance_cents = balance_entry.get("balance", 0)
    #         entry_type = balance_entry.get("type", "unknown")
    #         product_name = balance_entry.get("product", {}).get("name", "unknown")
            
    #         total_balance_cents += balance_cents
    #         logger.info(f"📊 Found {entry_type} balance: {balance_cents} cents from {product_name}")
        
    #     # Convert cents to credits: $0.00025 per credit = 0.025 cents per credit
    #     total_available_credits = int(total_balance_cents / 0.025)
    #     dollar_value = total_balance_cents / 100  # Convert cents to dollars
        
    #     logger.info(f"✅ Customer {customer_id} balance: {total_available_credits} credits (${dollar_value:.2f})")
        
    #     return {
    #         "customer_id": customer_id,
    #         "balance": total_available_credits,
    #         "balance_cents": total_balance_cents,
    #         "currency": "USD",
    #         "dollar_value": dollar_value,
    #         "last_updated": datetime.now().isoformat(),
    #         "source": "metronome_api"
    #     }
 
    async def get_customer_balance(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer's current credit balance from Metronome
        UPDATED: Now handles custom pricing units (Vocalis Credits)

        Args:
            customer_id: Metronome customer ID
            
        Returns:
            Dict containing balance info
        """
        # Add your custom credit type ID (replace with actual ID from Metronome)
        VOCALIS_CREDIT_TYPE_ID = "b45eb30b-547f-4e11-91c0-400c0be3370a"  

        logger.info(f"Getting balance for customer {customer_id}")

        payload = {
            "customer_id": customer_id,
            "include_balance": True,
            "include_ledgers": True,  # Include ledgers for debugging
            "include_contract_balances": True
        }

        response_data = await self._make_request(
            "POST", 
            "/v1/contracts/customerBalances/list", 
            payload
        )

        # Log the full response for debugging
        logger.info(f"📊 METRONOME BALANCE RESPONSE: {response_data}")
        print("=" * 70)
        print("📊 METRONOME CUSTOMER BALANCE RESPONSE:")
        print(f"   Customer ID: {customer_id}")
        print(f"   Full Response: {json.dumps(response_data, indent=2)}")
        print("=" * 70)

        # Get the balance entries
        balances = response_data.get("data", [])

        if not balances:
            raise Exception(f"No balance data found for customer {customer_id}")

        # Look for Vocalis Credits balance
        vocalis_balance = 0
        usd_balance_for_reference = 0
        found_vocalis_credits = False

        # for balance_entry in balances:
        #     credit_type = balance_entry.get("credit_type", {})
        #     credit_type_id = credit_type.get("id")
        #     credit_type_name = credit_type.get("name", "unknown")
        #     raw_balance = balance_entry.get("balance", 0)
        
        for balance_entry in balances:
            # Credit type is inside access_schedule
            access_schedule = balance_entry.get("access_schedule", {})
            credit_type = access_schedule.get("credit_type", {})
            credit_type_id = credit_type.get("id")
            credit_type_name = credit_type.get("name", "unknown")
            raw_balance = balance_entry.get("balance", 0)

            # Detailed logging for debugging
            logger.info(f"📊 Balance Entry Debug:")
            logger.info(f"   Credit Type: {credit_type_name}")
            logger.info(f"   Credit Type ID: {credit_type_id}")
            logger.info(f"   Raw Balance Value: {raw_balance}")
            
            print(f"📊 BALANCE ENTRY:")
            print(f"   Type: {credit_type_name} ({credit_type_id})")
            print(f"   Balance: {raw_balance}")
            print(f"   Entry Type: {balance_entry.get('type', 'unknown')}")
            
            # Check ledger entries for more clues
            ledger = balance_entry.get("ledger", [])
            if ledger:
                print(f"   Ledger entries: {len(ledger)}")
                for entry in ledger[:2]:  # Show first 2 entries
                    print(f"     - {entry.get('type')}: {entry.get('amount')}")
            
            # Handle different credit types
            if credit_type_id == VOCALIS_CREDIT_TYPE_ID:
                found_vocalis_credits = True
                vocalis_balance += raw_balance
                logger.info(f"✅ Found Vocalis Credits: {raw_balance} VC")
                
            elif credit_type_id == "2714e483-4ff1-48e4-9e25-ac732e8f24f2":  # USD cents
                usd_balance_for_reference += raw_balance
                logger.info(f"📊 Found USD balance: {raw_balance} cents")

        # Determine final balance and handle edge cases
        if found_vocalis_credits:
            # Using Vocalis Credits
            total_balance = vocalis_balance
            currency = "VC"
            dollar_value = vocalis_balance * 0.00025  # 1 VC = $0.00025
            
            logger.info(f"✅ Using Vocalis Credits balance: {total_balance} VC")
            
        else:
            # Fallback to USD calculation if no Vocalis Credits found
            logger.warning(f"⚠️ No Vocalis Credits found, falling back to USD calculation")
            
            # Convert cents to credits using old logic
            total_balance = int(usd_balance_for_reference / 0.025) if usd_balance_for_reference > 0 else 0
            currency = "USD"
            dollar_value = usd_balance_for_reference / 100
            
            print("=" * 70)
            print("⚠️ FALLBACK TO USD CALCULATION:")
            print(f"   USD cents: {usd_balance_for_reference}")
            print(f"   Calculated credits: {total_balance}")
            print(f"   This should not happen once Vocalis Credits are set up!")
            print("=" * 70)

        logger.info(f"✅ Final balance for {customer_id}: {total_balance} {currency}")

        return {
            "customer_id": customer_id,
            "balance": total_balance,
            "currency": currency,
            "dollar_value": dollar_value,
            "last_updated": datetime.now().isoformat(),
            "source": "metronome_api",
            "credit_type_id": VOCALIS_CREDIT_TYPE_ID if found_vocalis_credits else "2714e483-4ff1-48e4-9e25-ac732e8f24f2",
            "debug_info": {
                "found_vocalis_credits": found_vocalis_credits,
                "vocalis_balance": vocalis_balance,
                "usd_balance_cents": usd_balance_for_reference,
                "balance_entries_count": len(balances)
            }
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
    

    async def safe_release_threshold_billing(self, workflow_id: str, outcome: str) -> Dict[str, Any]:
        """Safely release threshold billing, handling already-committed states"""
        try:
            result = await self.release_threshold_billing(workflow_id, outcome)
            logger.info(f"✅ Successfully released workflow {workflow_id}")
            return {"success": True, "result": result}
            
        except Exception as e:
            error_msg = str(e)
            if "not in COMMITTING state" in error_msg or "already in state COMMITTED" in error_msg:
                # This is OK - someone else processed it
                logger.info(f"ℹ️ Workflow {workflow_id} already committed (this is normal)")
                return {"success": True, "already_committed": True}
            else:
                # Real error
                logger.error(f"❌ Failed to release workflow {workflow_id}: {error_msg}")
                raise

# Global client instance
metronome_client = MetronomeClient()