import os
import asyncio
import datetime
from typing import Dict, Optional
from fastapi import Request, HTTPException

# ==========================================
# IMPORT SERVICES - PRODUCTION ONLY
# ==========================================
from services import gallabox_service
from services.response_service import response_service
from services.jira_service import jira_service
from services.intent_service import intent_service
from config.settings import settings

print(f"🎯 Webhook handler loaded gallabox: {type(gallabox_service).__name__}")


# ======================
# CONFIGURATION
# ======================
WEBHOOK_DUPLICATE_WINDOW = 300  # 5 minutes
VALID_MESSAGE_TYPES = ["text", "image", "document", "audio", "video"]
MAX_WEBHOOK_TRACKER_SIZE = 10000  # Prevent memory overflow


# ======================
# DUPLICATE WEBHOOK TRACKER
# ======================
class WebhookTracker:
    """Thread-safe webhook tracker with automatic cleanup"""
    
    def __init__(self, window_seconds: int = WEBHOOK_DUPLICATE_WINDOW):
        self._tracker: Dict[str, float] = {}
        self._window = window_seconds
        self._last_cleanup = datetime.datetime.now().timestamp()
    
    def is_duplicate(self, message_id: str) -> bool:
        """Check if message is duplicate and add to tracker"""
        now = datetime.datetime.now().timestamp()
        
        # Auto cleanup every minute
        if now - self._last_cleanup > 60:
            self._cleanup(now)
        
        # Check duplicate
        if message_id in self._tracker:
            return True
        
        # Prevent memory overflow
        if len(self._tracker) > MAX_WEBHOOK_TRACKER_SIZE:
            self._cleanup(now)
        
        # Add to tracker
        self._tracker[message_id] = now
        return False
    
    def _cleanup(self, current_time: float):
        """Remove old entries"""
        cutoff = current_time - self._window
        self._tracker = {k: v for k, v in self._tracker.items() if v > cutoff}
        self._last_cleanup = current_time
        print(f"🧹 Webhook tracker cleaned. Current size: {len(self._tracker)}")
    
    def size(self) -> int:
        return len(self._tracker)
    
    def clear(self):
        self._tracker.clear()


# Global tracker instance
webhook_tracker = WebhookTracker()


# ======================
# WEBHOOK HANDLER
# ======================
async def receive_webhook(request: Request) -> dict:
    """
    Main webhook receiver with robust error handling
    """
    try:
        # Parse request
        data = await request.json()
        
        # Extract message details
        whatsapp_data = data.get("whatsapp", {})
        contact_data = data.get("contact", {})
        
        message_id = (
            whatsapp_data.get("messageId") or 
            data.get("id") or 
            f"msg-{int(datetime.datetime.now().timestamp() * 1000)}"
        )
        message_type = whatsapp_data.get("type")
        status = whatsapp_data.get("status")
        sender = whatsapp_data.get("from")
        user_name = contact_data.get("name", "User")
        
        print(f"📨 Webhook received: ID={message_id}, Type={message_type}, Status={status}, From={sender}")
        
        # Duplicate check
        if webhook_tracker.is_duplicate(message_id):
            print(f"🚫 Duplicate webhook blocked: {message_id}")
            return {"status": "duplicate_blocked"}
        
        # Validate required fields
        if status != "received":
            print(f"⏭️ Skipping non-received status: {status}")
            return {"status": "ignored_status"}
        
        if not sender:
            print("⚠️ Missing sender information")
            return {"status": "error", "message": "Missing sender"}
        
        # Validate message type
        if message_type not in VALID_MESSAGE_TYPES:
            print(f"⚠️ Unsupported message type: {message_type}")
            await gallabox_service.send_text_message(
                sender, 
                "Sorry, this message type is not supported. Please send text or file messages."
            )
            return {"status": "unsupported_type"}
        
        # Process based on message type
        if message_type == "text":
            await _handle_text_message(data, sender, user_name, message_id)
        
        elif message_type in ["image", "document", "audio", "video"]:
            await _handle_file_message(data, sender, user_name, message_id, message_type)
        
        return {"status": "processed", "messageId": message_id}
    
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


async def _handle_text_message(data: dict, sender: str, user_name: str, message_id: str):
    """Handle text message processing"""
    try:
        text = data.get("whatsapp", {}).get("text", {}).get("body", "").strip()
        
        if not text:
            print("⚠️ Empty text message received")
            return
        
        print(f"💬 Processing text: '{text[:50]}...' from {user_name}")
        
        # Process through intent service
        await intent_service.process_message(
            user_phone=sender,
            user_name=user_name,
            message_text=text
        )
        
        print(f"✅ Text message processed: {message_id}")
    
    except Exception as e:
        print(f"❌ Text message processing error: {e}")
        import traceback
        traceback.print_exc()
        await _send_error_response(sender, "text message")


async def _handle_file_message(data: dict, sender: str, user_name: str, message_id: str, message_type: str):
    """Handle file message processing"""
    try:
        content = data.get("whatsapp", {}).get(message_type, {})
        link = content.get("link")
        caption = content.get("caption", "")
        
        if not link:
            print(f"⚠️ No link found in {message_type} message")
            await gallabox_service.send_text_message(
                sender, 
                f"Sorry, couldn't access the {message_type}. Please try again."
            )
            return
        
        print(f"📎 Processing {message_type}: {link[:50]}... from {user_name}")
        
        # For now, acknowledge file receipt and ask for text description
        message = f"📎 I received your {message_type}."
        
        if caption:
            message += f"\n\nYou wrote: {caption}"
            # Process caption as text
            await intent_service.process_message(
                user_phone=sender,
                user_name=user_name,
                message_text=caption
            )
        else:
            message += "\n\nPlease describe the issue you're facing."
            await gallabox_service.send_text_message(sender, message)
        
        print(f"✅ {message_type.capitalize()} message processed: {message_id}")
    
    except Exception as e:
        print(f"❌ File message processing error: {e}")
        import traceback
        traceback.print_exc()
        await _send_error_response(sender, message_type)


async def _send_error_response(sender: str, message_type: str):
    """Send error response to user"""
    try:
        await gallabox_service.send_text_message(
            sender,
            f"Sorry, there was an error processing your {message_type}. Please try again later."
        )
    except Exception as e:
        print(f"❌ Failed to send error response: {e}")


# ======================
# MANUAL MESSAGE SENDING
# ======================
async def send_message(req_body: dict) -> dict:
    """Send a text message manually"""
    try:
        to = req_body.get("to")
        message = req_body.get("message")
        
        if not to or not message:
            return {
                "success": False, 
                "error": "Missing required fields: 'to' and 'message'"
            }
        
        print(f"📤 Sending manual message to {to}")
        result = await gallabox_service.send_text_message(to, message)
        
        return {
            "success": result.get("success", False),
            "message": "Text message sent successfully" if result.get("success") else "Failed to send message",
            "data": result
        }
    
    except Exception as e:
        print(f"❌ Send message error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


async def send_template_message(req_body: dict) -> dict:
    """Send a WhatsApp template message"""
    try:
        to = req_body.get("to")
        template_name = req_body.get("templateName")
        language_code = req_body.get("languageCode", "en")
        body_params = req_body.get("bodyParameters", [])
        header_params = req_body.get("headerParameters", [])
        
        if not to or not template_name:
            return {
                "success": False,
                "error": "Missing required fields: 'to' and 'templateName'"
            }
        
        print(f"📋 Sending template '{template_name}' to {to}")
        result = await gallabox_service.send_template_message(
            to=to,
            template_name=template_name,
            language_code=language_code,
            body_params=body_params,
            header_params=header_params
        )
        
        return {
            "success": result.get("success", False),
            "message": "Template message sent successfully" if result.get("success") else "Failed to send template",
            "data": result
        }
    
    except Exception as e:
        print(f"❌ Send template error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


# ======================
# HEALTH CHECK
# ======================
async def health_check() -> dict:
    """System health check endpoint"""
    try:
        # Check JIRA connection
        jira_status = "Not Configured"
        
        if all([settings.JIRA_HOST, settings.JIRA_EMAIL, settings.JIRA_API_TOKEN]):
            try:
                is_connected = await jira_service.test_jira_connection()
                jira_status = "Connected ✅" if is_connected else "Configuration Error ❌"
            except Exception as e:
                jira_status = f"Error: {str(e)}"
        
        return {
            "status": "OK",
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": settings.NODE_ENV,
            "mock_mode": settings.MOCK_MODE,
            "services": {
                "gallabox": {
                    "status": "Configured ✅" if settings.GALLABOX_API_KEY else "Not Configured ❌",
                    "type": type(gallabox_service).__name__,
                    "mock": settings.MOCK_MODE
                },
                "jira": jira_status,
                "openai": "Configured ✅" if settings.OPENAI_API_KEY else "Not Configured ❌"
            },
            "stats": {
                "pendingTickets": response_service.get_pending_tickets_count(),
                "webhookTrackerSize": webhook_tracker.size()
            }
        }
    
    except Exception as e:
        print(f"❌ Health check error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "ERROR",
            "timestamp": datetime.datetime.now().isoformat(),
            "error": str(e)
        }


# ======================
# MEMORY MANAGEMENT
# ======================
async def clear_memory(phone: str) -> dict:
    """Clear memory for a specific user"""
    try:
        if not phone:
            return {"success": False, "error": "Phone number required"}
        
        print(f"🧹 Clearing memory for {phone}")
        ticket_cleared = response_service.clear_pending_ticket(phone)
        
        return {
            "success": True,
            "phone": phone,
            "ticketCleared": ticket_cleared
        }
    
    except Exception as e:
        print(f"❌ Clear memory error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


async def clear_all_memories() -> dict:
    """Clear all user memories"""
    try:
        print("🧹 Clearing all memories")
        cleaned = response_service.cleanup_old_pending_tickets()
        webhook_tracker.clear()
        
        return {
            "success": True,
            "ticketsCleared": cleaned,
            "webhookTrackerCleared": True
        }
    
    except Exception as e:
        print(f"❌ Clear all memories error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


# ======================
# DEBUG & STATS
# ======================
async def get_user_statistics(phone: str) -> dict:
    """Get statistics for a specific user"""
    try:
        if not phone:
            return {"success": False, "error": "Phone number required"}
        
        pending_ticket = response_service.get_pending_ticket(phone)
        user_stats = response_service.get_user_stats(phone)
        
        return {
            "success": True,
            "phone": phone,
            "stats": user_stats,
            "pendingTicket": {
                "summary": pending_ticket.summary,
                "team": pending_ticket.team,
                "project_key": pending_ticket.project_key,
                "priority": pending_ticket.priority.value,
                "timestamp": pending_ticket.timestamp.isoformat()
            } if pending_ticket else None
        }
    
    except Exception as e:
        print(f"❌ Get user stats error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


async def get_all_tickets() -> dict:
    """Get all pending tickets"""
    try:
        tickets = response_service.get_all_pending_tickets()
        
        formatted_tickets = {
            phone: {
                "summary": ticket.summary,
                "team": ticket.team,
                "project_key": ticket.project_key,
                "priority": ticket.priority.value,
                "timestamp": ticket.timestamp.isoformat(),
                "awaiting_confirmation": ticket.awaiting_confirmation
            }
            for phone, ticket in tickets.items()
        }
        
        return {
            "success": True,
            "count": len(formatted_tickets),
            "tickets": formatted_tickets
        }
    
    except Exception as e:
        print(f"❌ Get all tickets error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }