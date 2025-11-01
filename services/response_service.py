# services/response_service.py
"""
Response & Session Management Service
Handles pending tickets and user statistics
"""

from models.schemas import PendingTicket
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class ResponseService:
    """Manage user sessions and pending tickets"""
    
    def __init__(self):
        # Pending tickets awaiting confirmation
        self._pending_tickets: Dict[str, PendingTicket] = {}
        
        # User statistics
        self._user_stats: Dict[str, Dict] = defaultdict(lambda: {
            "messages_sent": 0,
            "tickets_created": 0,
            "tickets_checked": 0,
            "first_contact": None,
            "last_contact": None,
            "total_interactions": 0
        })
        
        # Auto-cleanup old pending tickets
        self._pending_ticket_timeout_minutes = 60
    
    def store_pending_ticket(self, user_phone: str, ticket: PendingTicket):
        """Store a pending ticket awaiting user confirmation"""
        self._pending_tickets[user_phone] = ticket
        print(f"📝 Stored pending ticket for {user_phone}")
    
    def get_pending_ticket(self, user_phone: str) -> Optional[PendingTicket]:
        """Get pending ticket for user"""
        ticket = self._pending_tickets.get(user_phone)
        
        if ticket:
            # Check if expired
            age = datetime.now() - ticket.timestamp
            if age > timedelta(minutes=self._pending_ticket_timeout_minutes):
                print(f"⏰ Pending ticket expired for {user_phone}")
                del self._pending_tickets[user_phone]
                return None
        
        return ticket
    
    def clear_pending_ticket(self, user_phone: str) -> bool:
        """Clear pending ticket after creation or cancellation"""
        if user_phone in self._pending_tickets:
            del self._pending_tickets[user_phone]
            print(f"🧹 Cleared pending ticket for {user_phone}")
            return True
        return False
    
    def get_all_pending_tickets(self) -> Dict[str, PendingTicket]:
        """Get all pending tickets (for admin/debugging)"""
        return self._pending_tickets.copy()
    
    def get_pending_tickets_count(self) -> int:
        """Get count of pending tickets"""
        return len(self._pending_tickets)
    
    def update_user_stats(
        self, 
        user_phone: str, 
        action: str = "message",
        **kwargs
    ):
        """Update user interaction statistics"""
        stats = self._user_stats[user_phone]
        
        now = datetime.now()
        
        if stats["first_contact"] is None:
            stats["first_contact"] = now.isoformat()
        
        stats["last_contact"] = now.isoformat()
        stats["total_interactions"] += 1
        
        if action == "message":
            stats["messages_sent"] += 1
        elif action == "ticket_created":
            stats["tickets_created"] += 1
        elif action == "ticket_checked":
            stats["tickets_checked"] += 1
        
        # Store additional data
        for key, value in kwargs.items():
            if key not in ["message", "messages_sent", "tickets_created"]:
                stats[key] = value
    
    def get_user_stats(self, user_phone: str) -> Dict:
        """Get statistics for a user"""
        return self._user_stats.get(user_phone, {
            "messages_sent": 0,
            "tickets_created": 0,
            "tickets_checked": 0,
            "first_contact": None,
            "last_contact": None,
            "total_interactions": 0
        })
    
    def cleanup_old_pending_tickets(self):
        """Remove expired pending tickets"""
        cutoff = datetime.now() - timedelta(minutes=self._pending_ticket_timeout_minutes)
        
        expired = [
            phone for phone, ticket in self._pending_tickets.items()
            if ticket.timestamp < cutoff
        ]
        
        for phone in expired:
            del self._pending_tickets[phone]
        
        if expired:
            print(f"🧹 Cleaned up {len(expired)} expired pending tickets")
        
        return len(expired)


response_service = ResponseService()