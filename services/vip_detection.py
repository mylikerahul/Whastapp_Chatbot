# services/vip_detection.py
"""
VIP Client Detection for Luxury Real Estate
Identifies high-value clients and escalates accordingly
"""

from typing import Dict, Tuple, Optional
import re
from datetime import datetime

class VIPDetectionService:
    """Detect and prioritize VIP clients"""
    
    def __init__(self):
        # VIP indicators
        self._vip_keywords = [
            "vip", "premium", "exclusive", "high-value",
            "investor", "portfolio", "multiple properties",
            "urgent client", "important client"
        ]
        
        # Luxury property indicators
        self._luxury_indicators = [
            "penthouse", "villa", "mansion", "estate",
            "palm jumeirah", "burj khalifa", "emirates hills",
            "jumeirah bay island", "dubai hills",
            "million", "billion", "luxury"
        ]
        
        # Business value indicators
        self._business_value_indicators = [
            "deal pending", "closing soon", "contract",
            "agreement", "sale falling through", "losing client",
            "commission", "multiple units"
        ]
        
        # Known VIP phone numbers (can be loaded from database)
        self._vip_registry: Dict[str, Dict] = {
            # Example: "+971501234567": {"name": "John Doe", "tier": "platinum"}
        }
        
        # Temporary VIP flags (set during conversation)
        self._session_vip_flags: Dict[str, Dict] = {}
    
    def detect_vip(
        self, 
        message: str, 
        user_phone: str,
        user_name: str = None
    ) -> Dict[str, any]:
        """
        Detect if this is a VIP client interaction
        
        Returns:
            {
                "is_vip": bool,
                "vip_tier": "standard|gold|platinum|diamond",
                "confidence": 0.0-1.0,
                "indicators": list,
                "auto_escalate": bool
            }
        """
        message_lower = message.lower()
        
        # Check registry first
        if user_phone in self._vip_registry:
            vip_data = self._vip_registry[user_phone]
            return {
                "is_vip": True,
                "vip_tier": vip_data.get("tier", "gold"),
                "confidence": 1.0,
                "indicators": ["Registered VIP client"],
                "auto_escalate": True,
                "vip_name": vip_data.get("name")
            }
        
        # Check session flags
        if user_phone in self._session_vip_flags:
            return self._session_vip_flags[user_phone]
        
        # Detect from message content
        indicators = []
        score = 0.0
        
        # VIP keywords
        for keyword in self._vip_keywords:
            if keyword in message_lower:
                indicators.append(f"VIP keyword: {keyword}")
                score += 0.3
        
        # Luxury property mentions
        for indicator in self._luxury_indicators:
            if indicator in message_lower:
                indicators.append(f"Luxury property: {indicator}")
                score += 0.2
        
        # Business value indicators
        for indicator in self._business_value_indicators:
            if indicator in message_lower:
                indicators.append(f"Business value: {indicator}")
                score += 0.25
        
        # Large number detection (price mentions)
        large_numbers = re.findall(r'\b(\d{1,3}(?:,\d{3})+|\d{7,})\b', message)
        if large_numbers:
            indicators.append(f"Large number mentioned: {large_numbers[0]}")
            score += 0.2
        
        # Determine VIP tier
        confidence = min(score, 1.0)
        is_vip = confidence >= 0.5
        
        if confidence >= 0.9:
            tier = "diamond"
        elif confidence >= 0.7:
            tier = "platinum"
        elif confidence >= 0.5:
            tier = "gold"
        else:
            tier = "standard"
        
        result = {
            "is_vip": is_vip,
            "vip_tier": tier,
            "confidence": round(confidence, 2),
            "indicators": indicators,
            "auto_escalate": is_vip and tier in ["platinum", "diamond"]
        }
        
        # Cache result for session
        if is_vip:
            self._session_vip_flags[user_phone] = result
            print(f"👑 VIP DETECTED: {user_name or user_phone} | Tier: {tier} | Confidence: {confidence:.2f}")
        
        return result
    
    def register_vip(
        self, 
        phone: str, 
        name: str, 
        tier: str = "gold",
        metadata: Dict = None
    ):
        """Manually register a VIP client"""
        self._vip_registry[phone] = {
            "name": name,
            "tier": tier,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        print(f"✅ VIP registered: {name} ({phone}) - {tier}")
    
    def remove_vip(self, phone: str):
        """Remove VIP status"""
        if phone in self._vip_registry:
            del self._vip_registry[phone]
            print(f"🗑️ VIP removed: {phone}")
    
    def get_vip_info(self, phone: str) -> Optional[Dict]:
        """Get VIP information"""
        return self._vip_registry.get(phone)
    
    def get_all_vips(self) -> Dict:
        """Get all registered VIPs"""
        return self._vip_registry.copy()
    
    def clear_session_flags(self, phone: str = None):
        """Clear session VIP flags"""
        if phone:
            if phone in self._session_vip_flags:
                del self._session_vip_flags[phone]
        else:
            self._session_vip_flags.clear()


vip_detection_service = VIPDetectionService()