"""
Advanced Intent Processing Service - HOTFIXED VERSION
All critical bugs fixed
"""

from models.schemas import (
    IntentType, IntentClassification, Priority, 
    PendingTicket, TicketPreview
)
from services.openai_service import openai_service
from services.team_detection import team_detection_service
from services.project_matcher import project_matcher_service
from services.jira_service import jira_service
from services.response_service import response_service
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import re

from config.settings import settings
from services import gallabox_service

# Enhanced imports
from services.property_intelligence import property_intelligence_service, PropertyRequirements
from services.lead_qualifier import lead_qualifier, LeadType
from services.conversation_memory import conversation_memory, ConversationState, MessageRole
from services.multilingual import multilingual_service, Language
from services.smart_routing import smart_routing
from services.sentiment_service import sentiment_analyzer
from services.vip_detection import vip_detection_service

print(f"🎯 Intent service loaded gallabox: {type(gallabox_service).__name__}")


class IntentService:
    def __init__(self):
        # Legacy context storage
        self._conversation_context: Dict[str, List] = {}
        self._context_max_age_minutes = 30
        
        # ==========================================
        # FIXED: More specific technical keywords
        # ==========================================
        self._technical_keywords = {
            "report", "dashboard", "data", "analytics", "kpi", "metric",
            "ai report", "campaign report", "marketing report", "analysis",
            "salesforce", "crm", "system", "ticket", "support", "issue",
            "error", "bug", "not working", "down", "sync", "login",
            "password", "access", "permission", "laptop", "keyboard",
            "website", "api", "database", "server", "deployment"
        }
        
        # Real estate keywords (for actual property queries)
        self._real_estate_keywords = {
            "villa", "apartment", "penthouse", "property", "bedroom",
            "buy", "sell", "rent", "lease", "viewing", "purchase"
        }
    
    async def process_message(
        self, 
        user_phone: str,
        user_name: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        🔥 FIXED: Main message processing
        """
        
        print(f"\n{'='*70}")
        print(f"🔄 PROCESSING MESSAGE FROM {user_name}")
        print(f"{'='*70}")
        print(f"📱 Phone: {user_phone}")
        print(f"💬 Message: {message_text[:100]}...")
        
        # ==========================================
        # 1. DETECT LANGUAGE
        # ==========================================
        detected_language, lang_confidence = multilingual_service.detect_language(message_text)
        print(f"🌍 Language: {detected_language.value} (confidence: {lang_confidence:.2f})")
        
        # Translate to English if Arabic
        original_message = message_text
        if detected_language == Language.ARABIC:
            translation_result = await multilingual_service.translate(
                message_text,
                target_language=Language.ENGLISH,
                user_phone=user_phone,
                context="customer inquiry"
            )
            message_text = translation_result.translated_text
            print(f"🔄 Translated to English: {message_text[:80]}...")
        
        # ==========================================
        # 2. GET/CREATE SESSION
        # ==========================================
        session = conversation_memory.get_or_create_session(user_phone, user_name)
        print(f"💾 Session: {session.conversation_id} | State: {session.state.value}")
        
        conversation_memory.update_preference(
            user_phone,
            "preferred_language",
            detected_language.value
        )
        
        conversation_memory.add_message(
            user_phone,
            MessageRole.USER,
            original_message,
            metadata={"translated": message_text if detected_language == Language.ARABIC else None}
        )
        
        # ==========================================
        # 3. SENTIMENT ANALYSIS
        # ==========================================
        sentiment_result = sentiment_analyzer.analyze_sentiment(message_text, user_phone)
        print(f"😊 Sentiment: {sentiment_result['sentiment']} | Urgency: {sentiment_result['urgency']}/10")
        
        if sentiment_result.get('escalate'):
            print(f"🚨 ESCALATION TRIGGERED: {sentiment_result.get('reason')}")
        
        # ==========================================
        # 4. VIP DETECTION
        # ==========================================
        vip_result = vip_detection_service.detect_vip(message_text, user_phone, user_name)
        is_vip = vip_result['is_vip']
        
        if is_vip:
            print(f"👑 VIP DETECTED: Tier {vip_result['vip_tier']} | Confidence: {vip_result['confidence']:.2f}")
            conversation_memory.set_vip_status(user_phone, True, vip_result['vip_tier'])
        
        response_service.update_user_stats(
            user_phone,
            action="message",
            message=message_text
        )
        
        # ==========================================
        # 5. CHECK PENDING TICKET CONFIRMATION
        # ==========================================
        pending = response_service.get_pending_ticket(user_phone)
        
        if pending and pending.awaiting_confirmation:
            print("📋 User has pending ticket awaiting confirmation")
            result = await self._handle_confirmation(
                user_phone, user_name, message_text, pending, detected_language
            )
            
            # ==========================================
            # FIXED: Check if new issue detected
            # ==========================================
            if result.get("action") == "new_issue_detected":
                print("🔄 New issue detected, reprocessing...")
                # Don't return, continue processing as new message
                pass
            else:
                return result
        
        # ==========================================
        # 6. CHECK IF TECHNICAL SUPPORT QUERY
        # ==========================================
        if self._is_technical_query(message_text):
            print("🎫 TECHNICAL SUPPORT QUERY DETECTED")
            
            # Process as ticket creation
            return await self._handle_create_ticket(
                user_phone, user_name, message_text, None, detected_language
            )
        
        # ==========================================
        # 7. CHECK IF REAL ESTATE QUERY
        # ==========================================
        if self._is_real_estate_query(message_text):
            print("🏠 REAL ESTATE QUERY DETECTED - Redirecting")
            
            response = await multilingual_service.get_smart_response(
                "property_redirect",
                original_message,
                user_phone,
                name=user_name,
                email=settings.WHATSAPP_BUSINESS_EMAIL,
                website=settings.WHATSAPP_BUSINESS_WEBSITE
            )
            
            await gallabox_service.send_text_message(user_phone, response)
            
            conversation_memory.add_message(
                user_phone,
                MessageRole.AGENT,
                response,
                intent="property_redirect"
            )
            
            return {
                "intent": "property_inquiry",
                "action": "redirected_to_sales",
                "response_sent": True
            }
        
        # ==========================================
        # 8. CLASSIFY INTENT WITH AI
        # ==========================================
        conversation_history = conversation_memory.get_recent_context(user_phone, messages=5)
        
        intent_result = await openai_service.classify_intent(
            message=message_text,
            user_name=user_name,
            user_phone=user_phone,
            conversation_history=conversation_history
        )
        
        print(f"🎯 Intent: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
        
        conversation_memory.add_topic(user_phone, intent_result.intent.value)
        
        # ==========================================
        # 9. ROUTE BASED ON INTENT
        # ==========================================
        response = await self._route_intent(
            user_phone=user_phone,
            user_name=user_name,
            message_text=message_text,
            intent_result=intent_result,
            detected_language=detected_language
        )
        
        self._update_context(
            user_phone, 
            message_text, 
            intent_result.intent.value,
            intent_result.confidence
        )
        
        print(f"✅ Message processing complete")
        print(f"{'='*70}\n")
        
        return response
    
    # ==========================================
    # FIXED: TECHNICAL QUERY DETECTION
    # ==========================================
    
    def _is_technical_query(self, message: str) -> bool:
        """
        🔥 FIXED: Detect if this is a technical support query
        
        Returns True if:
        - Has technical keywords (salesforce, dashboard, laptop, etc.)
        - Describes a problem/issue
        - NOT a property inquiry
        """
        message_lower = message.lower()
        
        # Count technical keywords
        technical_count = sum(
            1 for keyword in self._technical_keywords
            if keyword in message_lower
        )
        
        # Problem indicators
        problem_indicators = [
            "issue", "problem", "error", "not working", "broken",
            "down", "failed", "can't", "unable", "wrong",
            "need help", "need support", "not loading", "stuck"
        ]
        
        has_problem = any(indicator in message_lower for indicator in problem_indicators)
        
        # Technical patterns
        technical_patterns = [
            r"(?:salesforce|crm|dashboard).*(?:not|issue|error|problem)",
            r"(?:laptop|keyboard|computer).*(?:not working|broken|issue)",
            r"(?:login|password|access).*(?:issue|problem|expired|denied)",
            r"(?:report|data|dashboard).*(?:wrong|incorrect|missing|error)",
            r"(?:website|api|system).*(?:down|not loading|error|crashed)"
        ]
        
        matches_pattern = any(re.search(p, message_lower) for p in technical_patterns)
        
        # Decision logic
        is_technical = (
            technical_count >= 2 or  # Multiple technical keywords
            (technical_count >= 1 and has_problem) or  # Technical keyword + problem
            matches_pattern  # Matches technical problem pattern
        )
        
        if is_technical:
            print(f"   ✅ Technical query detected (keywords: {technical_count}, problem: {has_problem})")
        
        return is_technical
    
    # ==========================================
    # FIXED: REAL ESTATE QUERY DETECTION
    # ==========================================
    
    def _is_real_estate_query(self, message: str) -> bool:
        """
        🔥 FIXED: Real estate query detection
        
        Only returns True for ACTUAL property inquiries like:
        - "I want to buy a 3-bedroom villa"
        - "Show me apartments in Dubai Marina"
        
        Returns False for:
        - "I need AI report for campaign" (even if campaign has location name)
        - "Dashboard for four seasons" (technical, not property)
        """
        message_lower = message.lower()
        
        # ==========================================
        # EXCLUDE if technical keywords present
        # ==========================================
        if any(keyword in message_lower for keyword in self._technical_keywords):
            print(f"   ❌ Has technical keywords - NOT real estate query")
            return False
        
        # ==========================================
        # ONLY include if EXPLICIT property intent
        # ==========================================
        
        # Property transaction keywords
        property_actions = ["buy", "purchase", "rent", "lease", "sell", "looking for", "want", "need", "show me"]
        property_types = ["villa", "apartment", "penthouse", "townhouse", "property", "flat"]
        
        # Check for "ACTION + PROPERTY TYPE" pattern
        property_patterns = [
            r'(?:buy|purchase|looking for|want|need|show me)\s+(?:a|an)?\s*(?:\d+)?\s*(?:bedroom|bed|br)?\s*(?:villa|apartment|property|penthouse)',
            r'(?:buy|rent|lease)\s+property',
            r'(?:villa|apartment|property).*(?:for sale|for rent|available)',
            r'view(?:ing)?\s+(?:a|the)?\s*property',
            r'(?:2|3|4|5)\s*(?:bed|bedroom|br)\s+(?:villa|apartment)',
            r'budget.*(?:villa|apartment|property)'
        ]
        
        matches_property_pattern = any(re.search(p, message_lower) for p in property_patterns)
        
        # Count pure property keywords (excluding technical context)
        property_keyword_count = sum(
            1 for keyword in self._real_estate_keywords
            if keyword in message_lower
        )
        
        # Decision
        is_property_query = (
            matches_property_pattern or  # Clear property transaction pattern
            property_keyword_count >= 3   # Multiple property-specific keywords
        )
        
        if is_property_query:
            print(f"   🏠 Real estate query detected")
        else:
            print(f"   ❌ NOT a real estate query")
        
        return is_property_query
    
    # ==========================================
    # ROUTE HANDLERS
    # ==========================================
    
    async def _route_intent(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Route message to appropriate handler"""
        
        handlers = {
            IntentType.CREATE_TICKET: self._handle_create_ticket,
            IntentType.CHECK_STATUS: self._handle_check_status,
            IntentType.UPDATE_TICKET: self._handle_update_ticket,
            IntentType.CLOSE_TICKET: self._handle_close_ticket,
            IntentType.PROPERTY_INQUIRY: self._handle_property_inquiry,
            IntentType.SCHEDULE_VIEWING: self._handle_schedule_viewing,
            IntentType.GENERAL_INQUIRY: self._handle_general_inquiry
        }
        
        handler = handlers.get(intent_result.intent)
        
        if handler:
            return await handler(
                user_phone, user_name, message_text, intent_result, detected_language
            )
        else:
            return await self._handle_general_inquiry(
                user_phone, user_name, message_text, intent_result, detected_language
            )
    
    async def _handle_create_ticket(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: Optional[IntentClassification],
        detected_language: Language
    ) -> Dict[str, Any]:
        """
        🔥 FIXED: Create support ticket with preview
        """
        
        print("🎫 Creating support ticket...")
        
        conversation_memory.update_state(user_phone, ConversationState.SUPPORT_TICKET)
        
        # Detect team from message
        team_name, team_confidence = team_detection_service.detect_team(message_text)
        print(f"🔍 Team detected: {team_name} (confidence: {team_confidence:.2f})")
        
        # Always use default project
        project_key = settings.JIRA_PROJECT_KEY
        
        # Get project name
        try:
            projects = await jira_service.get_all_projects()
            project = next((p for p in projects if p.key == project_key), None)
            project_name = project.name if project else project_key
        except:
            project_name = project_key
        
        # Generate summary and description
        summary = await openai_service.generate_ticket_summary(
            message_text, user_name, team_name, user_phone
        )
        
        description = await openai_service.generate_ticket_description(
            message_text, user_name, user_phone
        )
        
        # Determine priority
        priority = Priority.MEDIUM
        if intent_result and intent_result.priority:
            priority = intent_result.priority
        
        # Check sentiment for priority escalation
        session = conversation_memory.get_or_create_session(user_phone, user_name)
        if session.is_vip:
            priority = Priority.HIGH
            print("⚡ Priority escalated to HIGH (VIP)")
        
        # Create pending ticket
        pending_ticket = PendingTicket(
            user_phone=user_phone,
            user_name=user_name,
            summary=summary,
            description=description,
            team=team_name,
            project_key=project_key,
            priority=priority,
            awaiting_confirmation=True
        )
        
        # Store pending ticket
        response_service.store_pending_ticket(user_phone, pending_ticket)
        conversation_memory.set_pending_ticket(user_phone, f"PENDING_{project_key}")
        
        # Send confirmation message
        confirmation_message = await multilingual_service.get_smart_response(
            "confirm_ticket",
            message_text,
            user_phone,
            summary=summary,
            team=team_name,
            priority=priority.value
        )
        
        await gallabox_service.send_text_message(user_phone, confirmation_message)
        
        conversation_memory.add_message(
            user_phone,
            MessageRole.AGENT,
            confirmation_message,
            intent="ticket_preview"
        )
        
        return {
            "intent": "create_ticket",
            "action": "awaiting_confirmation",
            "response_sent": True,
            "ticket_preview": {
                "summary": summary,
                "team": team_name,
                "project_key": project_key,
                "priority": priority.value
            }
        }
    
    # ==========================================
    # FIXED: CONFIRMATION HANDLER
    # ==========================================
    
    async def _handle_confirmation(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        pending: PendingTicket,
        detected_language: Language
    ) -> Dict[str, Any]:
        """
        🔥 FIXED: Handle user confirmation or detect new issue
        """
        
        message_lower = message_text.lower().strip()
        
        # ==========================================
        # DETECT IF THIS IS A NEW ISSUE
        # ==========================================
        
        # Technical issue indicators
        new_issue_keywords = [
            "salesforce", "dashboard", "login", "password", "website",
            "laptop", "keyboard", "error", "not working", "down",
            "report", "data", "sync", "campaign", "urgent", "api",
            "crm", "system", "database", "server", "access"
        ]
        
        # Count issue keywords in message
        issue_keyword_count = sum(
            1 for keyword in new_issue_keywords
            if keyword in message_lower
        )
        
        # Confirmation keywords
        confirm_keywords = [
            'yes', 'confirm', 'create', 'ok', 'sure', 'proceed', 
            'correct', 'right', 'good', 'yeah', 'yep', 'y',
            'نعم', 'موافق', 'تمام'
        ]
        
        # Cancel keywords
        cancel_keywords = ['cancel', 'no', 'stop', 'لا', 'إلغاء']
        
        is_confirmation = any(word in message_lower for word in confirm_keywords)
        is_cancellation = any(word in message_lower for word in cancel_keywords)
        
        # ==========================================
        # IF NEW ISSUE DETECTED (NOT Yes/No/Cancel)
        # ==========================================
        if issue_keyword_count >= 2 and not is_confirmation and not is_cancellation:
            print(f"⚠️ NEW ISSUE DETECTED while pending ticket exists")
            print(f"   Issue keywords found: {issue_keyword_count}")
            print(f"   Clearing old pending ticket...")
            
            # Clear old pending ticket
            response_service.clear_pending_ticket(user_phone)
            
            # Send brief acknowledgment
            ack_msg = "Got it! Let me help with this new issue."
            if detected_language == Language.ARABIC:
                ack_msg = "حسناً! دعني أساعدك في هذه المشكلة الجديدة."
            
            await gallabox_service.send_text_message(user_phone, ack_msg)
            
            # Return flag to reprocess as new message
            return {
                "action": "new_issue_detected",
                "response_sent": True,
                "reprocess": True
            }
        
        # ==========================================
        # HANDLE CONFIRMATION
        # ==========================================
        if is_confirmation:
            print("✅ User confirmed ticket creation")
            
            # Create ticket in Jira
            result = await jira_service.create_ticket(
                summary=pending.summary,
                description=pending.description,
                project_key=pending.project_key,
                priority=pending.priority
            )
            
            if result['success']:
                conversation_memory.add_active_ticket(user_phone, result['ticket_key'])
                
                success_msg = await multilingual_service.get_smart_response(
                    "ticket_created",
                    message_text,
                    user_phone,
                    ticket_key=result['ticket_key'],
                    summary=result['summary']
                )
                
                await gallabox_service.send_text_message(user_phone, success_msg)
                
                conversation_memory.add_message(
                    user_phone,
                    MessageRole.AGENT,
                    success_msg,
                    intent="ticket_created"
                )
                
                response_service.update_user_stats(user_phone, action="ticket_created")
                response_service.clear_pending_ticket(user_phone)
                
                return {
                    "intent": "create_ticket",
                    "action": "created",
                    "ticket_key": result['ticket_key'],
                    "response_sent": True
                }
            else:
                error_msg = await multilingual_service.get_smart_response(
                    "error",
                    message_text,
                    user_phone
                )
                await gallabox_service.send_text_message(user_phone, error_msg)
                return {
                    "action": "failed",
                    "error": result.get('error')
                }
        
        # ==========================================
        # HANDLE CANCELLATION
        # ==========================================
        elif is_cancellation:
            response_service.clear_pending_ticket(user_phone)
            cancel_msg = "Ticket creation cancelled. How else can I help you?"
            
            if detected_language == Language.ARABIC:
                cancel_msg = "تم إلغاء إنشاء التذكرة. كيف يمكنني مساعدتك؟"
            
            await gallabox_service.send_text_message(user_phone, cancel_msg)
            return {
                "action": "cancelled",
                "response_sent": True
            }
        
        # ==========================================
        # HANDLE MODIFICATIONS
        # ==========================================
        else:
            print("🔄 User providing modification or additional info")
            
            # Update description with additional info
            pending.description += f"\n\n*Additional Information:*\n{message_text}"
            
            # Store updated ticket
            response_service.store_pending_ticket(user_phone, pending)
            
            # Send updated preview
            updated_msg = await multilingual_service.get_smart_response(
                "confirm_ticket",
                message_text,
                user_phone,
                summary=pending.summary,
                team=pending.team,
                priority=pending.priority.value
            )
            
            await gallabox_service.send_text_message(user_phone, updated_msg)
            
            return {
                "action": "updated_preview",
                "response_sent": True
            }
    
    # ==========================================
    # OTHER HANDLERS (Keep existing code)
    # ==========================================
    
    async def _handle_check_status(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Check ticket status"""
        
        ticket_key = intent_result.ticket_key
        
        if not ticket_key:
            match = re.search(r'\b([A-Z]{2,}-\d+)\b', message_text, re.IGNORECASE)
            if match:
                ticket_key = match.group(1).upper()
        
        if not ticket_key:
            tickets = await jira_service.search_tickets(user_phone, limit=5)
            
            if tickets:
                message = "📋 *Your Recent Tickets:*\n\n"
                for t in tickets:
                    status_emoji = "✅" if t['status'] in ['Done', 'Closed'] else "🔄"
                    message += f"{status_emoji} *{t['key']}*\n{t['summary']}\n_Status: {t['status']}_\n\n"
                
                message += "Reply with the ticket number (e.g., SUP-123) to see details."
                
                if detected_language == Language.ARABIC:
                    translation = await multilingual_service.translate(
                        message,
                        Language.ARABIC,
                        user_phone=user_phone
                    )
                    message = translation.translated_text
                
                await gallabox_service.send_text_message(user_phone, message)
            else:
                no_tickets_msg = "I couldn't find any tickets associated with your number."
                if detected_language == Language.ARABIC:
                    no_tickets_msg = "لم أجد أي تذاكر مرتبطة برقمك."
                
                await gallabox_service.send_text_message(user_phone, no_tickets_msg)
            
            return {
                "action": "requested_ticket_key",
                "response_sent": True
            }
        
        ticket_data = await jira_service.get_ticket_status(ticket_key)
        
        if ticket_data['success']:
            status_msg = await multilingual_service.get_smart_response(
                "ticket_status",
                message_text,
                user_phone,
                ticket_key=ticket_key,
                summary=ticket_data['summary'],
                status=ticket_data['status'],
                priority=ticket_data['priority'],
                assignee=ticket_data['assignee'],
                url=ticket_data['url']
            )
            
            await gallabox_service.send_text_message(user_phone, status_msg)
            
            return {
                "intent": "check_status",
                "action": "status_sent",
                "ticket_key": ticket_key,
                "response_sent": True
            }
        else:
            error_msg = f"❌ {ticket_data['error']}"
            await gallabox_service.send_text_message(user_phone, error_msg)
            return {
                "action": "ticket_not_found",
                "response_sent": True
            }
    
    async def _handle_update_ticket(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Update existing ticket"""
        
        ticket_key = intent_result.ticket_key
        
        if not ticket_key:
            match = re.search(r'\b([A-Z]{2,}-\d+)\b', message_text, re.IGNORECASE)
            if match:
                ticket_key = match.group(1).upper()
        
        if not ticket_key:
            msg = "Please provide the ticket number you'd like to update (e.g., SUP-123)."
            if detected_language == Language.ARABIC:
                msg = "يرجى تقديم رقم التذكرة التي ترغب في تحديثها (مثال: SUP-123)."
            
            await gallabox_service.send_text_message(user_phone, msg)
            return {
                "action": "requested_ticket_key",
                "response_sent": True
            }
        
        comment = f"*Comment from user via WhatsApp:*\n{message_text}\n\n_Added by: {user_name} ({user_phone})_"
        
        result = await jira_service.update_ticket(
            ticket_key=ticket_key,
            comment=comment,
            priority=intent_result.priority
        )
        
        if result['success']:
            success_msg = f"✅ Ticket *{ticket_key}* has been updated with your comment."
            if detected_language == Language.ARABIC:
                success_msg = f"✅ تم تحديث التذكرة *{ticket_key}* بتعليقك."
            
            await gallabox_service.send_text_message(user_phone, success_msg)
        else:
            await gallabox_service.send_text_message(
                user_phone,
                f"❌ Failed to update ticket: {result.get('error')}"
            )
        
        return {
            "intent": "update_ticket",
            "action": "updated" if result['success'] else "failed",
            "ticket_key": ticket_key,
            "response_sent": True
        }
    
    async def _handle_close_ticket(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Close/resolve ticket"""
        
        ticket_key = intent_result.ticket_key
        
        if not ticket_key:
            match = re.search(r'\b([A-Z]{2,}-\d+)\b', message_text, re.IGNORECASE)
            if match:
                ticket_key = match.group(1).upper()
        
        if not ticket_key:
            msg = "Which ticket would you like to close? Please provide the ticket number."
            if detected_language == Language.ARABIC:
                msg = "أي تذكرة ترغب في إغلاقها؟ يرجى تقديم رقم التذكرة."
            
            await gallabox_service.send_text_message(user_phone, msg)
            return {
                "action": "requested_ticket_key",
                "response_sent": True
            }
        
        result = await jira_service.close_ticket(ticket_key)
        
        if result['success']:
            success_msg = f"✅ Ticket *{ticket_key}* has been closed.\n\nThank you for confirming!"
            if detected_language == Language.ARABIC:
                success_msg = f"✅ تم إغلاق التذكرة *{ticket_key}*.\n\nشكراً لك على التأكيد!"
            
            await gallabox_service.send_text_message(user_phone, success_msg)
        else:
            await gallabox_service.send_text_message(
                user_phone,
                f"❌ Failed to close ticket: {result.get('error')}"
            )
        
        return {
            "intent": "close_ticket",
            "action": "closed" if result['success'] else "failed",
            "ticket_key": ticket_key,
            "response_sent": True
        }
    
    async def _handle_property_inquiry(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Handle property inquiry (redirect to sales)"""
        
        redirect_msg = await multilingual_service.get_smart_response(
            "property_redirect",
            message_text,
            user_phone,
            name=user_name,
            email=settings.WHATSAPP_BUSINESS_EMAIL,
            website=settings.WHATSAPP_BUSINESS_WEBSITE
        )
        
        await gallabox_service.send_text_message(user_phone, redirect_msg)
        
        return {
            "intent": "property_inquiry",
            "action": "redirected_to_sales",
            "response_sent": True
        }
    
    async def _handle_schedule_viewing(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """Handle viewing schedule request"""
        
        redirect_msg = await multilingual_service.get_smart_response(
            "property_redirect",
            message_text,
            user_phone,
            name=user_name,
            email=settings.WHATSAPP_BUSINESS_EMAIL,
            website=settings.WHATSAPP_BUSINESS_WEBSITE
        )
        
        await gallabox_service.send_text_message(user_phone, redirect_msg)
        
        return {
            "intent": "schedule_viewing",
            "action": "redirected_to_sales",
            "response_sent": True
        }
    
    async def _handle_general_inquiry(
        self,
        user_phone: str,
        user_name: str,
        message_text: str,
        intent_result: IntentClassification,
        detected_language: Language
    ) -> Dict[str, Any]:
        """
        🔥 FIXED: Simple greeting (no long text)
        """
        
        # Simple greeting template
        greeting = f"""Hello {user_name}! 👋

I'm your Jira Support Assistant. I can help you with:
• Create support tickets
• Check ticket status  
• Update existing tickets

What can I help you with today?"""
        
        if detected_language == Language.ARABIC:
            greeting = f"""مرحباً {user_name}! 👋

أنا مساعد دعم Jira. يمكنني مساعدتك في:
• إنشاء تذاكر الدعم
• التحقق من حالة التذكرة
• تحديث التذاكر الموجودة

كيف يمكنني مساعدتك اليوم؟"""
        
        await gallabox_service.send_text_message(user_phone, greeting)
        
        conversation_memory.add_message(
            user_phone,
            MessageRole.AGENT,
            greeting,
            intent="general_response"
        )
        
        return {
            "intent": "general_inquiry",
            "action": "responded",
            "response_sent": True
        }
    
    # ==========================================
    # LEGACY METHODS
    # ==========================================
    
    def _get_conversation_history(self, user_phone: str) -> List[Dict]:
        """Legacy method"""
        return conversation_memory.get_recent_context(user_phone, messages=5)
    
    def _update_context(
        self, 
        user_phone: str, 
        message: str, 
        intent: str,
        confidence: float
    ):
        """Legacy context update"""
        if user_phone not in self._conversation_context:
            self._conversation_context[user_phone] = []
        
        self._conversation_context[user_phone].append({
            "message": message[:100],
            "intent": intent,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self._conversation_context[user_phone]) > 10:
            self._conversation_context[user_phone] = self._conversation_context[user_phone][-10:]
    
    def cleanup_old_pending_tickets(self):
        """Cleanup old pending tickets"""
        return response_service.cleanup_old_pending_tickets()


# Global instance
intent_service = IntentService()