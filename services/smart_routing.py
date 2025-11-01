"""
🎯 Smart Agent Routing Service
Intelligent lead assignment based on property type, budget, expertise, and availability
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, time, timedelta
from collections import defaultdict
import random

from services.property_intelligence import PropertyRequirements, PropertyType, Purpose
from services.lead_qualifier import BANTScore, LeadType, AgentType

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ON_BREAK = "on_break"

class Specialization(str, Enum):
    LUXURY_VILLAS = "luxury_villas"
    LUXURY_APARTMENTS = "luxury_apartments"
    COMMERCIAL = "commercial"
    LEASING = "leasing"
    INVESTMENT = "investment"
    OFF_PLAN = "off_plan"
    AFFORDABLE = "affordable"
    GENERAL = "general"

class RoutingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    SKILL_BASED = "skill_based"
    LOAD_BALANCED = "load_balanced"
    PRIORITY_BASED = "priority_based"

class Agent(BaseModel):
    agent_id: str
    name: str
    email: str
    phone: str
    type: AgentType
    specializations: List[Specialization]
    languages: List[str] = ["en"]
    
    # Expertise
    min_budget_handled: int = 0
    max_budget_handled: int = 100_000_000
    preferred_areas: List[str] = []
    property_types: List[PropertyType] = []
    
    # Availability
    status: AgentStatus = AgentStatus.AVAILABLE
    working_hours_start: time = time(9, 0)
    working_hours_end: time = time(18, 0)
    working_days: List[int] = [0, 1, 2, 3, 4]  # Mon-Fri (0=Monday)
    timezone: str = "Asia/Dubai"
    
    # Performance metrics
    active_leads: int = 0
    max_concurrent_leads: int = 20
    total_deals_closed: int = 0
    average_response_time_minutes: int = 30
    success_rate: float = 0.0
    
    # Contact preferences
    preferred_contact_method: str = "whatsapp"
    auto_assign: bool = True

class RoutingResult(BaseModel):
    assigned_agent: Agent
    routing_strategy: RoutingStrategy
    confidence: float
    reasoning: List[str]
    alternative_agents: List[Agent] = []
    escalated: bool = False
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()

class RoutingRule(BaseModel):
    name: str
    priority: int  # Higher = more important
    condition: str  # Description
    weight: float = 1.0

# ==========================================
# SMART ROUTING SERVICE
# ==========================================

class SmartRoutingService:
    """
    Intelligent agent routing for Dubai real estate leads
    """
    
    def __init__(self):
        # Agent registry
        self._agents: Dict[str, Agent] = {}
        
        # Round-robin tracking
        self._round_robin_index: Dict[str, int] = defaultdict(int)
        
        # Routing rules
        self._routing_rules = self._initialize_routing_rules()
        
        # Assignment history (for analytics)
        self._assignment_history: List[Dict] = []
        
        # Initialize default agents
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agent pool"""
        
        # Senior Luxury Specialist
        self.register_agent(Agent(
            agent_id="agent_001",
            name="Ahmed Al Mansouri",
            email="ahmed.mansouri@sothebysrealty.ae",
            phone="+971501234567",
            type=AgentType.SENIOR_SPECIALIST,
            specializations=[
                Specialization.LUXURY_VILLAS,
                Specialization.LUXURY_APARTMENTS,
                Specialization.INVESTMENT
            ],
            languages=["en", "ar"],
            min_budget_handled=10_000_000,
            max_budget_handled=200_000_000,
            preferred_areas=["Palm Jumeirah", "Emirates Hills", "Jumeirah Bay Island"],
            property_types=[PropertyType.VILLA, PropertyType.PENTHOUSE],
            max_concurrent_leads=10,
            total_deals_closed=150,
            success_rate=0.85
        ))
        
        # Luxury Apartment Specialist
        self.register_agent(Agent(
            agent_id="agent_002",
            name="Sarah Johnson",
            email="sarah.johnson@sothebysrealty.ae",
            phone="+971509876543",
            type=AgentType.SPECIALIST,
            specializations=[
                Specialization.LUXURY_APARTMENTS,
                Specialization.OFF_PLAN
            ],
            languages=["en"],
            min_budget_handled=2_000_000,
            max_budget_handled=20_000_000,
            preferred_areas=["Dubai Marina", "Downtown Dubai", "Business Bay"],
            property_types=[PropertyType.APARTMENT, PropertyType.PENTHOUSE],
            max_concurrent_leads=15,
            total_deals_closed=95,
            success_rate=0.78
        ))
        
        # Leasing Specialist
        self.register_agent(Agent(
            agent_id="agent_003",
            name="Mohammed Hassan",
            email="mohammed.hassan@sothebysrealty.ae",
            phone="+971505555555",
            type=AgentType.LEASING,
            specializations=[
                Specialization.LEASING,
                Specialization.AFFORDABLE
            ],
            languages=["en", "ar"],
            min_budget_handled=30_000,
            max_budget_handled=500_000,
            preferred_areas=["JVC", "Dubai Marina", "JBR", "Business Bay"],
            property_types=[PropertyType.APARTMENT, PropertyType.STUDIO],
            max_concurrent_leads=25,
            total_deals_closed=220,
            success_rate=0.82
        ))
        
        # Commercial Specialist
        self.register_agent(Agent(
            agent_id="agent_004",
            name="Fatima Al Hashimi",
            email="fatima.hashimi@sothebysrealty.ae",
            phone="+971507777777",
            type=AgentType.COMMERCIAL,
            specializations=[
                Specialization.COMMERCIAL,
                Specialization.INVESTMENT
            ],
            languages=["en", "ar"],
            min_budget_handled=1_000_000,
            max_budget_handled=100_000_000,
            preferred_areas=["Business Bay", "DIFC", "Dubai Marina"],
            property_types=[PropertyType.OFFICE, PropertyType.RETAIL],
            max_concurrent_leads=12,
            total_deals_closed=75,
            success_rate=0.88
        ))
        
        # General Agent (Backup)
        self.register_agent(Agent(
            agent_id="agent_005",
            name="General Support Team",
            email="support@sothebysrealty.ae",
            phone="+971504444444",
            type=AgentType.GENERAL,
            specializations=[Specialization.GENERAL],
            languages=["en", "ar"],
            min_budget_handled=0,
            max_budget_handled=10_000_000,
            property_types=list(PropertyType),
            max_concurrent_leads=50,
            total_deals_closed=45,
            success_rate=0.65
        ))
        
        print(f"✅ Initialized {len(self._agents)} default agents")
    
    def _initialize_routing_rules(self) -> List[RoutingRule]:
        """Initialize routing rules with priorities"""
        
        return [
            RoutingRule(
                name="VIP Priority",
                priority=100,
                condition="VIP clients get senior specialists",
                weight=2.0
            ),
            RoutingRule(
                name="Ultra Luxury Budget",
                priority=90,
                condition="Budget > 20M AED gets senior specialist",
                weight=1.8
            ),
            RoutingRule(
                name="Commercial Properties",
                priority=85,
                condition="Commercial properties go to commercial team",
                weight=1.5
            ),
            RoutingRule(
                name="Leasing/Rental",
                priority=80,
                condition="Rental inquiries go to leasing team",
                weight=1.3
            ),
            RoutingRule(
                name="Language Match",
                priority=75,
                condition="Match agent language with user preference",
                weight=1.2
            ),
            RoutingRule(
                name="Budget Match",
                priority=70,
                condition="Match agent expertise with budget",
                weight=1.5
            ),
            RoutingRule(
                name="Area Expertise",
                priority=65,
                condition="Match agent area expertise",
                weight=1.1
            ),
            RoutingRule(
                name="Property Type Match",
                priority=60,
                condition="Match agent property type expertise",
                weight=1.2
            ),
            RoutingRule(
                name="Lead Score",
                priority=55,
                condition="Hot leads get specialists",
                weight=1.3
            ),
            RoutingRule(
                name="Availability",
                priority=50,
                condition="Agent must be available",
                weight=1.0
            ),
            RoutingRule(
                name="Load Balancing",
                priority=40,
                condition="Distribute leads evenly",
                weight=0.8
            ),
            RoutingRule(
                name="Working Hours",
                priority=35,
                condition="Respect agent working hours",
                weight=0.9
            )
        ]
    
    # ==========================================
    # AGENT MANAGEMENT
    # ==========================================
    
    def register_agent(self, agent: Agent):
        """Register a new agent"""
        self._agents[agent.agent_id] = agent
        print(f"✅ Agent registered: {agent.name} ({agent.type.value})")
    
    def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus
    ):
        """Update agent availability status"""
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            print(f"🔄 Agent {agent_id} status: {status.value}")
    
    def update_agent_load(
        self,
        agent_id: str,
        active_leads: int
    ):
        """Update agent's active lead count"""
        if agent_id in self._agents:
            self._agents[agent_id].active_leads = active_leads
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self._agents.values())
    
    def get_available_agents(self) -> List[Agent]:
        """Get currently available agents"""
        return [
            agent for agent in self._agents.values()
            if agent.status == AgentStatus.AVAILABLE
            and agent.auto_assign
            and agent.active_leads < agent.max_concurrent_leads
        ]
    
    # ==========================================
    # SMART ROUTING LOGIC
    # ==========================================
    
    def route_lead(
        self,
        property_requirements: Optional[PropertyRequirements] = None,
        bant_score: Optional[BANTScore] = None,
        is_vip: bool = False,
        user_language: str = "en",
        preferred_agent_id: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.SKILL_BASED
    ) -> RoutingResult:
        """
        Route lead to best matching agent
        
        Args:
            property_requirements: Property search requirements
            bant_score: Lead qualification score
            is_vip: Is VIP client
            user_language: User's preferred language
            preferred_agent_id: Specific agent request
            strategy: Routing strategy to use
        
        Returns:
            RoutingResult with assigned agent
        """
        
        reasoning = []
        
        # If specific agent requested and available
        if preferred_agent_id and preferred_agent_id in self._agents:
            agent = self._agents[preferred_agent_id]
            if agent.status == AgentStatus.AVAILABLE:
                reasoning.append(f"User requested agent: {agent.name}")
                return RoutingResult(
                    assigned_agent=agent,
                    routing_strategy=strategy,
                    confidence=1.0,
                    reasoning=reasoning
                )
        
        # Get available agents
        available_agents = self.get_available_agents()
        
        if not available_agents:
            print("⚠️ No agents available, assigning to general team")
            # Fallback to general team even if busy
            general_agent = next(
                (a for a in self._agents.values() if a.type == AgentType.GENERAL),
                None
            )
            if general_agent:
                reasoning.append("No agents available - assigned to general team")
                return RoutingResult(
                    assigned_agent=general_agent,
                    routing_strategy=strategy,
                    confidence=0.5,
                    reasoning=reasoning,
                    escalated=True
                )
        
        # Route based on strategy
        if strategy == RoutingStrategy.SKILL_BASED:
            return self._skill_based_routing(
                available_agents,
                property_requirements,
                bant_score,
                is_vip,
                user_language
            )
        
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            return self._load_balanced_routing(
                available_agents,
                property_requirements,
                bant_score
            )
        
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return self._priority_based_routing(
                available_agents,
                is_vip,
                bant_score
            )
        
        else:  # ROUND_ROBIN
            return self._round_robin_routing(available_agents)
    
    def _skill_based_routing(
        self,
        agents: List[Agent],
        requirements: Optional[PropertyRequirements],
        bant_score: Optional[BANTScore],
        is_vip: bool,
        language: str
    ) -> RoutingResult:
        """Skill-based routing with scoring"""
        
        scored_agents = []
        reasoning = []
        
        for agent in agents:
            score = 0.0
            agent_reasoning = []
            
            # VIP handling (highest priority)
            if is_vip:
                if agent.type == AgentType.SENIOR_SPECIALIST:
                    score += 50
                    agent_reasoning.append("VIP → Senior specialist (+50)")
                else:
                    score -= 20
                    agent_reasoning.append("VIP needs senior specialist (-20)")
            
            # Budget matching
            if requirements and requirements.budget and requirements.budget.min:
                budget = requirements.budget.min
                
                if agent.min_budget_handled <= budget <= agent.max_budget_handled:
                    score += 30
                    agent_reasoning.append(f"Budget match ({budget:,} AED) (+30)")
                elif budget > agent.max_budget_handled:
                    score -= 15
                    agent_reasoning.append("Budget too high (-15)")
                elif budget < agent.min_budget_handled:
                    score -= 10
                    agent_reasoning.append("Budget below expertise (-10)")
            
            # Property type matching
            if requirements and requirements.property_type:
                ptype = requirements.property_type
                
                # Commercial properties
                if ptype in [PropertyType.OFFICE, PropertyType.RETAIL, PropertyType.WAREHOUSE]:
                    if Specialization.COMMERCIAL in agent.specializations:
                        score += 40
                        agent_reasoning.append("Commercial specialist (+40)")
                    else:
                        score -= 20
                        agent_reasoning.append("Not commercial specialist (-20)")
                
                # Match property type expertise
                elif ptype in agent.property_types:
                    score += 20
                    agent_reasoning.append(f"Property type match ({ptype.value}) (+20)")
            
            # Purpose matching (rent/buy)
            if requirements and requirements.purpose == Purpose.RENT:
                if agent.type == AgentType.LEASING or Specialization.LEASING in agent.specializations:
                    score += 25
                    agent_reasoning.append("Leasing specialist (+25)")
            
            # Area expertise
            if requirements and requirements.locations:
                matching_areas = set(requirements.locations) & set(agent.preferred_areas)
                if matching_areas:
                    score += len(matching_areas) * 10
                    agent_reasoning.append(f"Area expertise ({len(matching_areas)} matches) (+{len(matching_areas)*10})")
            
            # Language match
            if language in agent.languages:
                score += 15
                agent_reasoning.append(f"Language match ({language}) (+15)")
            
            # Lead score consideration
            if bant_score:
                if bant_score.lead_type == LeadType.HOT:
                    if agent.type in [AgentType.SENIOR_SPECIALIST, AgentType.SPECIALIST]:
                        score += 20
                        agent_reasoning.append("Hot lead → Specialist (+20)")
                elif bant_score.lead_type == LeadType.COLD:
                    if agent.type == AgentType.GENERAL:
                        score += 10
                        agent_reasoning.append("Cold lead → General agent (+10)")
            
            # Performance metrics
            score += agent.success_rate * 10
            agent_reasoning.append(f"Success rate {agent.success_rate*100:.0f}% (+{agent.success_rate*10:.1f})")
            
            # Load balancing penalty
            capacity_used = agent.active_leads / agent.max_concurrent_leads
            load_penalty = capacity_used * 15
            score -= load_penalty
            agent_reasoning.append(f"Load {capacity_used*100:.0f}% (-{load_penalty:.1f})")
            
            scored_agents.append({
                "agent": agent,
                "score": score,
                "reasoning": agent_reasoning
            })
        
        # Sort by score
        scored_agents.sort(key=lambda x: x["score"], reverse=True)
        
        # Best match
        best = scored_agents[0]
        
        # Escalation check
        escalated = False
        if is_vip and best["agent"].type != AgentType.SENIOR_SPECIALIST:
            escalated = True
            reasoning.append("⚠️ VIP lead but no senior specialist available - escalated")
        
        # Alternative agents (top 3)
        alternatives = [item["agent"] for item in scored_agents[1:4]]
        
        # Build reasoning
        reasoning.extend(best["reasoning"][:5])  # Top 5 reasons
        
        confidence = min(max(best["score"] / 100, 0.1), 1.0)
        
        print(f"🎯 Routed to: {best['agent'].name} (score: {best['score']:.1f})")
        
        return RoutingResult(
            assigned_agent=best["agent"],
            routing_strategy=RoutingStrategy.SKILL_BASED,
            confidence=confidence,
            reasoning=reasoning,
            alternative_agents=alternatives,
            escalated=escalated
        )
    
    def _load_balanced_routing(
        self,
        agents: List[Agent],
        requirements: Optional[PropertyRequirements],
        bant_score: Optional[BANTScore]
    ) -> RoutingResult:
        """Load-balanced routing - assign to least busy qualified agent"""
        
        # Filter qualified agents
        qualified = []
        
        for agent in agents:
            # Basic qualification
            qualified_agent = True
            
            # Check budget if available
            if requirements and requirements.budget and requirements.budget.min:
                budget = requirements.budget.min
                if not (agent.min_budget_handled <= budget <= agent.max_budget_handled):
                    qualified_agent = False
            
            # Check property type
            if requirements and requirements.property_type:
                if requirements.property_type in [PropertyType.OFFICE, PropertyType.RETAIL]:
                    if Specialization.COMMERCIAL not in agent.specializations:
                        qualified_agent = False
            
            if qualified_agent:
                qualified.append(agent)
        
        if not qualified:
            qualified = agents  # Fallback to all available
        
        # Sort by load (ascending)
        qualified.sort(key=lambda a: a.active_leads / a.max_concurrent_leads)
        
        best_agent = qualified[0]
        
        reasoning = [
            f"Load balanced: {best_agent.active_leads}/{best_agent.max_concurrent_leads} leads",
            f"Agent type: {best_agent.type.value}"
        ]
        
        return RoutingResult(
            assigned_agent=best_agent,
            routing_strategy=RoutingStrategy.LOAD_BALANCED,
            confidence=0.8,
            reasoning=reasoning
        )
    
    def _priority_based_routing(
        self,
        agents: List[Agent],
        is_vip: bool,
        bant_score: Optional[BANTScore]
    ) -> RoutingResult:
        """Priority-based routing - VIP and hot leads get priority"""
        
        # VIP gets senior specialist
        if is_vip:
            senior = next(
                (a for a in agents if a.type == AgentType.SENIOR_SPECIALIST),
                None
            )
            if senior:
                return RoutingResult(
                    assigned_agent=senior,
                    routing_strategy=RoutingStrategy.PRIORITY_BASED,
                    confidence=0.95,
                    reasoning=["VIP client → Senior specialist"]
                )
        
        # Hot leads get specialists
        if bant_score and bant_score.lead_type == LeadType.HOT:
            specialist = next(
                (a for a in agents if a.type in [AgentType.SENIOR_SPECIALIST, AgentType.SPECIALIST]),
                None
            )
            if specialist:
                return RoutingResult(
                    assigned_agent=specialist,
                    routing_strategy=RoutingStrategy.PRIORITY_BASED,
                    confidence=0.85,
                    reasoning=["Hot lead → Specialist"]
                )
        
        # Default to first available
        return RoutingResult(
            assigned_agent=agents[0],
            routing_strategy=RoutingStrategy.PRIORITY_BASED,
            confidence=0.7,
            reasoning=["Standard priority routing"]
        )
    
    def _round_robin_routing(
        self,
        agents: List[Agent]
    ) -> RoutingResult:
        """Simple round-robin routing"""
        
        # Get next index
        index = self._round_robin_index["default"] % len(agents)
        self._round_robin_index["default"] += 1
        
        selected_agent = agents[index]
        
        return RoutingResult(
            assigned_agent=selected_agent,
            routing_strategy=RoutingStrategy.ROUND_ROBIN,
            confidence=0.6,
            reasoning=[f"Round-robin assignment (index: {index})"]
        )
    
    # ==========================================
    # ESCALATION LOGIC
    # ==========================================
    
    def escalate_to_senior(
        self,
        current_agent_id: str,
        reason: str
    ) -> Optional[Agent]:
        """Escalate lead to senior specialist"""
        
        # Find available senior specialist
        senior = next(
            (
                agent for agent in self._agents.values()
                if agent.type == AgentType.SENIOR_SPECIALIST
                and agent.status == AgentStatus.AVAILABLE
                and agent.agent_id != current_agent_id
            ),
            None
        )
        
        if senior:
            print(f"⬆️ Escalated to: {senior.name} | Reason: {reason}")
            return senior
        
        return None
    
    # ==========================================
    # ANALYTICS & REPORTING
    # ==========================================
    
    def get_routing_stats(self) -> Dict:
        """Get routing statistics"""
        
        total_agents = len(self._agents)
        available_agents = len(self.get_available_agents())
        
        # Agent load distribution
        load_distribution = {
            agent.agent_id: {
                "name": agent.name,
                "type": agent.type.value,
                "active_leads": agent.active_leads,
                "capacity": agent.max_concurrent_leads,
                "utilization": f"{(agent.active_leads / agent.max_concurrent_leads) * 100:.1f}%"
            }
            for agent in self._agents.values()
        }
        
        # Assignments by strategy
        strategy_counts = defaultdict(int)
        for assignment in self._assignment_history[-100:]:  # Last 100
            strategy_counts[assignment.get("strategy", "unknown")] += 1
        
        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "utilization": f"{(available_agents / total_agents) * 100:.1f}%" if total_agents > 0 else "0%",
            "load_distribution": load_distribution,
            "recent_assignments": len(self._assignment_history),
            "strategy_usage": dict(strategy_counts)
        }
    
    def get_agent_performance(self, agent_id: str) -> Optional[Dict]:
        """Get agent performance metrics"""
        
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "type": agent.type.value,
            "specializations": [s.value for s in agent.specializations],
            "active_leads": agent.active_leads,
            "max_concurrent_leads": agent.max_concurrent_leads,
            "utilization": f"{(agent.active_leads / agent.max_concurrent_leads) * 100:.1f}%",
            "total_deals_closed": agent.total_deals_closed,
            "success_rate": f"{agent.success_rate * 100:.1f}%",
            "avg_response_time_minutes": agent.average_response_time_minutes,
            "status": agent.status.value
        }


# Global instance
smart_routing = SmartRoutingService()