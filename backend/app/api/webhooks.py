"""
Webhook API Routes
Handle Metronome webhooks for billing events and alerts
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Set
import hashlib
import hmac
import json
import asyncio
from datetime import datetime


# Add this import for the Metronome client
from app.services.metronome import metronome_client
from app.utils.email import send_welcome_email
from app.core.config import settings

active_connections: Dict[str, Set[asyncio.Queue]] = {}
# In-memory idempotency store for webhook IDs we've already processed
processed_webhook_ids: Set[str] = set()

router = APIRouter()

@router.post("/metronome/alerts")
async def handle_metronome_alerts(request: Request):
    """
    ✅ ENHANCED: Handle Metronome alert webhooks with auto-recharge processing
    
    Common alert types:
    - alerts.low_remaining_credit_balance_reached
    - alerts.usage_threshold_reached
    - alerts.spend_threshold_reached
    - payment_gate.threshold_reached
    - payment_gate.external_initiate ← KEY: Auto-recharge payment request
    """
    try:
        # Get headers for verification
        headers = dict(request.headers)
        
        # Get webhook data
        webhook_data = await request.json()
        
        # 🔍 COMPREHENSIVE WEBHOOK LOGGING
        print("=" * 70)
        print("🔔 METRONOME ALERT WEBHOOK RECEIVED:")
        print(f"   Webhook ID: {webhook_data.get('id')}")
        print(f"   Type: {webhook_data.get('type')}")
        print(f"   Timestamp: {headers.get('date')}")
        print(f"   Properties: {json.dumps(webhook_data.get('properties', {}), indent=2)}")
        print(f"   Full Headers: {headers}")
        print("=" * 70)
        
        # Handle specific alert types
        alert_type = webhook_data.get('type')
        properties = webhook_data.get('properties', {})
        
        if alert_type == 'alerts.low_remaining_credit_balance_reached':
            customer_id = properties.get('customer_id')
            remaining_balance = properties.get('remaining_balance')
            threshold = properties.get('threshold')
            
            print(f"🚨 LOW CREDIT BALANCE ALERT:")
            print(f"   Customer: {customer_id}")
            print(f"   Remaining: {remaining_balance} credits")
            print(f"   Threshold: {threshold} credits")
            
        elif alert_type == 'payment_gate.threshold_reached':
            customer_id = properties.get('customer_id')
            contract_id = properties.get('contract_id')
            
            print(f"🎯 AUTO-RECHARGE THRESHOLD REACHED:")
            print(f"   Customer: {customer_id}")
            print(f"   Contract: {contract_id}")
            print(f"   ⏳ Waiting for external_initiate webhook...")
            

        elif alert_type == 'payment_gate.external_initiate':
            # 🎯 KEY WEBHOOK: Auto-recharge payment request - FAKE PAYMENT AND RELEASE
            customer_id = properties.get('customer_id')
            contract_id = properties.get('contract_id')
            invoice_id = properties.get('invoice_id')
            workflow_id = properties.get('workflow_id')
            invoice_total = properties.get('invoice_total')
            invoice_currency = properties.get('invoice_currency')
            
            print(f"💳 AUTO-RECHARGE PAYMENT REQUEST:")
            print(f"   Customer: {customer_id}")
            print(f"   Contract: {contract_id}")
            print(f"   Invoice: {invoice_id}")
            print(f"   Workflow: {workflow_id}")
            print(f"   Amount: {invoice_total} cents (${invoice_total/100:.2f})")
            print(f"   Currency: {invoice_currency}")
            
            if not workflow_id:
                print("❌ No workflow_id provided - cannot process payment")
                return {
                    "status": "error",
                    "message": "Missing workflow_id"
                }
            
            try:
                # 💳 FAKE THE PAYMENT - Just release with "paid" outcome
                print(f"💳 FAKING PAYMENT SUCCESS - Releasing commit...")
                
                # result = await metronome_client.release_threshold_billing(workflow_id, "paid")
                result = await metronome_client.safe_release_threshold_billing(workflow_id, "paid")
                
                if result.get('success'):
                    print(f"✅ COMMIT RELEASED SUCCESSFULLY!")
                    print(f"   Customer {customer_id} now has additional credits!")
                    print(f"   Workflow {workflow_id} completed successfully")
                    
                    # 🚀 ADD THIS NEW SECTION - GET UPDATED BALANCE AND BROADCAST
                    try:
                        print(f"📊 Getting updated balance after auto-recharge...")
                        updated_balance = await metronome_client.get_customer_balance(customer_id)
                        new_credit_balance = updated_balance.get('balance', 0)
                        
                        print(f"📊 BROADCASTING BALANCE UPDATE:")
                        print(f"   Customer: {customer_id}")
                        print(f"   New Balance: {new_credit_balance} credits")
                        
                        # 🚀 BROADCAST REAL-TIME UPDATE TO FRONTEND
                        await broadcast_event(customer_id, {
                            "type": "balance_updated",
                            "new_balance": new_credit_balance,
                            "auto_recharge": True,
                            "message": f"Auto-recharge complete! Added credits to your account.",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        print(f"✅ Real-time balance update sent to frontend!")
                        
                    except Exception as balance_error:
                        print(f"⚠️ Failed to get updated balance: {balance_error}")
                        # Still broadcast a generic update
                        await broadcast_event(customer_id, {
                            "type": "auto_recharge_complete",
                            "message": "Auto-recharge completed successfully!",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                else:
                    print(f"❌ Failed to release commit: {result}")
                    
            except Exception as e:
                print(f"❌ AUTO-RECHARGE RELEASE FAILED: {e}")
                print(f"   Workflow: {workflow_id}")
                print(f"   Customer: {customer_id}")


        elif alert_type == 'alerts.usage_threshold_reached':
            print(f"📊 USAGE THRESHOLD REACHED")
            
        elif alert_type == 'alerts.spend_threshold_reached':
            print(f"💰 SPEND THRESHOLD REACHED")
        
        elif alert_type == 'contract.start':
            # Onboarding email on contract start (offset notification or system event)
            webhook_id = webhook_data.get('id')
            if webhook_id and webhook_id in processed_webhook_ids:
                print(f"ℹ️  Duplicate contract.start webhook {webhook_id} ignored")
            else:
                if webhook_id:
                    processed_webhook_ids.add(webhook_id)

                customer_id = webhook_data.get('customer_id')
                contract_id = webhook_data.get('contract_id')
                cust_fields = webhook_data.get('customer_custom_fields') or {}
                email_to = cust_fields.get('email') or settings.DEMO_EMAIL_TO
                first_name = cust_fields.get('first_name') or ''

                if not email_to:
                    # Try fetching customer to resolve email
                    try:
                        customer = await metronome_client.get_customer(customer_id)
                        # Try to derive email from ingest_aliases/external_id pattern vocalis_<email>
                        ingest_aliases = customer.get('ingest_aliases') or []
                        derived = None
                        for alias in ingest_aliases:
                            if isinstance(alias, str) and alias.startswith('vocalis_') and '@' in alias:
                                derived = alias.replace('vocalis_', '', 1)
                                break
                        # Some APIs may return external_id separately
                        if not derived:
                            ext = customer.get('external_id')
                            if isinstance(ext, str) and ext.startswith('vocalis_') and '@' in ext:
                                derived = ext.replace('vocalis_', '', 1)
                        email_to = derived or settings.DEMO_EMAIL_TO
                    except Exception as resolve_err:
                        print(f"⚠️ Could not resolve customer email: {resolve_err}")

                if email_to:
                    print(f"📧 Sending welcome email to customer {customer_id} → {email_to}")
                    try:
                        # Try to compute trial end date from balances for this contract
                        trial_end_str = None
                        try:
                            balances = await metronome_client.list_customer_balances(customer_id)
                            items = balances.get('data', [])
                            target_end = None
                            for entry in items:
                                if contract_id and entry.get('contract', {}).get('id') != contract_id:
                                    continue
                                sched = (entry.get('access_schedule') or {}).get('schedule_items') or []
                                if sched:
                                    target_end = sched[0].get('ending_before') or target_end
                                if contract_id and target_end:
                                    break
                            if target_end:
                                iso = target_end.replace('Z', '+00:00') if 'Z' in target_end else target_end
                                dt = datetime.fromisoformat(iso)
                                trial_end_str = dt.strftime('%b %d, %Y %H:%M UTC')
                        except Exception as e:
                            print(f"⚠️ Could not compute trial end date: {e}")

                        # Fire and forget; do not block webhook response
                        asyncio.create_task(
                            send_welcome_email(
                                to=email_to,
                                first_name=first_name,
                                credits=settings.METRONOME_TRIAL_CREDITS,
                                trial_days=settings.METRONOME_TRIAL_DAYS,
                                trial_end_date=trial_end_str,
                            )
                        )
                    except Exception as e:
                        print(f"❌ Failed to enqueue welcome email: {e}")
                else:
                    print(f"⚠️ No email available for customer {customer_id}; skipping welcome email")
        
        else:
            print(f"ℹ️  UNKNOWN ALERT TYPE: {alert_type}")
        
        # Always return success to acknowledge receipt
        return {
            "status": "received", 
            "webhook_id": webhook_data.get('id'),
            "type": alert_type,
            "message": "Alert webhook processed successfully"
        }
        
    except Exception as e:
        print(f"❌ Alert webhook processing error: {e}")
        # Still return 200 to avoid retries for malformed requests
        return {
            "status": "error",
            "message": f"Failed to process alert webhook: {str(e)}"
        }
    
@router.post("/metronome/invoices")
async def handle_metronome_invoices(request: Request):
    """
    Handle Metronome invoice webhooks
    
    Invoice webhook types:
    - invoice.finalized
    - invoice.billing_provider_error
    """
    try:
        # Get headers for verification
        headers = dict(request.headers)
        
        # Get webhook data
        webhook_data = await request.json()
        
        # 🔍 COMPREHENSIVE WEBHOOK LOGGING
        print("=" * 70)
        print("🔔 METRONOME INVOICE WEBHOOK RECEIVED:")
        print(f"   Webhook ID: {webhook_data.get('id')}")
        print(f"   Type: {webhook_data.get('type')}")
        print(f"   Timestamp: {headers.get('date')}")
        print(f"   Properties: {json.dumps(webhook_data.get('properties', {}), indent=2)}")
        print(f"   Full Headers: {headers}")
        print("=" * 70)
        
        # Handle specific invoice types
        invoice_type = webhook_data.get('type')
        properties = webhook_data.get('properties', {})
        
        if invoice_type == 'invoice.finalized':
            invoice_id = properties.get('invoice_id')
            customer_id = properties.get('customer_id')
            finalized_date = properties.get('invoice_finalized_date')
            
            print(f"✅ INVOICE FINALIZED:")
            print(f"   Invoice: {invoice_id}")
            print(f"   Customer: {customer_id}")
            print(f"   Finalized: {finalized_date}")
            
            # TODO: Update customer credit balance
            # await update_customer_credits(customer_id, invoice_id)
            
        elif invoice_type == 'invoice.billing_provider_error':
            billing_provider = properties.get('billing_provider')
            error_message = properties.get('billing_provider_error')
            
            print(f"❌ BILLING PROVIDER ERROR:")
            print(f"   Provider: {billing_provider}")
            print(f"   Error: {error_message}")
            
            # TODO: Handle billing errors (notify customer, retry, etc.)
            
        else:
            print(f"ℹ️  UNKNOWN INVOICE TYPE: {invoice_type}")
        
        # Always return success to acknowledge receipt
        return {
            "status": "received",
            "webhook_id": webhook_data.get('id'),
            "type": invoice_type,
            "message": "Invoice webhook processed successfully"
        }
        
    except Exception as e:
        print(f"❌ Invoice webhook processing error: {e}")
        # Still return 200 to avoid retries for malformed requests
        return {
            "status": "error",
            "message": f"Failed to process invoice webhook: {str(e)}"
        }

@router.post("/metronome/payment-gating")
async def handle_metronome_payment_gating(request: Request):
    """
    Handle Metronome payment gating webhooks
    
    Payment gating webhook types:
    - payment_gate.payment_status
    - payment_gate.action_required
    - payment_gate.threshold_reached
    - payment_gate.external_workflow_initiated
    """
    try:
        # Get headers for verification
        headers = dict(request.headers)
        
        # Get webhook data
        webhook_data = await request.json()
        
        # 🔍 COMPREHENSIVE WEBHOOK LOGGING
        print("=" * 70)
        print("🔔 METRONOME PAYMENT GATING WEBHOOK RECEIVED:")
        print(f"   Webhook ID: {webhook_data.get('id')}")
        print(f"   Type: {webhook_data.get('type')}")
        print(f"   Timestamp: {headers.get('date')}")
        print(f"   Properties: {json.dumps(webhook_data.get('properties', {}), indent=2)}")
        print("=" * 70)
        
        # Handle payment gating events
        payment_type = webhook_data.get('type')
        properties = webhook_data.get('properties', {})
        
        if payment_type == 'payment_gate.payment_status':
            payment_status = properties.get('payment_status')
            customer_id = properties.get('customer_id')
            
            print(f"💳 PAYMENT STATUS UPDATE:")
            print(f"   Customer: {customer_id}")
            print(f"   Status: {payment_status}")
            
            if payment_status == 'failed':
                error_message = properties.get('error_message')
                print(f"   Error: {error_message}")
                # TODO: Handle payment failure
                
            elif payment_status == 'succeeded':
                print(f"   ✅ Payment successful")
                # TODO: Handle payment success
        
        else:
            print(f"ℹ️  PAYMENT GATING TYPE: {payment_type}")
        
        return {
            "status": "received",
            "webhook_id": webhook_data.get('id'),
            "type": payment_type,
            "message": "Payment gating webhook processed successfully"
        }
        
    except Exception as e:
        print(f"❌ Payment gating webhook processing error: {e}")
        return {
            "status": "error",
            "message": f"Failed to process payment gating webhook: {str(e)}"
        }

@router.post("/metronome/test")
async def handle_metronome_test(request: Request):
    """
    Generic test endpoint for any Metronome webhook
    Use this for debugging new webhook types
    """
    try:
        headers = dict(request.headers)
        webhook_data = await request.json()
        
        print("=" * 70)
        print("🧪 METRONOME TEST WEBHOOK RECEIVED:")
        print(f"   Full Data: {json.dumps(webhook_data, indent=2)}")
        print(f"   Full Headers: {headers}")
        print("=" * 70)
        
        return {
            "status": "received",
            "message": "Test webhook logged successfully"
        }
        
    except Exception as e:
        print(f"❌ Test webhook error: {e}")
        return {
            "status": "error",
            "message": f"Test webhook failed: {str(e)}"
        }

# Add this function to your webhooks.py file (after the broadcast_event function):

@router.get("/events/{customer_id}")

# Replace your customer_events function with this debug version:

@router.get("/events/{customer_id}")

# Add this to your webhooks.py - FIXED SSE endpoint with proper headers

@router.get("/events/{customer_id}")
async def customer_events(customer_id: str):
    """
    Server-Sent Events endpoint for real-time customer notifications
    ✅ FIXED: Added proper SSE headers and CORS support
    """
    print(f"🔥 SSE ENDPOINT CALLED for customer: {customer_id}")
    
    async def event_stream():
        print(f"🔥 EVENT STREAM STARTING for customer: {customer_id}")
        
        # Create a queue for this connection
        queue = asyncio.Queue()
        
        # Add to active connections
        if customer_id not in active_connections:
            active_connections[customer_id] = set()
        active_connections[customer_id].add(queue)
        
        print(f"🔌 SSE connection opened for customer {customer_id}")
        print(f"🔥 ABOUT TO YIELD INITIAL EVENT")
        
        try:
            # Send initial connection event
            initial_data = json.dumps({'type': 'connected', 'message': 'Real-time updates active'})
            initial_event = f"data: {initial_data}\n\n"
            print(f"🔥 YIELDING: {initial_event}")
            yield initial_event
            
            print(f"🔥 INITIAL EVENT YIELDED, STARTING EVENT LOOP")
            
            # Listen for events
            while True:
                try:
                    # Wait for event with timeout to send keep-alive
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    event_str = f"data: {json.dumps(event_data)}\n\n"
                    print(f"🔥 YIELDING EVENT: {event_str}")
                    yield event_str
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    ping_data = json.dumps({'type': 'ping'})
                    ping_event = f"data: {ping_data}\n\n"
                    print(f"🔥 YIELDING PING: {ping_event}")
                    yield ping_event
                    
        except asyncio.CancelledError:
            # Connection closed
            print(f"🔌 SSE connection closed for customer {customer_id}")
        except Exception as e:
            print(f"❌ SSE ERROR: {e}")
        finally:
            # Clean up connection
            if customer_id in active_connections:
                active_connections[customer_id].discard(queue)
                if not active_connections[customer_id]:
                    del active_connections[customer_id]
            print(f"🔥 SSE CLEANUP COMPLETE for customer {customer_id}")
    
    print(f"🔥 RETURNING STREAMING RESPONSE")
    
    # ✅ FIXED: Return StreamingResponse with proper SSE headers
    return StreamingResponse(
        event_stream(), 
        media_type="text/plain",
        headers={
            # Critical SSE headers
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            
            # CORS headers for SSE
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )

async def broadcast_event(customer_id: str, event_data: dict):
    """
    Broadcast an event to all active connections for a customer
    """
    if customer_id in active_connections:
        print(f"📡 Broadcasting to {len(active_connections[customer_id])} connections for customer {customer_id}")
        # Send to all active connections for this customer
        for queue in active_connections[customer_id]:
            try:
                await queue.put(event_data)
            except Exception as e:
                print(f"Failed to send event to queue: {e}")
    else:
        print(f"📡 No active connections for customer {customer_id}")

# TODO: Add webhook signature verification function
def verify_webhook_signature(signature: str, date_header: str, body: bytes, secret_key: str) -> bool:
    """
    Verify Metronome webhook signature
    
    Formula: HMAC_SHA256(secret_key, DATE_HEADER + "\n" + BODY)
    """
    try:
        # Construct the payload for HMAC
        payload = f"{date_header}\n{body.decode('utf-8')}"
        
        # Compute HMAC-SHA256
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        print(f"❌ Signature verification error: {e}")
        return False
