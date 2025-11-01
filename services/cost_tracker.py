"""
Advanced Cost Tracking & Analytics Service
Tracks OpenAI and Gallabox costs with detailed metrics
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

class CostTracker:
    """Real-time cost tracking with analytics"""
    
    # Pricing (update as needed)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.150 / 1_000_000,   # $0.150 per 1M input tokens
            "output": 0.600 / 1_000_000   # $0.600 per 1M output tokens
        },
        "gpt-4o": {
            "input": 5.00 / 1_000_000,
            "output": 15.00 / 1_000_000
        },
        "gallabox": {
            "message": 0.005,  # $0.005 per message (example)
            "media": 0.01      # $0.01 per media message
        }
    }
    
    def __init__(self):
        # Daily cost tracking
        self._daily_costs: Dict[str, Dict] = defaultdict(lambda: {
            "openai_cost": 0.0,
            "gallabox_cost": 0.0,
            "total_tokens": 0,
            "total_messages": 0,
            "breakdown": []
        })
        
        # User-wise cost tracking
        self._user_costs: Dict[str, float] = defaultdict(float)
        
        # Intent-wise cost tracking
        self._intent_costs: Dict[str, Dict] = defaultdict(lambda: {
            "count": 0,
            "total_cost": 0.0,
            "avg_cost": 0.0
        })
    
    def track_openai_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_phone: str = None,
        intent: str = None
    ) -> float:
        """Track OpenAI API usage and calculate cost"""
        
        pricing = self.PRICING.get(model, self.PRICING["gpt-4o-mini"])
        
        input_cost = prompt_tokens * pricing["input"]
        output_cost = completion_tokens * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Track daily
        date_key = datetime.now().strftime("%Y-%m-%d")
        self._daily_costs[date_key]["openai_cost"] += total_cost
        self._daily_costs[date_key]["total_tokens"] += (prompt_tokens + completion_tokens)
        self._daily_costs[date_key]["breakdown"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "openai",
            "model": model,
            "tokens": prompt_tokens + completion_tokens,
            "cost": round(total_cost, 6),
            "user": user_phone,
            "intent": intent
        })
        
        # Track by user
        if user_phone:
            self._user_costs[user_phone] += total_cost
        
        # Track by intent
        if intent:
            self._intent_costs[intent]["count"] += 1
            self._intent_costs[intent]["total_cost"] += total_cost
            self._intent_costs[intent]["avg_cost"] = (
                self._intent_costs[intent]["total_cost"] / 
                self._intent_costs[intent]["count"]
            )
        
        print(f"💰 OpenAI cost: ${total_cost:.6f} ({prompt_tokens + completion_tokens} tokens)")
        
        return total_cost
    
    def track_gallabox_usage(
        self,
        message_type: str = "text",
        user_phone: str = None
    ) -> float:
        """Track Gallabox messaging cost"""
        
        cost = self.PRICING["gallabox"]["media"] if message_type != "text" else self.PRICING["gallabox"]["message"]
        
        date_key = datetime.now().strftime("%Y-%m-%d")
        self._daily_costs[date_key]["gallabox_cost"] += cost
        self._daily_costs[date_key]["total_messages"] += 1
        self._daily_costs[date_key]["breakdown"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "gallabox",
            "message_type": message_type,
            "cost": cost,
            "user": user_phone
        })
        
        if user_phone:
            self._user_costs[user_phone] += cost
        
        return cost
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Get cost summary for a specific date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        data = self._daily_costs.get(date, {
            "openai_cost": 0.0,
            "gallabox_cost": 0.0,
            "total_tokens": 0,
            "total_messages": 0,
            "breakdown": []
        })
        
        return {
            "date": date,
            "openai_cost": round(data["openai_cost"], 4),
            "gallabox_cost": round(data["gallabox_cost"], 4),
            "total_cost": round(data["openai_cost"] + data["gallabox_cost"], 4),
            "total_tokens": data["total_tokens"],
            "total_messages": data["total_messages"],
            "avg_cost_per_message": round(
                (data["openai_cost"] + data["gallabox_cost"]) / max(data["total_messages"], 1),
                6
            )
        }
    
    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        """Get monthly cost summary"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        month_prefix = f"{year}-{month:02d}"
        
        total_openai = 0.0
        total_gallabox = 0.0
        total_tokens = 0
        total_messages = 0
        
        for date_key, data in self._daily_costs.items():
            if date_key.startswith(month_prefix):
                total_openai += data["openai_cost"]
                total_gallabox += data["gallabox_cost"]
                total_tokens += data["total_tokens"]
                total_messages += data["total_messages"]
        
        return {
            "month": month_prefix,
            "openai_cost": round(total_openai, 2),
            "gallabox_cost": round(total_gallabox, 2),
            "total_cost": round(total_openai + total_gallabox, 2),
            "total_tokens": total_tokens,
            "total_messages": total_messages
        }
    
    def get_user_cost(self, user_phone: str) -> float:
        """Get total cost for a specific user"""
        return round(self._user_costs.get(user_phone, 0.0), 4)
    
    def get_top_users_by_cost(self, limit: int = 10) -> List[Dict]:
        """Get users with highest costs"""
        sorted_users = sorted(
            self._user_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {"phone": phone, "total_cost": round(cost, 4)}
            for phone, cost in sorted_users
        ]
    
    def get_intent_analytics(self) -> Dict:
        """Get cost analytics by intent"""
        return {
            intent: {
                "count": data["count"],
                "total_cost": round(data["total_cost"], 4),
                "avg_cost": round(data["avg_cost"], 6)
            }
            for intent, data in self._intent_costs.items()
        }
    
    def export_to_dict(self) -> Dict:
        """Export all cost data for storage"""
        return {
            "daily_costs": dict(self._daily_costs),
            "user_costs": dict(self._user_costs),
            "intent_costs": dict(self._intent_costs),
            "exported_at": datetime.now().isoformat()
        }


# Global instance
cost_tracker = CostTracker()