# services/gallabox_service.py
"""
🔥 ADVANCED GALLABOX WHATSAPP INTEGRATION SERVICE
Production-grade with media handling, templates, rate limiting, and monitoring
"""

import httpx
import asyncio
from config.settings import settings
from services.cost_tracker import cost_tracker
from typing import Dict, Any, Optional, List, Union
import json
from datetime import datetime, timedelta
import os
import tempfile
import logging
from enum import Enum
from collections import deque, defaultdict
import hashlib
import mimetypes
from urllib.parse import urlparse
import base64

logger = logging.getLogger(__name__)

# ==========================================
# ENUMS & CONSTANTS
# ==========================================

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    LOCATION = "location"
    CONTACT = "contact"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"

class InteractiveType(str, Enum):
    BUTTON = "button"
    LIST = "list"
    PRODUCT = "product"
    PRODUCT_LIST = "product_list"

class DeliveryStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"

# ==========================================
# MESSAGE QUEUE FOR BULK SENDING
# ==========================================

class MessageQueue:
    """Asynchronous message queue with priority"""
    
    def __init__(self, max_concurrent: int = 5):
        self._queue: deque = deque()
        self._processing = False
        self._max_concurrent = max_concurrent
        self._stats = {
            "queued": 0,
            "sent": 0,
            "failed": 0
        }
    
    def add(self, message: Dict, priority: int = 5):
        """Add message to queue (priority 1-10, 10 = highest)"""
        self._queue.append({
            "message": message,
            "priority": priority,
            "queued_at": datetime.now(),
            "retries": 0
        })
        self._stats["queued"] += 1
    
    async def process(self, send_function):
        """Process queue with concurrent sending"""
        if self._processing:
            return
        
        self._processing = True
        
        while self._queue:
            # Sort by priority
            sorted_queue = sorted(
                self._queue, 
                key=lambda x: x["priority"], 
                reverse=True
            )
            self._queue = deque(sorted_queue)
            
            # Process batch
            batch = []
            for _ in range(min(self._max_concurrent, len(self._queue))):
                if self._queue:
                    batch.append(self._queue.popleft())
            
            # Send concurrently
            tasks = [send_function(**item["message"]) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Track results
            for result, item in zip(results, batch):
                if isinstance(result, Exception):
                    self._stats["failed"] += 1
                    logger.error(f"Queue send failed: {result}")
                    
                    # Retry logic
                    if item["retries"] < 3:
                        item["retries"] += 1
                        self._queue.append(item)
                else:
                    self._stats["sent"] += 1
            
            await asyncio.sleep(1)  # Rate limiting
        
        self._processing = False
    
    def get_stats(self) -> Dict:
        return self._stats.copy()

# ==========================================
# DELIVERY TRACKING
# ==========================================

class DeliveryTracker:
    """Track message delivery status"""
    
    def __init__(self, max_history: int = 10000):
        self._status_map: Dict[str, Dict] = {}
        self._max_history = max_history
        self._delivery_times: deque = deque(maxlen=1000)
    
    def track(self, message_id: str, to: str, status: DeliveryStatus):
        """Track message status"""
        if message_id not in self._status_map:
            self._status_map[message_id] = {
                "to": to,
                "created_at": datetime.now(),
                "status_history": []
            }
        
        self._status_map[message_id]["status_history"].append({
            "status": status.value,
            "timestamp": datetime.now()
        })
        
        # Calculate delivery time for delivered messages
        if status == DeliveryStatus.DELIVERED:
            created = self._status_map[message_id]["created_at"]
            delivery_time = (datetime.now() - created).total_seconds()
            self._delivery_times.append(delivery_time)
        
        # Cleanup old entries
        if len(self._status_map) > self._max_history:
            oldest_keys = sorted(
                self._status_map.keys(),
                key=lambda k: self._status_map[k]["created_at"]
            )[:100]
            for key in oldest_keys:
                del self._status_map[key]
    
    def get_status(self, message_id: str) -> Optional[Dict]:
        """Get message status"""
        return self._status_map.get(message_id)
    
    def get_average_delivery_time(self) -> float:
        """Get average delivery time in seconds"""
        if not self._delivery_times:
            return 0.0
        return sum(self._delivery_times) / len(self._delivery_times)

# ==========================================
# MAIN GALLABOX SERVICE
# ==========================================

class GallaboxService:
    """
    🚀 Advanced Gallabox WhatsApp Integration
    
    Features:
    - All message types (text, media, templates, interactive)
    - Rate limiting & circuit breaker
    - Retry logic with exponential backoff
    - Message queue for bulk sending
    - Delivery tracking
    - Media upload to S3
    - Template management
    - Real estate specific helpers
    """
    
    def __init__(self):
        self.api_url = settings.GALLABOX_API_URL
        self.api_key = settings.GALLABOX_API_KEY
        self.api_secret = settings.GALLABOX_API_SECRET
        self.channel_id = settings.GALLABOX_CHANNEL_ID
        
        # Headers
        self.headers = {
            "apiKey": self.api_key,
            "apiSecret": self.api_secret,
            "Content-Type": "application/json"
        }
        
        # Circuit breaker
        self._failure_count = 0
        self._circuit_open = False
        self._last_failure_time = None
        self._max_failures = 5
        self._circuit_timeout = 60
        
        # Rate limiting (per user)
        self._user_message_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self._rate_limit_window = 60  # seconds
        self._rate_limit_max = 10  # messages per window
        
        # Global rate limiting
        self._global_message_times: deque = deque(maxlen=100)
        self._global_rate_limit = 50  # messages per minute
        
        # Retry configuration
        self._max_retries = 3
        self._retry_delay_base = 2
        
        # Message queue
        self._message_queue = MessageQueue(max_concurrent=5)
        
        # Delivery tracking
        self._delivery_tracker = DeliveryTracker()
        
        # Template cache
        self._template_cache: Dict[str, Dict] = {}
        
        # HTTP client pool
        self._client_timeout = httpx.Timeout(30.0, connect=10.0)
        self._limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        
        # Supported media types
        self._supported_media = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "video": [".mp4", ".3gp", ".mov"],
            "audio": [".mp3", ".ogg", ".aac", ".m4a", ".amr"]
        }
        
        logger.info(f"🚀 Advanced Gallabox service initialized")
    
    # ==========================================
    # CIRCUIT BREAKER & RATE LIMITING
    # ==========================================
    
    def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker status"""
        if not self._circuit_open:
            return True
        
        if self._last_failure_time:
            elapsed = (datetime.now() - self._last_failure_time).seconds
            if elapsed > self._circuit_timeout:
                self._circuit_open = False
                self._failure_count = 0
                logger.info("✅ Circuit breaker reset")
                return True
        
        logger.warning("⚠️ Circuit breaker is OPEN - blocking request")
        return False
    
    def _record_failure(self):
        """Record API failure"""
        self._failure_count += 1
        if self._failure_count >= self._max_failures:
            self._circuit_open = True
            self._last_failure_time = datetime.now()
            logger.error(f"🔴 Circuit breaker OPENED after {self._failure_count} failures")
    
    def _record_success(self):
        """Record successful API call"""
        if self._failure_count > 0:
            self._failure_count = max(0, self._failure_count - 1)
    
    def _check_user_rate_limit(self, phone: str) -> bool:
        """Check per-user rate limit"""
        now = datetime.now().timestamp()
        
        # Remove old timestamps
        user_times = self._user_message_times[phone]
        while user_times and now - user_times[0] > self._rate_limit_window:
            user_times.popleft()
        
        # Check limit
        if len(user_times) >= self._rate_limit_max:
            logger.warning(f"⚠️ Rate limit exceeded for {phone}")
            return False
        
        # Add current timestamp
        user_times.append(now)
        return True
    
    def _check_global_rate_limit(self) -> bool:
        """Check global rate limit"""
        now = datetime.now().timestamp()
        
        # Remove old timestamps
        while self._global_message_times and now - self._global_message_times[0] > 60:
            self._global_message_times.popleft()
        
        # Check limit
        if len(self._global_message_times) >= self._global_rate_limit:
            logger.warning("⚠️ Global rate limit exceeded")
            return False
        
        self._global_message_times.append(now)
        return True
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is hit"""
        if not self._check_global_rate_limit():
            wait_time = 60 - (datetime.now().timestamp() - self._global_message_times[0])
            if wait_time > 0:
                logger.info(f"⏳ Waiting {wait_time:.1f}s for rate limit reset")
                await asyncio.sleep(wait_time)
    
    # ==========================================
    # CORE API METHODS
    # ==========================================
    
    async def _make_api_call(
        self,
        endpoint: str,
        payload: Dict,
        retry_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Core API call with retry logic and error handling
        """
        if not self._check_circuit_breaker():
            return {
                "success": False,
                "error": "Service temporarily unavailable (circuit breaker open)"
            }
        
        retry_count = retry_count or self._max_retries
        
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(
                    timeout=self._client_timeout,
                    limits=self._limits
                ) as client:
                    
                    response = await client.post(
                        f"{self.api_url}{endpoint}",
                        headers=self.headers,
                        json=payload
                    )
                    
                    # Success (202 Accepted)
                    if response.status_code == 202:
                        self._record_success()
                        data = response.json()
                        
                        # Track delivery
                        if data.get("id"):
                            self._delivery_tracker.track(
                                data["id"],
                                payload.get("recipient", {}).get("phone", "unknown"),
                                DeliveryStatus.SENT
                            )
                        
                        return {
                            "success": True,
                            "data": data,
                            "message_id": data.get("id"),
                            "status": "sent"
                        }
                    
                    # Rate limiting (429)
                    elif response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"⚠️ Rate limited by API. Retry after {retry_after}s")
                        
                        if attempt < retry_count - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "Rate limit exceeded",
                                "retry_after": retry_after
                            }
                    
                    # Bad request (400)
                    elif response.status_code == 400:
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get("message", "Bad request")
                        logger.error(f"❌ Bad request: {error_msg}")
                        
                        return {
                            "success": False,
                            "error": f"Bad request: {error_msg}",
                            "details": error_data
                        }
                    
                    # Unauthorized (401)
                    elif response.status_code == 401:
                        logger.error("❌ Unauthorized - Check API credentials")
                        self._record_failure()
                        
                        return {
                            "success": False,
                            "error": "Unauthorized - Invalid API credentials"
                        }
                    
                    # Server errors (5xx)
                    elif 500 <= response.status_code < 600:
                        logger.error(f"❌ Server error: {response.status_code}")
                        
                        if attempt < retry_count - 1:
                            wait_time = self._retry_delay_base ** attempt
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            self._record_failure()
                            return {
                                "success": False,
                                "error": f"Server error: {response.status_code}"
                            }
                    
                    # Other errors
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"❌ API error: {error_msg}")
                        
                        if attempt < retry_count - 1:
                            await asyncio.sleep(self._retry_delay_base ** attempt)
                            continue
                        else:
                            self._record_failure()
                            return {
                                "success": False,
                                "error": error_msg
                            }
            
            except httpx.TimeoutException:
                logger.warning(f"⏱️ Request timeout (attempt {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    await asyncio.sleep(self._retry_delay_base ** attempt)
                    continue
                else:
                    self._record_failure()
                    return {
                        "success": False,
                        "error": "Request timeout"
                    }
            
            except httpx.ConnectError as e:
                logger.error(f"🔌 Connection error: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(self._retry_delay_base ** attempt)
                    continue
                else:
                    self._record_failure()
                    return {
                        "success": False,
                        "error": f"Connection error: {str(e)}"
                    }
            
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(self._retry_delay_base ** attempt)
                    continue
                else:
                    self._record_failure()
                    return {
                        "success": False,
                        "error": f"Unexpected error: {str(e)}"
                    }
        
        return {
            "success": False,
            "error": "Max retries exceeded"
        }
    
    # ==========================================
    # TEXT MESSAGES
    # ==========================================
    
    async def send_text_message(
        self,
        to: str,
        message: str,
        preview_url: bool = True,
        queue: bool = False
    ) -> Dict[str, Any]:
        """
        Send text message
        
        Args:
            to: Phone number with country code (+971501234567)
            message: Text content
            preview_url: Enable URL preview
            queue: Add to queue instead of sending immediately
        """
        # Rate limit check
        if not self._check_user_rate_limit(to):
            return {
                "success": False,
                "error": "Rate limit exceeded for this user"
            }
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {
                "name": "User",
                "phone": to
            },
            "whatsapp": {
                "type": "text",
                "text": {
                    "body": message,
                    "previewUrl": preview_url
                }
            }
        }
        
        # Queue or send immediately
        if queue:
            self._message_queue.add({"to": to, "message": message})
            return {
                "success": True,
                "queued": True,
                "message": "Message added to queue"
            }
        
        # Send
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        # Track cost
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"✅ Text sent to {to}: {message[:50]}...")
        
        return result
    
    # ==========================================
    # MEDIA MESSAGES
    # ==========================================
    
    async def send_image_message(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send image message"""
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "image",
                "image": {
                    "link": image_url,
                    "caption": caption or ""
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("media", to)
            logger.info(f"🖼️ Image sent to {to}")
        
        return result
    
    async def send_document_message(
        self,
        to: str,
        document_url: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send document message"""
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "document",
                "document": {
                    "link": document_url,
                    "filename": filename or "document.pdf",
                    "caption": caption or ""
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("media", to)
            logger.info(f"📄 Document sent to {to}: {filename}")
        
        return result
    
    async def send_video_message(
        self,
        to: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send video message"""
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "video",
                "video": {
                    "link": video_url,
                    "caption": caption or ""
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("media", to)
            logger.info(f"🎥 Video sent to {to}")
        
        return result
    
    async def send_audio_message(
        self,
        to: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """Send audio message"""
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "audio",
                "audio": {
                    "link": audio_url
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("media", to)
            logger.info(f"🎵 Audio sent to {to}")
        
        return result
    
    # ==========================================
    # LOCATION & CONTACT
    # ==========================================
    
    async def send_location_message(
        self,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send location message
        Perfect for property locations!
        """
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "location",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name or "Location",
                    "address": address or ""
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"📍 Location sent to {to}: {name or 'Unnamed'}")
        
        return result
    
    async def send_contact_message(
        self,
        to: str,
        contact_name: str,
        contact_phone: str,
        organization: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send contact card"""
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "contact",
                "contact": {
                    "name": {
                        "formatted_name": contact_name,
                        "first_name": contact_name.split()[0] if contact_name else ""
                    },
                    "phones": [{
                        "phone": contact_phone,
                        "type": "WORK"
                    }],
                    "org": {
                        "company": organization or settings.COMPANY_NAME
                    }
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"👤 Contact sent to {to}: {contact_name}")
        
        return result
    
    # ==========================================
    # INTERACTIVE MESSAGES
    # ==========================================
    
    async def send_button_message(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive button message
        
        Args:
            buttons: List of dicts with 'id' and 'title'
                     Max 3 buttons, title max 20 chars
        
        Example:
            buttons = [
                {"id": "btn_1", "title": "Yes"},
                {"id": "btn_2", "title": "No"},
                {"id": "btn_3", "title": "Maybe"}
            ]
        """
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        if len(buttons) > 3:
            return {"success": False, "error": "Max 3 buttons allowed"}
        
        await self._wait_for_rate_limit()
        
        # Format buttons
        formatted_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"][:20]  # Max 20 chars
                }
            }
            for btn in buttons
        ]
        
        interactive_content = {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": formatted_buttons
            }
        }
        
        if header_text:
            interactive_content["header"] = {
                "type": "text",
                "text": header_text
            }
        
        if footer_text:
            interactive_content["footer"] = {
                "text": footer_text
            }
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "interactive",
                "interactive": interactive_content
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"🔘 Button message sent to {to}")
        
        return result
    
    async def send_list_message(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive list message
        
        Args:
            sections: List of sections, each with 'title' and 'rows'
                      rows = [{"id": "...", "title": "...", "description": "..."}]
        
        Example:
            sections = [{
                "title": "Choose a team",
                "rows": [
                    {"id": "team_1", "title": "Salesforce Team", "description": "CRM issues"},
                    {"id": "team_2", "title": "Dev Team", "description": "Technical bugs"}
                ]
            }]
        """
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        interactive_content = {
            "type": "list",
            "body": {
                "text": body_text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
        
        if header_text:
            interactive_content["header"] = {
                "type": "text",
                "text": header_text
            }
        
        if footer_text:
            interactive_content["footer"] = {
                "text": footer_text
            }
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "interactive",
                "interactive": interactive_content
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"📋 List message sent to {to}")
        
        return result
    
    # ==========================================
    # TEMPLATE MESSAGES
    # ==========================================
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        header_params: Optional[List[str]] = None,
        body_params: Optional[List[str]] = None,
        button_params: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp template message
        
        Templates must be pre-approved in WhatsApp Business Manager
        
        Args:
            template_name: Name of approved template
            language_code: Language (en, ar, etc.)
            header_params: Dynamic values for header
            body_params: Dynamic values for body
            button_params: Dynamic values for buttons
        """
        
        if not self._check_user_rate_limit(to):
            return {"success": False, "error": "Rate limit exceeded"}
        
        await self._wait_for_rate_limit()
        
        # Build template components
        components = []
        
        # Header
        if header_params:
            components.append({
                "type": "header",
                "parameters": [
                    {"type": "text", "text": param}
                    for param in header_params
                ]
            })
        
        # Body
        if body_params:
            components.append({
                "type": "body",
                "parameters": [
                    {"type": "text", "text": param}
                    for param in body_params
                ]
            })
        
        # Buttons
        if button_params:
            components.append({
                "type": "button",
                "sub_type": "url",
                "index": 0,
                "parameters": [
                    {"type": "text", "text": param}
                    for param in button_params
                ]
            })
        
        payload = {
            "channelId": self.channel_id,
            "channelType": "whatsapp",
            "recipient": {"name": "User", "phone": to},
            "whatsapp": {
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    },
                    "components": components
                }
            }
        }
        
        result = await self._make_api_call("/devapi/messages/whatsapp", payload)
        
        if result.get("success"):
            cost_tracker.track_gallabox_usage("text", to)
            logger.info(f"📋 Template '{template_name}' sent to {to}")
        
        return result
    
    # ==========================================
    # REAL ESTATE SPECIFIC HELPERS
    # ==========================================
    
    async def send_property_details(
        self,
        to: str,
        property_data: Dict
    ) -> Dict[str, Any]:
        """
        Send property details with image
        
        property_data = {
            "name": "Luxury Penthouse",
            "location": "Palm Jumeirah",
            "price": "25,000,000 AED",
            "bedrooms": 5,
            "bathrooms": 6,
            "size_sqft": 12000,
            "image_url": "https://...",
            "brochure_url": "https://..."
        }
        """
        
        message = f"""🏠 **{property_data['name']}**

📍 Location: {property_data['location']}
💰 Price: {property_data['price']}
🛏️ Bedrooms: {property_data['bedrooms']}
🚿 Bathrooms: {property_data['bathrooms']}
📐 Size: {property_data['size_sqft']:,} sq ft

Would you like to schedule a viewing?"""
        
        # Send image with caption
        if property_data.get("image_url"):
            result = await self.send_image_message(
                to=to,
                image_url=property_data["image_url"],
                caption=message
            )
        else:
            result = await self.send_text_message(to, message)
        
        # Send brochure if available
        if result.get("success") and property_data.get("brochure_url"):
            await asyncio.sleep(1)  # Small delay
            await self.send_document_message(
                to=to,
                document_url=property_data["brochure_url"],
                filename=f"{property_data['name']} - Brochure.pdf",
                caption="📄 Property Brochure"
            )
        
        return result
    
    async def send_viewing_confirmation(
        self,
        to: str,
        viewing_data: Dict
    ) -> Dict[str, Any]:
        """
        Send viewing appointment confirmation
        
        viewing_data = {
            "property_name": "...",
            "date": "2025-02-15",
            "time": "14:00",
            "agent_name": "John Doe",
            "agent_phone": "+971...",
            "location": {"lat": 25.0, "lng": 55.0},
            "address": "..."
        }
        """
        
        message = f"""✅ **Viewing Confirmed**

🏠 Property: {viewing_data['property_name']}
📅 Date: {viewing_data['date']}
⏰ Time: {viewing_data['time']}

👤 Agent: {viewing_data['agent_name']}
📞 Contact: {viewing_data['agent_phone']}

We look forward to showing you this property!"""
        
        # Send confirmation message
        result = await self.send_text_message(to, message)
        
        # Send location if available
        if result.get("success") and viewing_data.get("location"):
            await asyncio.sleep(1)
            await self.send_location_message(
                to=to,
                latitude=viewing_data["location"]["lat"],
                longitude=viewing_data["location"]["lng"],
                name=viewing_data["property_name"],
                address=viewing_data.get("address", "")
            )
        
        return result
    
    async def send_contract_documents(
        self,
        to: str,
        contract_data: Dict
    ) -> Dict[str, Any]:
        """
        Send contract documents for signing
        
        contract_data = {
            "property": "...",
            "contract_url": "https://...",
            "terms_url": "https://...",
            "buyer_name": "..."
        }
        """
        
        message = f"""📄 **Contract Ready for Review**

Dear {contract_data['buyer_name']},

Your purchase contract for **{contract_data['property']}** is ready.

Please review the documents attached and let us know if you have any questions.

{settings.COMPANY_NAME}"""
        
        # Send message
        result = await self.send_text_message(to, message)
        
        if result.get("success"):
            # Send contract
            await asyncio.sleep(1)
            await self.send_document_message(
                to=to,
                document_url=contract_data["contract_url"],
                filename="Purchase_Contract.pdf",
                caption="📝 Purchase Contract"
            )
            
            # Send terms if available
            if contract_data.get("terms_url"):
                await asyncio.sleep(1)
                await self.send_document_message(
                    to=to,
                    document_url=contract_data["terms_url"],
                    filename="Terms_and_Conditions.pdf",
                    caption="📋 Terms & Conditions"
                )
        
        return result
    
    # ==========================================
    # MEDIA DOWNLOAD
    # ==========================================
    
    async def download_media(
        self,
        media_url: str,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Download media from WhatsApp/Gallabox
        
        Returns path to downloaded file
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    media_url,
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Media download failed: HTTP {response.status_code}")
                    return None
                
                # Determine file extension
                content_type = response.headers.get("content-type", "")
                ext = self._get_extension_from_mime(content_type)
                
                # Create temp file if no path provided
                if not save_path:
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=ext
                    )
                    save_path = temp_file.name
                    temp_file.close()
                
                # Save file
                with open(save_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"📥 Media downloaded: {save_path} ({len(response.content)} bytes)")
                return save_path
        
        except Exception as e:
            logger.error(f"❌ Media download error: {e}")
            return None
    
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.ms-excel": ".xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "video/mp4": ".mp4",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg"
        }
        return mime_map.get(mime_type, ".bin")
    
    # ==========================================
    # BULK MESSAGING
    # ==========================================
    
    async def send_broadcast(
        self,
        recipients: List[str],
        message: str,
        delay_seconds: int = 2
    ) -> Dict[str, Any]:
        """
        Send broadcast message to multiple recipients
        
        Args:
            recipients: List of phone numbers
            message: Message text
            delay_seconds: Delay between messages to avoid rate limit
        """
        
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for phone in recipients:
            result = await self.send_text_message(phone, message)
            
            if result.get("success"):
                results["sent"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "phone": phone,
                "success": result.get("success"),
                "error": result.get("error")
            })
            
            # Delay to respect rate limits
            await asyncio.sleep(delay_seconds)
        
        logger.info(f"📢 Broadcast complete: {results['sent']}/{results['total']} sent")
        
        return results
    
    # ==========================================
    # UTILITY & MONITORING
    # ==========================================
    
    def get_rate_limit_stats(self) -> Dict:
        """Get rate limiting statistics"""
        return {
            "circuit_breaker": {
                "open": self._circuit_open,
                "failure_count": self._failure_count,
                "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None
            },
            "rate_limits": {
                "tracked_users": len(self._user_message_times),
                "global_messages_last_minute": len(self._global_message_times)
            },
            "message_queue": self._message_queue.get_stats(),
            "delivery": {
                "average_delivery_time_seconds": round(self._delivery_tracker.get_average_delivery_time(), 2)
            }
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker (admin function)"""
        self._circuit_open = False
        self._failure_count = 0
        self._last_failure_time = None
        logger.info("✅ Circuit breaker manually reset")
    
    async def process_message_queue(self):
        """Process pending messages in queue"""
        await self._message_queue.process(self.send_text_message)
    
    def get_delivery_status(self, message_id: str) -> Optional[Dict]:
        """Get delivery status for a message"""
        return self._delivery_tracker.get_status(message_id)


# ==========================================
    # 🧪 MOCK COMPATIBILITY METHODS (ADD THESE AT END OF CLASS)
    # ==========================================
    
    def get_messages_for_user(self, phone: str) -> List[Dict]:
        """Mock compatibility - not supported in real mode"""
        logger.warning(f"⚠️ get_messages_for_user() called in REAL mode (not supported)")
        return []
    
    def get_all_messages(self) -> List[Dict]:
        """Mock compatibility - not supported in real mode"""
        logger.warning(f"⚠️ get_all_messages() called in REAL mode (not supported)")
        return []
    
    def clear_messages(self):
        """Mock compatibility - no-op in real mode"""
        logger.warning(f"⚠️ clear_messages() called in REAL mode (no-op)")
    
    def enable_failure_simulation(self, rate: float = 0.1):
        """Mock compatibility - no-op in real mode"""
        logger.warning(f"⚠️ enable_failure_simulation() called in REAL mode (no-op)")
    
    def disable_failure_simulation(self):
        """Mock compatibility - no-op in real mode"""
        logger.warning(f"⚠️ disable_failure_simulation() called in REAL mode (no-op)")
    
    def get_stats(self) -> Dict:
        """Get service stats"""
        return {
            "mock_mode": False,
            "service": "real_gallabox",
            "rate_limit_stats": self.get_rate_limit_stats()
        }

# ==========================================
# GLOBAL INSTANCE
# ==========================================

gallabox_service = GallaboxService()