# services/sentiment_service.py
"""
Advanced Sentiment Analysis for Priority Escalation
Detects frustrated customers and escalates automatically
"""

from typing import Dict, Tuple
import re
from datetime import datetime, timedelta
from collections import defaultdict

class SentimentAnalyzer:
    """Real-time sentiment analysis for customer messages"""
    
    def __init__(self):
        # Negative sentiment indicators
        self._negative_keywords = {
            "urgent": 3,
            "critical": 3,
            "emergency": 4,
            "immediately": 3,
            "asap": 2,
            "frustrated": 3,
            "angry": 3,
            "disappointed": 2,
            "unacceptable": 3,
            "terrible": 3,
            "worst": 3,
            "broken": 2,
            "not working": 2,
            "failed": 2,
            "issue": 1,
            "problem": 1,
            "bug": 1,
            "error": 1,
            "down": 2,
            "crash": 2,
            "losing": 3,
            "lost": 3
        }
        
        # Positive sentiment indicators
        self._positive_keywords = {
            "thank": 1,
            "thanks": 1,
            "appreciate": 2,
            "great": 2,
            "excellent": 2,
            "perfect": 2,
            "resolved": 2,
            "fixed": 2,
            "working": 1,
            "good": 1,
            "helpful": 2
        }
        
        # Urgency patterns (regex)
        self._urgency_patterns = [
            r"need.*immediately",
            r"urgent.*help",
            r"asap",
            r"right now",
            r"can't wait",
            r"losing.*money",
            r"client.*waiting",
            r"deal.*pending",
            r"vip.*client"
        ]
        
        # Track user frustration over time
        self._user_frustration_history: Dict[str, list] = defaultdict(list)
        self._frustration_window_minutes = 30
    
    def analyze_sentiment(
        self, 
        message: str, 
        user_phone: str = None
    ) -> Dict[str, any]:
        """
        Analyze message sentiment
        
        Returns:
            {
                "sentiment": "positive|neutral|negative",
                "score": -1.0 to 1.0,
                "urgency": 0-10,
                "escalate": bool,
                "reason": str
            }
        """
        message_lower = message.lower()
        
        # Calculate sentiment score
        negative_score = 0
        positive_score = 0
        
        for keyword, weight in self._negative_keywords.items():
            if keyword in message_lower:
                negative_score += weight
        
        for keyword, weight in self._positive_keywords.items():
            if keyword in message_lower:
                positive_score += weight
        
        # Normalize to -1 to 1
        total = negative_score + positive_score
        if total > 0:
            sentiment_score = (positive_score - negative_score) / total
        else:
            sentiment_score = 0.0
        
        # Determine sentiment category
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate urgency
        urgency = self._calculate_urgency(message_lower)
        
        # Check for urgency patterns
        pattern_urgency = 0
        for pattern in self._urgency_patterns:
            if re.search(pattern, message_lower):
                pattern_urgency += 2
        
        urgency = min(urgency + pattern_urgency, 10)
        
        # Track frustration history
        if user_phone:
            self._update_frustration_history(user_phone, sentiment_score, urgency)
            repeat_frustration = self._check_repeat_frustration(user_phone)
            if repeat_frustration:
                urgency = min(urgency + 3, 10)
        
        # Escalation logic
        should_escalate = (
            urgency >= 7 or 
            sentiment == "negative" and urgency >= 5 or
            "vip" in message_lower or
            "urgent" in message_lower and "client" in message_lower
        )
        
        escalation_reason = ""
        if should_escalate:
            if urgency >= 8:
                escalation_reason = "Critical urgency detected"
            elif "vip" in message_lower:
                escalation_reason = "VIP client mention"
            elif sentiment == "negative" and urgency >= 5:
                escalation_reason = "High negative sentiment with urgency"
            else:
                escalation_reason = "Escalation threshold met"
        
        result = {
            "sentiment": sentiment,
            "score": round(sentiment_score, 2),
            "urgency": urgency,
            "escalate": should_escalate,
            "reason": escalation_reason,
            "indicators": {
                "negative_score": negative_score,
                "positive_score": positive_score,
                "pattern_matches": pattern_urgency > 0
            }
        }
        
        print(f"😊 Sentiment: {sentiment} | Score: {sentiment_score:.2f} | Urgency: {urgency}/10")
        
        if should_escalate:
            print(f"🚨 ESCALATION TRIGGERED: {escalation_reason}")
        
        return result
    
    def _calculate_urgency(self, message: str) -> int:
        """Calculate urgency level 0-10"""
        urgency = 0
        
        # Exclamation marks
        urgency += min(message.count("!"), 3)
        
        # ALL CAPS words
        words = message.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 3]
        urgency += min(len(caps_words), 2)
        
        # Question marks (mild urgency)
        urgency += min(message.count("?"), 1)
        
        return urgency
    
    def _update_frustration_history(
        self, 
        user_phone: str, 
        sentiment_score: float,
        urgency: int
    ):
        """Track user frustration over time"""
        now = datetime.now()
        
        self._user_frustration_history[user_phone].append({
            "timestamp": now,
            "sentiment": sentiment_score,
            "urgency": urgency
        })
        
        # Cleanup old entries
        cutoff = now - timedelta(minutes=self._frustration_window_minutes)
        self._user_frustration_history[user_phone] = [
            entry for entry in self._user_frustration_history[user_phone]
            if entry["timestamp"] > cutoff
        ]
    
    def _check_repeat_frustration(self, user_phone: str) -> bool:
        """Check if user has repeated negative sentiment"""
        history = self._user_frustration_history.get(user_phone, [])
        
        if len(history) < 2:
            return False
        
        # Check last 3 messages
        recent = history[-3:]
        negative_count = sum(1 for entry in recent if entry["sentiment"] < -0.3)
        
        return negative_count >= 2
    
    def get_user_sentiment_trend(self, user_phone: str) -> Dict:
        """Get sentiment trend for a user"""
        history = self._user_frustration_history.get(user_phone, [])
        
        if not history:
            return {
                "trend": "neutral",
                "average_sentiment": 0.0,
                "message_count": 0
            }
        
        avg_sentiment = sum(entry["sentiment"] for entry in history) / len(history)
        
        if avg_sentiment < -0.3:
            trend = "declining"
        elif avg_sentiment > 0.3:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "average_sentiment": round(avg_sentiment, 2),
            "message_count": len(history),
            "recent_urgency": history[-1]["urgency"] if history else 0
        }


sentiment_analyzer = SentimentAnalyzer()