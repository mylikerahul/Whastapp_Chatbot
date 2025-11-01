"""
🏠 Property Intelligence Service - Dubai Real Estate Specialist
Extracts structured property requirements from natural language
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import re
import json

from services.openai_service import openai_service
from services.cost_tracker import cost_tracker

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class PropertyType(str, Enum):
    VILLA = "villa"
    APARTMENT = "apartment"
    PENTHOUSE = "penthouse"
    TOWNHOUSE = "townhouse"
    STUDIO = "studio"
    DUPLEX = "duplex"
    LAND = "land"
    OFFICE = "office"
    RETAIL = "retail"
    WAREHOUSE = "warehouse"

class Timeline(str, Enum):
    URGENT = "urgent"           # Within 2 weeks
    ONE_MONTH = "1_month"
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"
    EXPLORING = "exploring"
    NOT_MENTIONED = "not_mentioned"

class Purpose(str, Enum):
    BUY = "buy"
    RENT = "rent"
    INVEST = "invest"
    SELL = "sell"

class BudgetRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "AED"
    confidence: float = 0.0

class PropertyRequirements(BaseModel):
    property_type: Optional[PropertyType] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqft: Optional[int] = None
    budget: Optional[BudgetRange] = None
    locations: List[str] = []
    must_haves: List[str] = []
    nice_to_haves: List[str] = []
    timeline: Timeline = Timeline.NOT_MENTIONED
    purpose: Purpose = Purpose.BUY
    confidence: float = 0.0
    raw_message: str = ""
    extracted_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.extracted_at:
            self.extracted_at = datetime.now()

# ==========================================
# PROPERTY INTELLIGENCE SERVICE
# ==========================================

class PropertyIntelligenceService:
    """Advanced property requirement extraction using AI + Rules"""
    
    def __init__(self):
        # Dubai areas by tier
        self.dubai_areas = {
            "ultra_luxury": [
                "Palm Jumeirah", "Emirates Hills", "Jumeirah Bay Island",
                "Dubai Hills Estate", "Al Barari", "Bulgari Resort"
            ],
            "luxury": [
                "Dubai Marina", "Downtown Dubai", "Business Bay",
                "Jumeirah Beach Residence", "JBR", "Dubai Creek Harbour",
                "City Walk", "Bluewaters Island"
            ],
            "premium": [
                "Arabian Ranches", "Jumeirah Village Circle", "JVC",
                "Dubai Sports City", "Motor City", "Arabian Ranches 2",
                "Damac Hills", "Town Square"
            ],
            "affordable": [
                "Dubai Silicon Oasis", "DSO", "Discovery Gardens",
                "International City", "Dubailand", "Remraam",
                "Liwan", "Queue Point"
            ]
        }
        
        # Property type aliases
        self.property_aliases = {
            "flat": PropertyType.APARTMENT,
            "condo": PropertyType.APARTMENT,
            "duplex": PropertyType.DUPLEX,
            "triplex": PropertyType.APARTMENT,
            "bungalow": PropertyType.VILLA,
            "mansion": PropertyType.VILLA,
            "estate": PropertyType.VILLA,
            "plot": PropertyType.LAND,
            "commercial": PropertyType.OFFICE
        }
        
        # Typical price ranges (AED)
        self.price_ranges = {
            PropertyType.STUDIO: (400_000, 800_000),
            PropertyType.APARTMENT: {
                1: (800_000, 1_500_000),
                2: (1_500_000, 3_000_000),
                3: (2_500_000, 5_000_000),
                4: (4_000_000, 8_000_000)
            },
            PropertyType.VILLA: {
                3: (3_000_000, 8_000_000),
                4: (5_000_000, 15_000_000),
                5: (8_000_000, 25_000_000),
                6: (15_000_000, 40_000_000)
            },
            PropertyType.PENTHOUSE: {
                2: (5_000_000, 15_000_000),
                3: (10_000_000, 30_000_000),
                4: (20_000_000, 100_000_000)
            }
        }
    
    async def extract_requirements(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        user_phone: str = None
    ) -> PropertyRequirements:
        """
        Extract structured property requirements using AI + fallback rules
        
        Args:
            message: User's message
            conversation_history: Previous conversation context
            user_phone: User's phone number for cost tracking
        
        Returns:
            PropertyRequirements object
        """
        
        # Try AI extraction first
        try:
            ai_result = await self._ai_extraction(message, conversation_history, user_phone)
            if ai_result.confidence >= 0.6:
                print(f"🏠 AI Extraction: {ai_result.property_type} | {ai_result.bedrooms}BR | Confidence: {ai_result.confidence:.2f}")
                return ai_result
        except Exception as e:
            print(f"⚠️ AI extraction failed: {e}, falling back to rules")
        
        # Fallback to rule-based extraction
        rule_result = self._rule_based_extraction(message)
        print(f"🏠 Rule Extraction: {rule_result.property_type} | {rule_result.bedrooms}BR | Confidence: {rule_result.confidence:.2f}")
        return rule_result
    
    async def _ai_extraction(
        self,
        message: str,
        conversation_history: Optional[List[Dict]],
        user_phone: Optional[str]
    ) -> PropertyRequirements:
        """AI-powered extraction using GPT"""
        
        # Build context from history
        context = ""
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history[-3:]:
                context += f"- {msg.get('message', '')[:100]}\n"
        
        prompt = f"""Extract property requirements from this Dubai real estate inquiry.

**Message:** "{message}"

{context}

**Dubai Market Context:**
- Currency: AED (default)
- Popular areas: Palm Jumeirah, Dubai Marina, Downtown Dubai, Business Bay, JBR
- Typical prices:
  - Studio: 400K-800K AED
  - 1BR: 800K-1.5M AED
  - 2BR: 1.5M-3M AED
  - 3BR: 2.5M-5M AED
  - Villa 3BR: 3M-8M AED
  - Villa 4BR: 5M-15M AED
  - Penthouse: 10M-100M+ AED

**Extract and return JSON:**
{{
  "property_type": "villa|apartment|penthouse|townhouse|studio|land|office|null",
  "bedrooms": 0-10 or null,
  "bathrooms": 1-15 or null,
  "size_sqft": number or null,
  "budget": {{
    "min": number in AED or null,
    "max": number in AED or null,
    "currency": "AED",
    "confidence": 0.0-1.0
  }},
  "locations": ["Palm Jumeirah", "Dubai Marina"] or [],
  "must_haves": ["sea view", "pool", "maid room"] or [],
  "nice_to_haves": ["gym", "parking"] or [],
  "timeline": "urgent|1_month|3_months|6_months|exploring|not_mentioned",
  "purpose": "buy|rent|invest|sell",
  "confidence": 0.0-1.0
}}

**Examples:**

Input: "I want a 3-bedroom villa in Palm Jumeirah, budget 10-12 million"
Output: {{"property_type": "villa", "bedrooms": 3, "budget": {{"min": 10000000, "max": 12000000, "currency": "AED", "confidence": 0.95}}, "locations": ["Palm Jumeirah"], "purpose": "buy", "timeline": "exploring", "confidence": 0.9}}

Input: "Looking for studio to rent around 50K yearly"
Output: {{"property_type": "studio", "bedrooms": 0, "budget": {{"min": 45000, "max": 55000, "currency": "AED", "confidence": 0.8}}, "purpose": "rent", "timeline": "exploring", "confidence": 0.85}}

Input: "Need 2BR apartment with sea view ASAP"
Output: {{"property_type": "apartment", "bedrooms": 2, "must_haves": ["sea view"], "timeline": "urgent", "confidence": 0.75}}

Return ONLY valid JSON."""

        try:
            response = await openai_service.client.chat.completions.create(
                model=openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a Dubai real estate data extraction specialist. Extract property requirements and return structured JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temp for structured extraction
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            # Track cost
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=openai_service.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone or "unknown",
                intent="property_extraction"
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Parse to PropertyRequirements
            requirements = PropertyRequirements(
                property_type=PropertyType(result["property_type"]) if result.get("property_type") else None,
                bedrooms=result.get("bedrooms"),
                bathrooms=result.get("bathrooms"),
                size_sqft=result.get("size_sqft"),
                budget=BudgetRange(**result["budget"]) if result.get("budget") else None,
                locations=result.get("locations", []),
                must_haves=result.get("must_haves", []),
                nice_to_haves=result.get("nice_to_haves", []),
                timeline=Timeline(result.get("timeline", "not_mentioned")),
                purpose=Purpose(result.get("purpose", "buy")),
                confidence=result.get("confidence", 0.5),
                raw_message=message
            )
            
            return requirements
            
        except Exception as e:
            print(f"❌ AI extraction error: {e}")
            raise
    
    def _rule_based_extraction(self, message: str) -> PropertyRequirements:
        """Fallback rule-based extraction"""
        message_lower = message.lower()
        
        # Extract property type
        property_type = None
        for ptype in PropertyType:
            if ptype.value in message_lower:
                property_type = ptype
                break
        
        # Check aliases
        if not property_type:
            for alias, ptype in self.property_aliases.items():
                if alias in message_lower:
                    property_type = ptype
                    break
        
        # Extract bedrooms
        bedrooms = None
        bedroom_patterns = [
            r'(\d+)\s*(?:bed|br|bedroom)',
            r'(\d+)br\b',
            r'studio'
        ]
        for pattern in bedroom_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if 'studio' in pattern:
                    bedrooms = 0
                    property_type = PropertyType.STUDIO
                else:
                    bedrooms = int(match.group(1))
                break
        
        # Extract bathrooms
        bathrooms = None
        bathroom_match = re.search(r'(\d+)\s*(?:bath|bathroom)', message_lower)
        if bathroom_match:
            bathrooms = int(bathroom_match.group(1))
        
        # Extract size
        size_sqft = None
        size_patterns = [
            r'(\d+(?:,\d{3})*)\s*(?:sq\s*ft|sqft|square\s*feet)',
            r'(\d+(?:,\d{3})*)\s*sqm'  # Convert sqm to sqft
        ]
        for pattern in size_patterns:
            match = re.search(pattern, message_lower)
            if match:
                size_str = match.group(1).replace(',', '')
                size = float(size_str)
                
                if 'sqm' in pattern:
                    size = size * 10.764  # Convert sqm to sqft
                
                size_sqft = int(size)
                break
        
        # Extract budget
        budget = self._extract_budget(message_lower)
        
        # Extract locations
        locations = []
        for tier, areas in self.dubai_areas.items():
            for area in areas:
                if area.lower() in message_lower:
                    if area not in locations:
                        locations.append(area)
        
        # Extract must-haves
        must_haves = []
        amenities = [
            "sea view", "beach access", "pool", "gym", "parking",
            "maid room", "balcony", "garden", "terrace", "marina view",
            "golf course", "security", "concierge", "elevator"
        ]
        for amenity in amenities:
            if amenity in message_lower:
                must_haves.append(amenity)
        
        # Extract timeline
        timeline = Timeline.NOT_MENTIONED
        if any(word in message_lower for word in ['urgent', 'asap', 'immediately', 'now', 'today']):
            timeline = Timeline.URGENT
        elif any(word in message_lower for word in ['this month', 'soon', 'within month']):
            timeline = Timeline.ONE_MONTH
        elif any(word in message_lower for word in ['3 months', 'three months', 'quarter']):
            timeline = Timeline.THREE_MONTHS
        elif any(word in message_lower for word in ['exploring', 'looking', 'interested']):
            timeline = Timeline.EXPLORING
        
        # Extract purpose
        purpose = Purpose.BUY
        if any(word in message_lower for word in ['rent', 'rental', 'lease', 'renting']):
            purpose = Purpose.RENT
        elif any(word in message_lower for word in ['invest', 'investment', 'roi']):
            purpose = Purpose.INVEST
        elif any(word in message_lower for word in ['sell', 'selling']):
            purpose = Purpose.SELL
        
        # Calculate confidence
        confidence = 0.0
        if property_type: confidence += 0.25
        if bedrooms is not None: confidence += 0.20
        if budget: confidence += 0.25
        if locations: confidence += 0.15
        if must_haves: confidence += 0.10
        if timeline != Timeline.NOT_MENTIONED: confidence += 0.05
        
        return PropertyRequirements(
            property_type=property_type,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            size_sqft=size_sqft,
            budget=budget,
            locations=locations,
            must_haves=must_haves,
            timeline=timeline,
            purpose=purpose,
            confidence=min(confidence, 1.0),
            raw_message=message
        )
    
    def _extract_budget(self, message: str) -> Optional[BudgetRange]:
        """Extract budget from message"""
        
        # Pattern 1: "10-12 million"
        range_pattern = r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:million|m|mil)'
        match = re.search(range_pattern, message)
        if match:
            min_val = float(match.group(1)) * 1_000_000
            max_val = float(match.group(2)) * 1_000_000
            return BudgetRange(min=min_val, max=max_val, currency="AED", confidence=0.9)
        
        # Pattern 2: "around 5 million"
        around_pattern = r'(?:around|about|approximately)\s*(\d+(?:\.\d+)?)\s*(?:million|m|mil)'
        match = re.search(around_pattern, message)
        if match:
            val = float(match.group(1)) * 1_000_000
            return BudgetRange(min=val * 0.9, max=val * 1.1, currency="AED", confidence=0.7)
        
        # Pattern 3: "5 million"
        single_pattern = r'(\d+(?:\.\d+)?)\s*(?:million|m|mil)'
        match = re.search(single_pattern, message)
        if match:
            val = float(match.group(1)) * 1_000_000
            return BudgetRange(min=val, max=val * 1.2, currency="AED", confidence=0.6)
        
        # Pattern 4: "50K" (for rent)
        k_pattern = r'(\d+)\s*k\b'
        match = re.search(k_pattern, message)
        if match and any(word in message for word in ['rent', 'rental', 'lease']):
            val = float(match.group(1)) * 1_000
            return BudgetRange(min=val * 0.9, max=val * 1.1, currency="AED", confidence=0.7)
        
        # Pattern 5: Exact number "5000000"
        exact_pattern = r'\b(\d{6,})\b'
        match = re.search(exact_pattern, message)
        if match:
            val = float(match.group(1))
            if val >= 100_000:  # Reasonable property price
                return BudgetRange(min=val, max=val * 1.1, currency="AED", confidence=0.5)
        
        return None
    
    def get_price_range_for_property(
        self,
        property_type: PropertyType,
        bedrooms: Optional[int] = None,
        location_tier: str = "luxury"
    ) -> Tuple[float, float]:
        """Get typical price range for property specifications"""
        
        if property_type == PropertyType.STUDIO:
            base = self.price_ranges[PropertyType.STUDIO]
        elif property_type in [PropertyType.APARTMENT, PropertyType.VILLA, PropertyType.PENTHOUSE]:
            if bedrooms and bedrooms in self.price_ranges.get(property_type, {}):
                base = self.price_ranges[property_type][bedrooms]
            else:
                base = (1_000_000, 5_000_000)  # Default
        else:
            base = (1_000_000, 10_000_000)  # Generic default
        
        # Adjust for location tier
        multipliers = {
            "ultra_luxury": 2.0,
            "luxury": 1.3,
            "premium": 1.0,
            "affordable": 0.6
        }
        
        multiplier = multipliers.get(location_tier, 1.0)
        
        return (base[0] * multiplier, base[1] * multiplier)


# Global instance
property_intelligence_service = PropertyIntelligenceService()