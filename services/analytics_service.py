# services/analytics_service.py
"""
Real-time Analytics & Monitoring Service
Tracks KPIs, response times, and system health
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

class AnalyticsService:
    """Comprehensive analytics and monitoring"""
    
    def __init__(self):
        # Response time tracking (rolling window)
        self._response_times = deque(maxlen=1000)
        
        # Intent distribution
        self._intent_counts: Dict[str, int] = defaultdict(int)
        
        # Hourly metrics
        self._hourly_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "messages": 0,
            "tickets_created": 0,
            "tickets_resolved": 0,
            "average_response_time_ms": 0,
            "vip_interactions": 0,
            "escalations": 0
        })
        
        # Daily summaries
        self._daily_summaries: Dict[str, Dict] = {}
        
        # Error tracking
        self._errors: List[Dict] = []
        self._error_rate_window = deque(maxlen=100)
        
        # User engagement
        self._active_users: Dict[str, datetime] = {}
        self._user_activity_window_minutes = 30
    
    def track_response_time(self, duration_ms: int):
        """Track response time"""
        self._response_times.append(duration_ms)
    
    def track_intent(self, intent: str):
        """Track intent distribution"""
        self._intent_counts[intent] += 1
        
        # Update hourly
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        # Could add intent breakdown per hour if needed
    
    def track_message(
        self, 
        user_phone: str,
        intent: str = None,
        response_time_ms: int = None,
        is_vip: bool = False,
        escalated: bool = False
    ):
        """Track incoming message and metrics"""
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        metrics = self._hourly_metrics[hour_key]
        
        metrics["messages"] += 1
        
        if response_time_ms:
            self.track_response_time(response_time_ms)
            # Update average
            if self._response_times:
                metrics["average_response_time_ms"] = int(
                    sum(self._response_times) / len(self._response_times)
                )
        
        if intent:
            self.track_intent(intent)
        
        if is_vip:
            metrics["vip_interactions"] += 1
        
        if escalated:
            metrics["escalations"] += 1
        
        # Track active users
        self._active_users[user_phone] = datetime.now()
    
    def track_ticket_created(self):
        """Track ticket creation"""
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        self._hourly_metrics[hour_key]["tickets_created"] += 1
    
    def track_ticket_resolved(self):
        """Track ticket resolution"""
        hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        self._hourly_metrics[hour_key]["tickets_resolved"] += 1
    
    def track_error(
        self, 
        error_type: str,
        error_message: str,
        context: Dict = None
    ):
        """Track errors"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_message,
            "context": context or {}
        }
        
        self._errors.append(error_entry)
        self._error_rate_window.append(1)
        
        # Keep only last 100 errors
        if len(self._errors) > 100:
            self._errors = self._errors[-100:]
    
    def get_realtime_metrics(self) -> Dict:
        """Get current metrics"""
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        current_hour = self._hourly_metrics.get(hour_key, {})
        
        # Calculate active users
        active_cutoff = now - timedelta(minutes=self._user_activity_window_minutes)
        active_users = sum(
            1 for last_seen in self._active_users.values()
            if last_seen > active_cutoff
        )
        
        # Response time stats
        if self._response_times:
            avg_response = statistics.mean(self._response_times)
            p95_response = statistics.quantiles(self._response_times, n=20)[18]  # 95th percentile
        else:
            avg_response = 0
            p95_response = 0
        
        # Error rate
        error_rate = len(self._error_rate_window) / 100 if self._error_rate_window else 0
        
        return {
            "timestamp": now.isoformat(),
            "current_hour": {
                "messages": current_hour.get("messages", 0),
                "tickets_created": current_hour.get("tickets_created", 0),
                "tickets_resolved": current_hour.get("tickets_resolved", 0),
                "vip_interactions": current_hour.get("vip_interactions", 0),
                "escalations": current_hour.get("escalations", 0)
            },
            "response_times": {
                "average_ms": int(avg_response),
                "p95_ms": int(p95_response),
                "count": len(self._response_times)
            },
            "active_users": active_users,
            "error_rate": round(error_rate, 3),
            "recent_errors": len(self._errors)
        }
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """Get intent distribution"""
        total = sum(self._intent_counts.values())
        
        return {
            "total": total,
            "breakdown": dict(self._intent_counts),
            "percentages": {
                intent: round((count / total) * 100, 1) if total > 0 else 0
                for intent, count in self._intent_counts.items()
            }
        }
    
    def get_hourly_summary(self, hours_back: int = 24) -> List[Dict]:
        """Get hourly metrics for last N hours"""
        summaries = []
        now = datetime.now()
        
        for i in range(hours_back):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y-%m-%d-%H")
            
            metrics = self._hourly_metrics.get(hour_key, {
                "messages": 0,
                "tickets_created": 0,
                "tickets_resolved": 0,
                "average_response_time_ms": 0,
                "vip_interactions": 0,
                "escalations": 0
            })
            
            summaries.append({
                "hour": hour_key,
                "timestamp": hour.isoformat(),
                **metrics
            })
        
        return summaries
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Get daily summary"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Aggregate from hourly metrics
        total_messages = 0
        total_tickets_created = 0
        total_tickets_resolved = 0
        total_vip = 0
        total_escalations = 0
        
        for hour_key, metrics in self._hourly_metrics.items():
            if hour_key.startswith(date):
                total_messages += metrics["messages"]
                total_tickets_created += metrics["tickets_created"]
                total_tickets_resolved += metrics["tickets_resolved"]
                total_vip += metrics["vip_interactions"]
                total_escalations += metrics["escalations"]
        
        resolution_rate = 0
        if total_tickets_created > 0:
            resolution_rate = (total_tickets_resolved / total_tickets_created) * 100
        
        return {
            "date": date,
            "total_messages": total_messages,
            "tickets_created": total_tickets_created,
            "tickets_resolved": total_tickets_resolved,
            "vip_interactions": total_vip,
            "escalations": total_escalations,
            "resolution_rate_percent": round(resolution_rate, 1),
            "average_tickets_per_hour": round(total_tickets_created / 24, 1)
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors"""
        return self._errors[-limit:]
    
    def export_analytics(self) -> Dict:
        """Export all analytics data"""
        return {
            "realtime_metrics": self.get_realtime_metrics(),
            "intent_distribution": self.get_intent_distribution(),
            "hourly_summary": self.get_hourly_summary(24),
            "daily_summary": self.get_daily_summary(),
            "recent_errors": self.get_recent_errors(20),
            "exported_at": datetime.now().isoformat()
        }


analytics_service = AnalyticsService()