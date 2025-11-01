"""
🧠 Conversation Memory & Session Management
Tracks multi-turn conversations, user context, and conversation state
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
from collections import defaultdict, deque
import json

from services.property_intelligence import PropertyRequirements
from services.lead_qualifier import BANTScore

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class ConversationState(str, Enum):
    GREETING = "greeting"
    INQUIRY = "inquiry"
    QUALIFICATION = "qualification"
    PROPERTY_SEARCH = "property_search"
    VIEWING_SCHEDULE = "viewing_schedule"
    NEGOTIATION = "negotiation"
    DOCUMENTATION = "documentation"
    SUPPORT_TICKET = "support_ticket"
    CLOSED = "closed"

class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime
    intent: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = {}

class UserPreferences(BaseModel):
    preferred_language: str = "en"
    communication_style: str = "professional"  # professional, casual, formal
    preferred_contact_method: str = "whatsapp"
    timezone: str = "Asia/Dubai"
    marketing_consent: bool = False

class ConversationContext(BaseModel):
    user_phone: str
    user_name: str
    conversation_id: str
    state: ConversationState = ConversationState.GREETING
    started_at: datetime
    last_activity: datetime
    message_count: int = 0
    messages: List[ConversationMessage] = []
    
    # Property context
    current_property_requirements: Optional[PropertyRequirements] = None
    previous_searches: List[PropertyRequirements] = []
    
    # Lead context
    lead_score: Optional[BANTScore] = None
    is_vip: bool = False
    vip_tier: Optional[str] = None
    
    # User preferences
    preferences: UserPreferences = UserPreferences()
    
    # Conversation flow tracking
    topics_discussed: List[str] = []
    questions_asked: List[str] = []
    properties_viewed: List[str] = []
    
    # Support ticket context
    pending_ticket_key: Optional[str] = None
    active_tickets: List[str] = []
    
    # Metadata
    metadata: Dict[str, Any] = {}

# ==========================================
# CONVERSATION MEMORY SERVICE
# ==========================================

class ConversationMemoryService:
    """
    Manages conversation history, context, and session state
    """
    
    def __init__(
        self,
        max_history_per_user: int = 50,
        session_timeout_minutes: int = 30,
        max_sessions: int = 10000
    ):
        # Active sessions
        self._sessions: Dict[str, ConversationContext] = {}
        
        # Configuration
        self._max_history = max_history_per_user
        self._session_timeout = timedelta(minutes=session_timeout_minutes)
        self._max_sessions = max_sessions
        
        # User statistics
        self._user_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_messages": 0,
            "total_sessions": 0,
            "first_contact": None,
            "last_contact": None,
            "total_properties_viewed": 0,
            "total_tickets_created": 0
        })
        
        # Cleanup tracking
        self._last_cleanup = datetime.now()
    
    # ==========================================
    # SESSION MANAGEMENT
    # ==========================================
    
    def get_or_create_session(
        self,
        user_phone: str,
        user_name: str = "User"
    ) -> ConversationContext:
        """
        Get existing session or create new one
        
        Args:
            user_phone: User's phone number
            user_name: User's name
        
        Returns:
            ConversationContext
        """
        
        # Auto cleanup if needed
        if (datetime.now() - self._last_cleanup).total_seconds() > 300:  # Every 5 minutes
            self._cleanup_expired_sessions()
        
        # Check if session exists and is not expired
        if user_phone in self._sessions:
            session = self._sessions[user_phone]
            
            # Check if expired
            if datetime.now() - session.last_activity > self._session_timeout:
                print(f"🕐 Session expired for {user_phone}, creating new session")
                # Archive old session (could save to DB here)
                self._archive_session(session)
                # Create new session
                session = self._create_new_session(user_phone, user_name)
            else:
                # Update activity timestamp
                session.last_activity = datetime.now()
        else:
            # Create new session
            session = self._create_new_session(user_phone, user_name)
        
        return session
    
    def _create_new_session(
        self,
        user_phone: str,
        user_name: str
    ) -> ConversationContext:
        """Create a new conversation session"""
        
        now = datetime.now()
        
        session = ConversationContext(
            user_phone=user_phone,
            user_name=user_name,
            conversation_id=f"{user_phone}_{int(now.timestamp())}",
            started_at=now,
            last_activity=now
        )
        
        # Store session
        self._sessions[user_phone] = session
        
        # Update user stats
        stats = self._user_stats[user_phone]
        stats["total_sessions"] += 1
        if not stats["first_contact"]:
            stats["first_contact"] = now.isoformat()
        stats["last_contact"] = now.isoformat()
        
        print(f"🆕 New session created for {user_name} ({user_phone})")
        
        return session
    
    def end_session(self, user_phone: str):
        """Explicitly end a session"""
        if user_phone in self._sessions:
            session = self._sessions[user_phone]
            session.state = ConversationState.CLOSED
            self._archive_session(session)
            del self._sessions[user_phone]
            print(f"🔚 Session ended for {user_phone}")
    
    def _archive_session(self, session: ConversationContext):
        """
        Archive session for future analysis
        In production, this would save to database/S3
        """
        # For now, just log summary
        print(f"📦 Archiving session: {session.conversation_id}")
        print(f"   Messages: {session.message_count}")
        print(f"   Duration: {(session.last_activity - session.started_at).total_seconds():.0f}s")
        print(f"   State: {session.state.value}")
        
        # TODO: Save to database or S3 for training/analysis
    
    # ==========================================
    # MESSAGE TRACKING
    # ==========================================
    
    def add_message(
        self,
        user_phone: str,
        role: MessageRole,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Dict[str, Any] = None
    ) -> ConversationMessage:
        """
        Add a message to conversation history
        
        Args:
            user_phone: User's phone number
            role: Message role (user/agent/system)
            content: Message content
            intent: Detected intent
            confidence: Intent confidence score
            metadata: Additional metadata
        
        Returns:
            ConversationMessage
        """
        
        session = self.get_or_create_session(user_phone)
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            intent=intent,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        # Add to session messages
        session.messages.append(message)
        session.message_count += 1
        session.last_activity = datetime.now()
        
        # Trim history if too long
        if len(session.messages) > self._max_history:
            session.messages = session.messages[-self._max_history:]
        
        # Update user stats
        self._user_stats[user_phone]["total_messages"] += 1
        self._user_stats[user_phone]["last_contact"] = datetime.now().isoformat()
        
        return message
    
    def get_conversation_history(
        self,
        user_phone: str,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> List[ConversationMessage]:
        """
        Get conversation history for user
        
        Args:
            user_phone: User's phone number
            limit: Maximum number of messages to return
            include_system: Include system messages
        
        Returns:
            List of ConversationMessage
        """
        
        if user_phone not in self._sessions:
            return []
        
        session = self._sessions[user_phone]
        messages = session.messages
        
        # Filter system messages if needed
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_recent_context(
        self,
        user_phone: str,
        messages: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context in simple format
        Useful for passing to OpenAI
        
        Args:
            user_phone: User's phone number
            messages: Number of recent messages
        
        Returns:
            List of dicts with 'role' and 'message'
        """
        
        history = self.get_conversation_history(user_phone, limit=messages)
        
        return [
            {
                "role": msg.role.value,
                "message": msg.content[:200],  # Truncate for token efficiency
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in history
        ]
    
    # ==========================================
    # STATE MANAGEMENT
    # ==========================================
    
    def update_state(
        self,
        user_phone: str,
        new_state: ConversationState
    ):
        """Update conversation state"""
        
        session = self.get_or_create_session(user_phone)
        old_state = session.state
        session.state = new_state
        
        print(f"🔄 State transition for {user_phone}: {old_state.value} → {new_state.value}")
        
        # Add system message
        self.add_message(
            user_phone,
            MessageRole.SYSTEM,
            f"State changed to {new_state.value}",
            metadata={"old_state": old_state.value, "new_state": new_state.value}
        )
    
    def get_state(self, user_phone: str) -> ConversationState:
        """Get current conversation state"""
        
        if user_phone not in self._sessions:
            return ConversationState.GREETING
        
        return self._sessions[user_phone].state
    
    # ==========================================
    # PROPERTY CONTEXT MANAGEMENT
    # ==========================================
    
    def update_property_requirements(
        self,
        user_phone: str,
        requirements: PropertyRequirements
    ):
        """Update current property search requirements"""
        
        session = self.get_or_create_session(user_phone)
        
        # Save previous as history
        if session.current_property_requirements:
            session.previous_searches.append(session.current_property_requirements)
        
        # Update current
        session.current_property_requirements = requirements
        
        # Update state if needed
        if session.state == ConversationState.GREETING:
            self.update_state(user_phone, ConversationState.INQUIRY)
        
        print(f"🏠 Property requirements updated for {user_phone}")
        print(f"   Type: {requirements.property_type}")
        print(f"   Bedrooms: {requirements.bedrooms}")
        print(f"   Budget: {requirements.budget.min if requirements.budget else 'N/A'}")
    
    def get_property_requirements(
        self,
        user_phone: str
    ) -> Optional[PropertyRequirements]:
        """Get current property requirements"""
        
        if user_phone not in self._sessions:
            return None
        
        return self._sessions[user_phone].current_property_requirements
    
    def add_property_viewed(
        self,
        user_phone: str,
        property_id: str
    ):
        """Track property viewing"""
        
        session = self.get_or_create_session(user_phone)
        session.properties_viewed.append(property_id)
        
        # Update stats
        self._user_stats[user_phone]["total_properties_viewed"] += 1
    
    # ==========================================
    # LEAD CONTEXT MANAGEMENT
    # ==========================================
    
    def update_lead_score(
        self,
        user_phone: str,
        bant_score: BANTScore
    ):
        """Update lead qualification score"""
        
        session = self.get_or_create_session(user_phone)
        session.lead_score = bant_score
        
        print(f"📊 Lead score updated for {user_phone}: {bant_score.total_score}/100")
    
    def set_vip_status(
        self,
        user_phone: str,
        is_vip: bool,
        tier: Optional[str] = None
    ):
        """Set VIP status"""
        
        session = self.get_or_create_session(user_phone)
        session.is_vip = is_vip
        session.vip_tier = tier
        
        if is_vip:
            print(f"👑 VIP status set for {user_phone} | Tier: {tier}")
    
    # ==========================================
    # TOPIC TRACKING
    # ==========================================
    
    def add_topic(
        self,
        user_phone: str,
        topic: str
    ):
        """Track topics discussed"""
        
        session = self.get_or_create_session(user_phone)
        if topic not in session.topics_discussed:
            session.topics_discussed.append(topic)
    
    def has_discussed_topic(
        self,
        user_phone: str,
        topic: str
    ) -> bool:
        """Check if topic was already discussed"""
        
        if user_phone not in self._sessions:
            return False
        
        return topic in self._sessions[user_phone].topics_discussed
    
    # ==========================================
    # TICKET CONTEXT
    # ==========================================
    
    def set_pending_ticket(
        self,
        user_phone: str,
        ticket_key: str
    ):
        """Set pending ticket key"""
        
        session = self.get_or_create_session(user_phone)
        session.pending_ticket_key = ticket_key
        
        # Update state
        if session.state != ConversationState.SUPPORT_TICKET:
            self.update_state(user_phone, ConversationState.SUPPORT_TICKET)
    
    def add_active_ticket(
        self,
        user_phone: str,
        ticket_key: str
    ):
        """Add to active tickets list"""
        
        session = self.get_or_create_session(user_phone)
        if ticket_key not in session.active_tickets:
            session.active_tickets.append(ticket_key)
        
        # Update stats
        self._user_stats[user_phone]["total_tickets_created"] += 1
    
    # ==========================================
    # USER PREFERENCES
    # ==========================================
    
    def update_preference(
        self,
        user_phone: str,
        key: str,
        value: Any
    ):
        """Update user preference"""
        
        session = self.get_or_create_session(user_phone)
        
        if hasattr(session.preferences, key):
            setattr(session.preferences, key, value)
            print(f"✏️ Preference updated for {user_phone}: {key} = {value}")
    
    def get_preference(
        self,
        user_phone: str,
        key: str
    ) -> Optional[Any]:
        """Get user preference"""
        
        if user_phone not in self._sessions:
            return None
        
        return getattr(self._sessions[user_phone].preferences, key, None)
    
    # ==========================================
    # ANALYTICS & STATS
    # ==========================================
    
    def get_session_summary(
        self,
        user_phone: str
    ) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        
        if user_phone not in self._sessions:
            return {"error": "No active session"}
        
        session = self._sessions[user_phone]
        
        duration = (session.last_activity - session.started_at).total_seconds()
        
        return {
            "conversation_id": session.conversation_id,
            "user": {
                "phone": session.user_phone,
                "name": session.user_name,
                "is_vip": session.is_vip,
                "vip_tier": session.vip_tier
            },
            "session": {
                "state": session.state.value,
                "started_at": session.started_at.isoformat(),
                "duration_seconds": int(duration),
                "message_count": session.message_count
            },
            "property_context": {
                "current_search": session.current_property_requirements.dict() if session.current_property_requirements else None,
                "previous_searches": len(session.previous_searches),
                "properties_viewed": len(session.properties_viewed)
            },
            "lead_context": {
                "score": session.lead_score.total_score if session.lead_score else None,
                "type": session.lead_score.lead_type.value if session.lead_score else None
            },
            "support_context": {
                "pending_ticket": session.pending_ticket_key,
                "active_tickets": len(session.active_tickets)
            },
            "engagement": {
                "topics_discussed": session.topics_discussed,
                "questions_asked": len(session.questions_asked)
            }
        }
    
    def get_user_stats(
        self,
        user_phone: str
    ) -> Dict[str, Any]:
        """Get user statistics across all sessions"""
        
        return self._user_stats.get(user_phone, {
            "total_messages": 0,
            "total_sessions": 0,
            "first_contact": None,
            "last_contact": None,
            "total_properties_viewed": 0,
            "total_tickets_created": 0
        })
    
    def get_all_active_sessions(self) -> Dict[str, Dict]:
        """Get all active sessions summary"""
        
        return {
            phone: {
                "user_name": session.user_name,
                "state": session.state.value,
                "message_count": session.message_count,
                "is_vip": session.is_vip,
                "last_activity": session.last_activity.isoformat(),
                "duration_minutes": int((session.last_activity - session.started_at).total_seconds() / 60)
            }
            for phone, session in self._sessions.items()
        }
    
    # ==========================================
    # CLEANUP & MAINTENANCE
    # ==========================================
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        
        now = datetime.now()
        expired = []
        
        for phone, session in self._sessions.items():
            if now - session.last_activity > self._session_timeout:
                expired.append(phone)
        
        for phone in expired:
            self._archive_session(self._sessions[phone])
            del self._sessions[phone]
        
        if expired:
            print(f"🧹 Cleaned up {len(expired)} expired sessions")
        
        self._last_cleanup = now
    
    def force_cleanup(self):
        """Force cleanup of all expired sessions"""
        self._cleanup_expired_sessions()
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self._sessions)
    
    # ==========================================
    # EXPORT & IMPORT (for persistence)
    # ==========================================
    
    def export_session(self, user_phone: str) -> Optional[Dict]:
        """Export session data for persistence"""
        
        if user_phone not in self._sessions:
            return None
        
        session = self._sessions[user_phone]
        
        return {
            "user_phone": session.user_phone,
            "user_name": session.user_name,
            "conversation_id": session.conversation_id,
            "state": session.state.value,
            "started_at": session.started_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": session.message_count,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            "property_requirements": session.current_property_requirements.dict() if session.current_property_requirements else None,
            "lead_score": session.lead_score.dict() if session.lead_score else None,
            "is_vip": session.is_vip,
            "vip_tier": session.vip_tier,
            "topics_discussed": session.topics_discussed,
            "properties_viewed": session.properties_viewed,
            "active_tickets": session.active_tickets,
            "preferences": session.preferences.dict()
        }
    
    def clear_session(self, user_phone: str):
        """Clear session for a user"""
        
        if user_phone in self._sessions:
            self._archive_session(self._sessions[user_phone])
            del self._sessions[user_phone]
            print(f"🗑️ Session cleared for {user_phone}")


# Global instance
conversation_memory = ConversationMemoryService(
    max_history_per_user=50,
    session_timeout_minutes=30,
    max_sessions=10000
)