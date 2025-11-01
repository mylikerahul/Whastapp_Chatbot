"""
💰 Lead Qualification Engine - BANT Scoring for Real Estate
Identifies hot leads and prioritizes follow-up actions
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

from services.property_intelligence import PropertyRequirements, Timeline, Purpose

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class LeadType(str, Enum):
    HOT = "hot"              # Score 80-100 - Immediate action
    WARM = "warm"            # Score 50-79 - Priority follow-up
    COLD = "cold"            # Score 25-49 - Nurture campaign
    UNQUALIFIED = "unqualified"  # Score 0-24 - Needs more info

class LeadPriority(str, Enum):
    CRITICAL = "critical"    # VIP + Hot
    URGENT = "urgent"        # Hot lead
    HIGH = "high"            # Warm lead
    MEDIUM = "medium"        # Cold lead
    LOW = "low"              # Unqualified

class AgentType(str, Enum):
    SENIOR_SPECIALIST = "senior_specialist"  # Luxury properties, VIP clients
    SPECIALIST = "specialist"                 # Standard properties
    GENERAL = "general"                       # Initial qualification
    LEASING = "leasing"                       # Rental properties
    COMMERCIAL = "commercial"                 # Commercial properties

class BANTScore(BaseModel):
    budget_score: int = 0      # 0-30 points
    authority_score: int = 0   # 0-25 points
    need_score: int = 0        # 0-25 points
    timeline_score: int = 0    # 0-20 points
    total_score: int = 0       # 0-100
    lead_type: LeadType = LeadType.UNQUALIFIED
    lead_priority: LeadPriority = LeadPriority.LOW
    reasoning: List[str] = []
    recommended_agent: AgentType = AgentType.GENERAL
    calculated_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.calculated_at:
            self.calculated_at = datetime.now()

class LeadAction(BaseModel):
    action: str
    priority: LeadPriority
    suggested_sla_hours: int
    agent_type: AgentType
    message: str
    next_steps: List[str]
    escalate: bool = False

# ==========================================
# LEAD QUALIFICATION SERVICE
# ==========================================

class LeadQualifier:
    """BANT-based lead scoring for Dubai real estate"""
    
    def __init__(self):
        # Timeline scoring matrix
        self.timeline_scores = {
            Timeline.URGENT: 20,
            Timeline.ONE_MONTH: 15,
            Timeline.THREE_MONTHS: 10,
            Timeline.SIX_MONTHS: 5,
            Timeline.EXPLORING: 2,
            Timeline.NOT_MENTIONED: 0
        }
        
        # Budget thresholds for tier classification
        self.budget_tiers = {
            "ultra_luxury": 20_000_000,  # 20M+ AED
            "luxury": 5_000_000,         # 5M-20M AED
            "premium": 1_500_000,        # 1.5M-5M AED
            "standard": 500_000,         # 500K-1.5M AED
            "affordable": 0              # <500K AED
        }
    
    def qualify_lead(
        self,
        property_requirements: PropertyRequirements,
        conversation_context: Optional[Dict] = None,
        is_vip: bool = False,
        sentiment_score: Optional[float] = None
    ) -> BANTScore:
        """
        Calculate BANT score based on property requirements
        
        BANT Framework:
        - Budget (30 pts): Has clear budget? Can afford target property?
        - Authority (25 pts): Decision maker? Investor? End user?
        - Need (25 pts): Clear requirements? Specific needs?
        - Timeline (20 pts): When are they buying/renting?
        
        Args:
            property_requirements: Extracted property requirements
            conversation_context: Additional conversation data
            is_vip: Is this a VIP client?
            sentiment_score: Sentiment analysis score
        
        Returns:
            BANTScore with detailed breakdown
        """
        
        reasoning = []
        
        # 1. BUDGET SCORING (0-30 points)
        budget_score = self._score_budget(property_requirements, reasoning)
        
        # 2. AUTHORITY SCORING (0-25 points)
        authority_score = self._score_authority(
            property_requirements, 
            conversation_context, 
            is_vip,
            reasoning
        )
        
        # 3. NEED SCORING (0-25 points)
        need_score = self._score_need(property_requirements, reasoning)
        
        # 4. TIMELINE SCORING (0-20 points)
        timeline_score = self.timeline_scores.get(property_requirements.timeline, 0)
        if timeline_score > 0:
            reasoning.append(f"Timeline: {property_requirements.timeline.value} (+{timeline_score}pts)")
        
        # CALCULATE TOTAL
        total_score = budget_score + authority_score + need_score + timeline_score
        
        # BONUS: VIP boost
        if is_vip:
            bonus = min(10, 100 - total_score)  # Max 10 bonus points
            total_score += bonus
            reasoning.append(f"VIP Client Bonus (+{bonus}pts)")
        
        # BONUS: Negative sentiment penalty
        if sentiment_score and sentiment_score < -0.5:
            penalty = 5
            total_score = max(0, total_score - penalty)
            reasoning.append(f"Frustrated customer penalty (-{penalty}pts)")
        
        # Classify lead type
        if total_score >= 80:
            lead_type = LeadType.HOT
            lead_priority = LeadPriority.URGENT
        elif total_score >= 50:
            lead_type = LeadType.WARM
            lead_priority = LeadPriority.HIGH
        elif total_score >= 25:
            lead_type = LeadType.COLD
            lead_priority = LeadPriority.MEDIUM
        else:
            lead_type = LeadType.UNQUALIFIED
            lead_priority = LeadPriority.LOW
        
        # VIP critical priority
        if is_vip and lead_type in [LeadType.HOT, LeadType.WARM]:
            lead_priority = LeadPriority.CRITICAL
        
        # Recommend agent type
        recommended_agent = self._recommend_agent(property_requirements, total_score, is_vip)
        
        print(f"📊 Lead Score: {total_score}/100 | Type: {lead_type.value.upper()} | Priority: {lead_priority.value.upper()}")
        print(f"   B:{budget_score} A:{authority_score} N:{need_score} T:{timeline_score}")
        
        return BANTScore(
            budget_score=budget_score,
            authority_score=authority_score,
            need_score=need_score,
            timeline_score=timeline_score,
            total_score=total_score,
            lead_type=lead_type,
            lead_priority=lead_priority,
            reasoning=reasoning,
            recommended_agent=recommended_agent
        )
    
    def _score_budget(self, req: PropertyRequirements, reasoning: List[str]) -> int:
        """Score budget clarity and feasibility (0-30 points)"""
        score = 0
        
        if not req.budget or not req.budget.min:
            reasoning.append("Budget: Not mentioned (0pts)")
            return 0
        
        # Budget clarity (0-15 points)
        if req.budget.confidence >= 0.9:
            score += 15
            reasoning.append("Budget: Very clear (+15pts)")
        elif req.budget.confidence >= 0.7:
            score += 12
            reasoning.append("Budget: Clear (+12pts)")
        elif req.budget.confidence >= 0.5:
            score += 8
            reasoning.append("Budget: Mentioned (+8pts)")
        else:
            score += 4
            reasoning.append("Budget: Vague (+4pts)")
        
        # Budget adequacy (0-15 points)
        if req.property_type and req.bedrooms is not None:
            from services.property_intelligence import property_intelligence_service
            
            # Get typical price range
            typical_min, typical_max = property_intelligence_service.get_price_range_for_property(
                req.property_type,
                req.bedrooms,
                "luxury"  # Default assumption for Dubai
            )
            
            budget_min = req.budget.min
            
            # Check if budget is realistic
            if budget_min >= typical_min:
                score += 15
                reasoning.append("Budget: Adequate for requirements (+15pts)")
            elif budget_min >= typical_min * 0.7:
                score += 10
                reasoning.append("Budget: Slightly below market (+10pts)")
            elif budget_min >= typical_min * 0.5:
                score += 5
                reasoning.append("Budget: Below market (+5pts)")
            else:
                score += 2
                reasoning.append("Budget: Significantly below market (+2pts)")
        else:
            # No property details to compare
            if req.budget.min >= 5_000_000:
                score += 15
                reasoning.append("Budget: High value (5M+) (+15pts)")
            elif req.budget.min >= 2_000_000:
                score += 12
                reasoning.append("Budget: Good value (2M+) (+12pts)")
            elif req.budget.min >= 1_000_000:
                score += 8
                reasoning.append("Budget: Standard (1M+) (+8pts)")
            else:
                score += 5
                reasoning.append("Budget: Entry level (+5pts)")
        
        return min(score, 30)
    
    def _score_authority(
        self,
        req: PropertyRequirements,
        context: Optional[Dict],
        is_vip: bool,
        reasoning: List[str]
    ) -> int:
        """Score decision-making authority (0-25 points)"""
        score = 0
        message_lower = req.raw_message.lower()
        
        # Direct decision maker indicators (0-15 points)
        if any(phrase in message_lower for phrase in ['i am buying', 'i want to buy', 'i need', 'i am looking']):
            score += 15
            reasoning.append("Authority: Direct buyer (+15pts)")
        elif any(phrase in message_lower for phrase in ['we are', 'we want', 'my family', 'our family']):
            score += 12
            reasoning.append("Authority: Family decision (+12pts)")
        elif any(phrase in message_lower for phrase in ['my client', 'on behalf', 'representing']):
            score += 6
            reasoning.append("Authority: Agent/Representative (+6pts)")
        else:
            score += 10
            reasoning.append("Authority: Assumed buyer (+10pts)")
        
        # Investor/High authority indicators (0-10 points)
        if any(word in message_lower for word in ['investor', 'investment', 'portfolio', 'roi']):
            score += 10
            reasoning.append("Authority: Investor profile (+10pts)")
        elif any(word in message_lower for word in ['cash buyer', 'cash payment', 'full payment']):
            score += 8
            reasoning.append("Authority: Cash buyer (+8pts)")
        elif req.purpose == Purpose.INVEST:
            score += 7
            reasoning.append("Authority: Investment intent (+7pts)")
        
        # VIP authority boost
        if is_vip:
            # Already handled in main score, just note it
            pass
        
        return min(score, 25)
    
    def _score_need(self, req: PropertyRequirements, reasoning: List[str]) -> int:
        """Score clarity and strength of need (0-25 points)"""
        score = 0
        
        # Specific property type (0-8 points)
        if req.property_type:
            score += 8
            reasoning.append(f"Need: Specific type ({req.property_type.value}) (+8pts)")
        else:
            score += 2
            reasoning.append("Need: Type not specified (+2pts)")
        
        # Bedroom requirement (0-7 points)
        if req.bedrooms is not None:
            score += 7
            reasoning.append(f"Need: Specific size ({req.bedrooms}BR) (+7pts)")
        
        # Location preference (0-5 points)
        if req.locations:
            score += 5
            reasoning.append(f"Need: Location(s) specified ({len(req.locations)}) (+5pts)")
        
        # Must-haves (0-5 points)
        if req.must_haves:
            points = min(5, len(req.must_haves))
            score += points
            reasoning.append(f"Need: {len(req.must_haves)} must-haves (+{points}pts)")
        
        return min(score, 25)
    
    def _recommend_agent(
        self,
        req: PropertyRequirements,
        total_score: int,
        is_vip: bool
    ) -> AgentType:
        """Recommend agent type based on lead profile"""
        
        # VIP always gets senior specialist
        if is_vip:
            return AgentType.SENIOR_SPECIALIST
        
        # Commercial properties
        if req.property_type in ['office', 'retail', 'warehouse']:
            return AgentType.COMMERCIAL
        
        # Rental/leasing
        if req.purpose == Purpose.RENT:
            return AgentType.LEASING
        
        # Luxury properties (20M+)
        if req.budget and req.budget.min and req.budget.min >= 20_000_000:
            return AgentType.SENIOR_SPECIALIST
        
        # High-value properties (5M+) or hot leads
        if (req.budget and req.budget.min and req.budget.min >= 5_000_000) or total_score >= 70:
            return AgentType.SPECIALIST
        
        # Standard
        return AgentType.GENERAL
    
    def recommend_action(self, bant_score: BANTScore, is_vip: bool = False) -> LeadAction:
        """Recommend next steps based on lead score"""
        
        # CRITICAL (VIP Hot/Warm)
        if bant_score.lead_priority == LeadPriority.CRITICAL:
            return LeadAction(
                action="immediate_vip_callback",
                priority=LeadPriority.CRITICAL,
                suggested_sla_hours=0.5,  # 30 minutes
                agent_type=bant_score.recommended_agent,
                message="🔥🌟 CRITICAL: VIP Hot Lead - Immediate senior specialist callback required",
                next_steps=[
                    "Assign to senior specialist immediately",
                    "Call within 30 minutes",
                    "Send luxury property portfolio via WhatsApp",
                    "Schedule viewing within 24 hours",
                    "Flag in CRM as VIP priority"
                ],
                escalate=True
            )
        
        # HOT LEAD
        elif bant_score.lead_type == LeadType.HOT:
            return LeadAction(
                action="immediate_callback",
                priority=LeadPriority.URGENT,
                suggested_sla_hours=1,
                agent_type=bant_score.recommended_agent,
                message="🔥 HOT LEAD - Immediate callback required within 1 hour",
                next_steps=[
                    f"Assign to {bant_score.recommended_agent.value}",
                    "Call within 1 hour",
                    "Send property matches via WhatsApp",
                    "Schedule viewing within 48 hours",
                    "Send personalized follow-up"
                ],
                escalate=is_vip
            )
        
        # WARM LEAD
        elif bant_score.lead_type == LeadType.WARM:
            return LeadAction(
                action="priority_callback",
                priority=LeadPriority.HIGH,
                suggested_sla_hours=4,
                agent_type=bant_score.recommended_agent,
                message="🌟 WARM LEAD - Priority callback within 4 hours",
                next_steps=[
                    f"Assign to {bant_score.recommended_agent.value}",
                    "Call/WhatsApp within 4 hours",
                    "Send property recommendations",
                    "Qualify budget and timeline further",
                    "Schedule viewing if interested"
                ],
                escalate=False
            )
        
        # COLD LEAD
        elif bant_score.lead_type == LeadType.COLD:
            return LeadAction(
                action="nurture_campaign",
                priority=LeadPriority.MEDIUM,
                suggested_sla_hours=24,
                agent_type=AgentType.GENERAL,
                message="📧 COLD LEAD - Add to nurture campaign",
                next_steps=[
                    "Add to email nurture sequence",
                    "Send WhatsApp follow-up within 24 hours",
                    "Share market insights and new listings",
                    "Schedule callback in 1 week",
                    "Track engagement with automated messages"
                ],
                escalate=False
            )
        
        # UNQUALIFIED
        else:
            return LeadAction(
                action="gather_information",
                priority=LeadPriority.LOW,
                suggested_sla_hours=48,
                agent_type=AgentType.GENERAL,
                message="❓ UNQUALIFIED - Gather more information",
                next_steps=[
                    "Send automated qualification questions via WhatsApp",
                    "Ask about budget, timeline, and requirements",
                    "Share general property guide",
                    "Follow up in 2-3 days",
                    "Re-qualify after additional information"
                ],
                escalate=False
            )
    
    def get_budget_tier(self, budget: Optional[float]) -> str:
        """Get budget tier classification"""
        if not budget:
            return "unknown"
        
        if budget >= self.budget_tiers["ultra_luxury"]:
            return "ultra_luxury"
        elif budget >= self.budget_tiers["luxury"]:
            return "luxury"
        elif budget >= self.budget_tiers["premium"]:
            return "premium"
        elif budget >= self.budget_tiers["standard"]:
            return "standard"
        else:
            return "affordable"


# Global instance
lead_qualifier = LeadQualifier()