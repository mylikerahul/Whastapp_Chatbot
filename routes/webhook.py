from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from datetime import datetime
from typing import Dict, Any
import hmac
import hashlib
import traceback
import json

from services.intent_service import intent_service
from services.gallabox_service import gallabox_service
from services.jira_service import jira_service
from models.schemas import Priority
from config.settings import settings

router = APIRouter()

# ==========================================
# WEBHOOK SIGNATURE VERIFICATION
# ==========================================

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook request authenticity"""
    webhook_secret = getattr(settings, 'GALLABOX_WEBHOOK_SECRET', None)
    
    if not webhook_secret:
        print("⚠️ No webhook secret configured, skipping verification")
        return True
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(signature, expected_signature)
    if not is_valid:
        print(f"❌ Signature mismatch! Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
    return is_valid

# ==========================================
# BACKGROUND PROCESSING
# ==========================================

async def process_webhook_async(data: Dict[str, Any]):
    """Background task to process webhook"""
    user_phone = None
    
    try:
        print(f"\n{'='*70}")
        print("🔄 WEBHOOK PROCESSING STARTED")
        print(f"{'='*70}")
        
        message_data = data.get('data', {})
        message_type = message_data.get('type', 'text')
        
        print(f"📋 Message type: {message_type}")
        
        if message_type != 'text':
            print(f"⚠️ Unsupported message type: {message_type}")
            return
        
        user_phone = message_data.get('from', '')
        user_name = message_data.get('name', 'User')
        message_text = message_data.get('text', {}).get('body', '')
        
        print(f"👤 User Phone: {user_phone}")
        print(f"👤 User Name: {user_name}")
        print(f"💬 Message Text: '{message_text}'")
        
        if not message_text or not user_phone:
            print("❌ Missing message text or phone number")
            return
        
        print(f"\n{'='*70}")
        print("🤖 CALLING INTENT SERVICE")
        print(f"{'='*70}")
        
        try:
            response_result = await intent_service.process_message(
                user_phone=user_phone,
                user_name=user_name,
                message_text=message_text
            )
            
            print(f"\n{'='*70}")
            print("📤 INTENT SERVICE RESPONSE RECEIVED")
            print(f"{'='*70}")
            print(f"✅ Response: {response_result}")
            
        except Exception as intent_error:
            print(f"\n{'='*70}")
            print("❌ INTENT SERVICE ERROR")
            print(f"{'='*70}")
            print(f"Error: {intent_error}")
            traceback.print_exc()
            
            try:
                await gallabox_service.send_text_message(
                    to=user_phone,
                    message="Sorry, I encountered an error. Please try again or contact support."
                )
            except Exception as send_error:
                print(f"❌ Failed to send error message: {send_error}")
        
        print(f"\n{'='*70}")
        print("✅ WEBHOOK PROCESSING COMPLETED")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n{'='*70}")
        print("❌ CRITICAL ERROR IN WEBHOOK PROCESSING")
        print(f"{'='*70}")
        print(f"Error: {e}")
        traceback.print_exc()
        
        if user_phone:
            try:
                await gallabox_service.send_text_message(
                    to=user_phone,
                    message="Sorry, something went wrong. Please try again later."
                )
            except Exception as send_error:
                print(f"❌ Failed to send error message: {send_error}")

# ==========================================
# GALLABOX WEBHOOK
# ==========================================

@router.post("/webhook/gallabox")
async def gallabox_webhook(request: Request, background_tasks: BackgroundTasks):
    """Main webhook endpoint for Gallabox/WhatsApp messages"""
    try:
        print(f"\n{'='*70}")
        print("📥 GALLABOX WEBHOOK REQUEST RECEIVED")
        print(f"{'='*70}")
        
        body = await request.body()
        signature = request.headers.get('X-Gallabox-Signature', '')
        
        if signature and not verify_webhook_signature(body, signature):
            print("❌ Invalid signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = await request.json()
        event_type = data.get('event', '')
        
        print(f"📋 Event type: {event_type}")
        print(f"📋 Full payload: {json.dumps(data, indent=2)}")
        
        if event_type != 'message:in:new':
            print(f"⚠️ Ignoring event: {event_type}")
            return {"status": "ignored", "reason": f"Event '{event_type}' not handled"}
        
        background_tasks.add_task(process_webhook_async, data)
        
        print(f"✅ Webhook accepted, processing in background")
        print(f"{'='*70}\n")
        
        return {"status": "received", "message": "Webhook processing started"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhook/gallabox")
async def gallabox_webhook_verification(request: Request):
    """Webhook verification endpoint"""
    verify_token = request.query_params.get('hub.verify_token', '')
    challenge = request.query_params.get('hub.challenge', '')
    
    print(f"🔍 Webhook verification request")
    
    expected_token = getattr(settings, 'VERIFY_TOKEN', '')
    
    if verify_token == expected_token:
        print("✅ Verification token matched!")
        return int(challenge) if challenge else {"status": "verified"}
    
    print("⚠️ Verification token mismatch")
    return {"status": "ok", "message": "Webhook endpoint active"}

# ==========================================
# TWILIO WEBHOOK (FIXED)
# ==========================================

@router.post("/webhook/twilio")
async def twilio_webhook(request: Request, background_tasks: BackgroundTasks):
    """Twilio WhatsApp webhook"""
    try:
        print(f"\n{'='*70}")
        print("📥 TWILIO WEBHOOK RECEIVED")
        print(f"{'='*70}")
        
        form_data = await request.form()
        
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        message_body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        profile_name = form_data.get("ProfileName", "User")
        
        print(f"📞 From: {from_number}")
        print(f"👤 Name: {profile_name}")
        print(f"💬 Message: {message_body}")
        print(f"🆔 SID: {message_sid}")
        print(f"{'='*70}\n")
        
        # Convert to standard webhook format
        webhook_data = {
            "event": "message:in:new",
            "data": {
                "from": from_number,
                "name": profile_name,
                "type": "text",
                "text": {"body": message_body},
                "messageId": message_sid,
                "timestamp": int(datetime.now().timestamp())
            }
        }
        
        # Process in background
        background_tasks.add_task(process_webhook_async, webhook_data)
        
        # Return TwiML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
        
    except Exception as e:
        print(f"❌ Twilio webhook error: {e}")
        traceback.print_exc()
        
        # Always return valid TwiML
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

# ==========================================
# TEST ENDPOINTS
# ==========================================

@router.post("/webhook/test")
async def test_webhook(request: Request):
    """Test endpoint for development"""
    try:
        data = await request.json()
        
        test_phone = data.get('phone', '+919649385555')
        test_name = data.get('name', 'Test User')
        test_message = data.get('message', 'Test message')
        
        print(f"\n{'='*70}")
        print("🧪 TEST WEBHOOK")
        print(f"{'='*70}")
        print(f"📞 Phone: {test_phone}")
        print(f"👤 Name: {test_name}")
        print(f"💬 Message: {test_message}")
        
        result = await intent_service.process_message(
            user_phone=test_phone,
            user_name=test_name,
            message_text=test_message
        )
        
        print(f"\n✅ Result: {result}")
        print(f"{'='*70}\n")
        
        return {
            "status": "success",
            "test_data": {
                "phone": test_phone,
                "name": test_name,
                "message": test_message
            },
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Test webhook error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/create-ticket")
async def test_create_ticket(request: Request):
    """Test Jira ticket creation directly"""
    try:
        data = await request.json()
        
        summary = data.get('summary', 'Test Ticket from API')
        description = data.get('description', 'This is a test ticket to verify Jira integration')
        project_key = data.get('project_key', settings.JIRA_PROJECT_KEY)
        priority_str = data.get('priority', 'MEDIUM')
        
        # Convert string to Priority enum
        try:
            priority = Priority[priority_str.upper()]
        except:
            priority = Priority.MEDIUM
        
        print(f"\n{'='*70}")
        print("🧪 TEST JIRA TICKET CREATION")
        print(f"{'='*70}")
        print(f"📋 Summary: {summary}")
        print(f"📋 Description: {description}")
        print(f"📋 Project: {project_key}")
        print(f"📋 Priority: {priority.value}")
        
        result = await jira_service.create_ticket(
            summary=summary,
            description=description,
            project_key=project_key,
            priority=priority,
            issue_type="Task"
        )
        
        print(f"\n✅ Result: {json.dumps(result, indent=2)}")
        print(f"{'='*70}\n")
        
        return {
            "success": result.get('success'),
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Test create ticket error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/test/jira-connection")
async def test_jira_connection():
    """Test Jira connection"""
    try:
        print(f"\n{'='*70}")
        print("🧪 TESTING JIRA CONNECTION")
        print(f"{'='*70}")
        
        is_connected = await jira_service.test_jira_connection()
        
        if is_connected:
            # Get projects
            projects = await jira_service.get_all_projects()
            
            return {
                "success": True,
                "connected": True,
                "jira_host": settings.JIRA_HOST,
                "default_project": settings.JIRA_PROJECT_KEY,
                "available_projects": [
                    {"key": p.key, "name": p.name} for p in projects
                ]
            }
        else:
            return {
                "success": False,
                "connected": False,
                "error": "Failed to connect to Jira"
            }
        
    except Exception as e:
        print(f"❌ Jira connection test error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.post("/test/send-message")
async def test_send_message(request: Request):
    """Test sending message via Gallabox"""
    try:
        data = await request.json()
        
        to = data.get('to', '+919649385555')
        message = data.get('message', 'Test message from webhook')
        
        print(f"\n{'='*70}")
        print("🧪 TEST SEND MESSAGE")
        print(f"{'='*70}")
        print(f"📞 To: {to}")
        print(f"💬 Message: {message}")
        
        result = await gallabox_service.send_text_message(to, message)
        
        print(f"\n✅ Result: {json.dumps(result, indent=2)}")
        print(f"{'='*70}\n")
        
        return {
            "success": result.get('success', False),
            "result": result
        }
        
    except Exception as e:
        print(f"❌ Test send message error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ==========================================
# CLEANUP ENDPOINT
# ==========================================

@router.post("/webhook/cleanup")
async def cleanup_pending_tickets():
    """Cleanup old pending tickets"""
    try:
        cleaned = intent_service.cleanup_old_pending_tickets()
        return {
            "status": "success",
            "message": "Pending tickets cleaned up",
            "cleaned_count": cleaned
        }
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Jira connection
        jira_connected = await jira_service.test_jira_connection()
        
        return {
            "status": "healthy",
            "service": "WhatsApp-Jira Integration",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "jira": {
                    "connected": jira_connected,
                    "host": settings.JIRA_HOST,
                    "project": settings.JIRA_PROJECT_KEY
                },
                "gallabox": {
                    "configured": bool(settings.GALLABOX_API_KEY)
                },
                "openai": {
                    "configured": bool(settings.OPENAI_API_KEY)
                }
            }
        }
    except Exception as e:
        print(f"❌ Health check error: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# ==========================================
# DEBUG ENDPOINTS
# ==========================================

@router.get("/debug/settings")
async def debug_settings():
    """Show current settings (safe values only)"""
    return {
        "jira": {
            "host": settings.JIRA_HOST,
            "project": settings.JIRA_PROJECT_KEY,
            "email": settings.JIRA_EMAIL[:3] + "***" if settings.JIRA_EMAIL else None,
            "token_configured": bool(settings.JIRA_API_TOKEN)
        },
        "gallabox": {
            "api_key_configured": bool(settings.GALLABOX_API_KEY),
            "base_url": getattr(settings, 'GALLABOX_BASE_URL', None)
        },
        "openai": {
            "api_key_configured": bool(settings.OPENAI_API_KEY)
        },
        "environment": settings.NODE_ENV,
        "mock_mode": settings.MOCK_MODE
    }

@router.post("/debug/process-message")
async def debug_process_message(request: Request):
    """Debug message processing with full logs"""
    try:
        data = await request.json()
        
        user_phone = data.get('phone', '+919649385555')
        user_name = data.get('name', 'Debug User')
        message_text = data.get('message', 'Debug message')
        
        print(f"\n{'='*70}")
        print("🐛 DEBUG MESSAGE PROCESSING")
        print(f"{'='*70}")
        print(f"📞 Phone: {user_phone}")
        print(f"👤 Name: {user_name}")
        print(f"💬 Message: {message_text}")
        print(f"{'='*70}\n")
        
        result = await intent_service.process_message(
            user_phone=user_phone,
            user_name=user_name,
            message_text=message_text
        )
        
        return {
            "success": True,
            "input": {
                "phone": user_phone,
                "name": user_name,
                "message": message_text
            },
            "output": result
        }
        
    except Exception as e:
        print(f"❌ Debug process message error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ==========================================
# JIRA DEBUG ENDPOINTS
# ==========================================

@router.get("/debug/jira/projects")
async def debug_jira_projects():
    """Get all Jira projects"""
    try:
        projects = await jira_service.get_all_projects()
        return {
            "success": True,
            "count": len(projects),
            "projects": [
                {
                    "key": p.key,
                    "name": p.name,
                    "description": p.description,
                    "lead": p.lead
                }
                for p in projects
            ]
        }
    except Exception as e:
        print(f"❌ Debug jira projects error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/debug/jira/issue-types/{project_key}")
async def debug_jira_issue_types(project_key: str):
    """Get issue types for a project"""
    try:
        issue_types = jira_service._get_project_issue_types(project_key)
        return {
            "success": True,
            "project_key": project_key,
            "issue_types": issue_types
        }
    except Exception as e:
        print(f"❌ Debug jira issue types error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/debug/jira/priorities")
async def debug_jira_priorities():
    """Get available priorities"""
    try:
        priorities = jira_service._get_project_priorities(settings.JIRA_PROJECT_KEY)
        return {
            "success": True,
            "priorities": priorities
        }
    except Exception as e:
        print(f"❌ Debug jira priorities error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@router.get("/debug/jira/ticket/{ticket_key}")
async def debug_jira_ticket(ticket_key: str):
    """Get ticket details"""
    try:
        ticket = await jira_service.get_ticket_status(ticket_key)
        return {
            "success": ticket.get('success', False),
            "ticket": ticket
        }
    except Exception as e:
        print(f"❌ Debug jira ticket error: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }