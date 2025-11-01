# services/twilio_service.py

from twilio.rest import Client
from typing import Dict, Any, Optional, List
from config.settings import settings
import traceback

class TwilioService:
    def __init__(self):
        # Get credentials from settings
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        # Initialize client
        if self.account_sid and self.auth_token and self.from_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print(f"✅ Twilio service initialized: {self.from_number}")
            except Exception as e:
                self.client = None
                print(f"❌ Twilio initialization error: {e}")
        else:
            self.client = None
            print("❌ Twilio credentials missing in settings")
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone for Twilio WhatsApp
        Input: +919649385555 or 919649385555
        Output: whatsapp:+919649385555
        """
        # Remove existing whatsapp: prefix
        cleaned = phone.replace("whatsapp:", "").strip()
        
        # Add + if not present
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        
        # Add whatsapp: prefix
        result = f"whatsapp:{cleaned}"
        
        return result
    
    async def send_text_message(
        self, 
        to: str, 
        message: str,
        **kwargs  # For compatibility with gallabox_service
    ) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        
        if not self.client:
            print("❌ Twilio client not initialized")
            return {
                "success": False,
                "error": "Twilio not configured"
            }
        
        try:
            # Normalize phone numbers
            to_number = self._normalize_phone(to)
            from_number = self._normalize_phone(self.from_number)
            
            print(f"\n{'='*70}")
            print("📤 SENDING MESSAGE VIA TWILIO")
            print(f"{'='*70}")
            print(f"📞 To: {to_number}")
            print(f"📞 From: {from_number}")
            print(f"💬 Message: {message[:100]}...")
            
            # Send message
            twilio_msg = self.client.messages.create(
                from_=from_number,
                body=message,
                to=to_number
            )
            
            print(f"✅ Message sent successfully!")
            print(f"🆔 SID: {twilio_msg.sid}")
            print(f"📊 Status: {twilio_msg.status}")
            print(f"{'='*70}\n")
            
            return {
                "success": True,
                "messageId": twilio_msg.sid,
                "message_id": twilio_msg.sid,  # Alias for compatibility
                "status": twilio_msg.status,
                "to": to_number,
                "from": from_number
            }
            
        except Exception as e:
            print(f"❌ Twilio send error: {e}")
            traceback.print_exc()
            print(f"{'='*70}\n")
            
            return {
                "success": False,
                "error": str(e),
                "to": to
            }
    
    async def send_image_message(
        self,
        to: str,
        image_url: str,
        caption: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send image via Twilio (as media)"""
        
        if not self.client:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            to_number = self._normalize_phone(to)
            from_number = self._normalize_phone(self.from_number)
            
            print(f"📸 Sending image to {to_number}")
            
            # Twilio supports media URLs
            twilio_msg = self.client.messages.create(
                from_=from_number,
                body=caption if caption else "Image",
                media_url=[image_url],  # Twilio accepts list of media URLs
                to=to_number
            )
            
            print(f"✅ Image sent! SID: {twilio_msg.sid}")
            
            return {
                "success": True,
                "messageId": twilio_msg.sid,
                "message_id": twilio_msg.sid
            }
            
        except Exception as e:
            print(f"❌ Image send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_document_message(
        self,
        to: str,
        document_url: str,
        filename: str = None,
        caption: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send document via Twilio"""
        
        if not self.client:
            return {"success": False, "error": "Twilio not configured"}
        
        try:
            to_number = self._normalize_phone(to)
            from_number = self._normalize_phone(self.from_number)
            
            print(f"📄 Sending document to {to_number}")
            
            body = caption if caption else (filename if filename else "Document")
            
            twilio_msg = self.client.messages.create(
                from_=from_number,
                body=body,
                media_url=[document_url],
                to=to_number
            )
            
            print(f"✅ Document sent! SID: {twilio_msg.sid}")
            
            return {
                "success": True,
                "messageId": twilio_msg.sid,
                "message_id": twilio_msg.sid
            }
            
        except Exception as e:
            print(f"❌ Document send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        body_params: List[str] = None,
        header_params: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send template message
        Note: Twilio templates work differently than Gallabox
        For now, we'll just send a text approximation
        """
        print(f"⚠️ Template messages not fully supported in Twilio test mode")
        print(f"   Template: {template_name}")
        
        # Simple fallback: just send the template name
        message = f"[Template: {template_name}]"
        if body_params:
            message += f"\nParams: {', '.join(body_params)}"
        
        return await self.send_text_message(to, message)
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """Get status of sent message"""
        
        if not self.client:
            return {"error": "Twilio not configured"}
        
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "success": True,
                "sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except Exception as e:
            print(f"❌ Get status error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get service stats (for compatibility with gallabox_service)"""
        return {
            "service": "Twilio",
            "from_number": self.from_number,
            "configured": self.client is not None,
            "requests_in_window": 0,  # Twilio handles rate limiting internally
            "max_requests": "N/A",
            "circuit_breaker_open": False
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "service": "Twilio",
            "configured": self.client is not None,
            "from_number": self.from_number,
            "account_sid": self.account_sid[:8] + "..." if self.account_sid else None
        }
    
    def reset_circuit_breaker(self):
        """Placeholder for compatibility"""
        print("ℹ️ Twilio doesn't use circuit breaker")
        pass


# Create singleton instance
twilio_service = TwilioService()