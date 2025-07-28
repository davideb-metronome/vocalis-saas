"""
Webhook API Routes
Handle Metronome webhooks for billing events and alerts
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import hashlib
import hmac
import json
from datetime import datetime

# Add this import for the Metronome client
from app.services.metronome import metronome_client

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
            # 🎯 KEY WEBHOOK: Auto-recharge payment request
            customer_id = properties.get('customer_id')
            contract_id = properties.get('contract_id')
            invoice_id = properties.get('invoice_id')
            workflow_id = properties.get('workflow_id')
            invoice_total = properties.get('invoice_total')  # Amount in cents
            invoice_currency = properties.get('invoice_currency')
            
            print(f"💳 AUTO-RECHARGE PAYMENT REQUEST:")
            print(f"   Customer: {customer_id}")
            print(f"   Contract: {contract_id}")
            print(f"   Invoice: {invoice_id}")
            print(f"   Workflow: {workflow_id}")
            print(f"   Amount: {invoice_total} cents (${invoice_total/100:.2f})")
            print(f"   Currency: {invoice_currency}")
            print(f"   📝 TODO: Implement payment processing and workflow release")
            
        elif alert_type == 'alerts.usage_threshold_reached':
            print(f"📊 USAGE THRESHOLD REACHED")
            
        elif alert_type == 'alerts.spend_threshold_reached':
            print(f"💰 SPEND THRESHOLD REACHED")
            
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