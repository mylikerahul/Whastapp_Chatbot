"""
Data Models & Schemas - ENHANCED VERSION
Complete data models for Dubai real estate AI chatbot
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum

# ==========================================
# EXISTING ENUMS (Keep for backward compatibility)
# ==========================================

class IntentType(str, Enum):
    CREATE_TICKET = "create_ticket"
    CHECK_STATUS = "check_status"
    UPDATE_TICKET = "update_ticket"
    CLOSE_TICKET = "close_ticket"
    PROPERTY_INQUIRY = "property_inquiry"
    SCHEDULE_VIEWING = "schedule_viewing"
    GENERAL_INQUIRY = "general_inquiry"

class Priority(str, Enum):
    LOWEST = "Lowest"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    HIGHEST = "Highest"

# ==========================================
# NEW ENUMS - PROPERTY INTELLIGENCE
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
    URGENT = "urgent"
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

# ==========================================
# NEW ENUMS - LEAD QUALIFICATION
# ==========================================

class LeadType(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"

class LeadPriority(str, Enum):
    CRITICAL = "critical"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AgentType(str, Enum):
    SENIOR_SPECIALIST = "senior_specialist"
    SPECIALIST = "specialist"
    GENERAL = "general"
    LEASING = "leasing"
    COMMERCIAL = "commercial"

# ==========================================
# NEW ENUMS - CONVERSATION
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

# ==========================================
# NEW ENUMS - MULTILINGUAL
# ==========================================

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"
    MIXED = "mixed"

class TranslationQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ==========================================
# NEW ENUMS - ROUTING
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

# ==========================================
# EXISTING MODELS (Keep for backward compatibility)
# ==========================================

class WebhookMessage(BaseModel):
    messageId: str = Field(alias="messageId")
    type: str
    status: str
    from_number: Optional[str] = Field(None, alias="from")
    text: Optional[str] = None
    userName: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: Optional[int] = None

class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = {}
    ticket_key: Optional[str] = None
    priority: Optional[Priority] = None

class JiraProject(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    lead: Optional[str] = None

class TicketPreview(BaseModel):
    summary: str
    description: str
    project_key: str
    project_name: str
    team: str
    priority: Priority
    assignee: Optional[str] = None

class PendingTicket(BaseModel):
    user_phone: str
    user_name: str
    summary: str
    description: str
    team: str
    project_key: str
    priority: Priority = Priority.MEDIUM
    attachments: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    awaiting_confirmation: bool = True

class ConversationLog(BaseModel):
    message_id: str
    user_phone: str
    user_name: str
    message_type: str
    message_text: Optional[str]
    intent: Optional[str]
    confidence: Optional[float]
    response_sent: bool
    processing_time_ms: int
    estimated_cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    jira_ticket_key: Optional[str] = None

# ==========================================
# NEW MODELS - PROPERTY INTELLIGENCE
# ==========================================

class BudgetRange(BaseModel):
    """Budget range for property search"""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "AED"
    confidence: float = 0.0

class PropertyRequirements(BaseModel):
    """Structured property requirements extracted from conversation"""
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
    extracted_at: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.extracted_at:
            self.extracted_at = datetime.now()

# ==========================================
# NEW MODELS - LEAD QUALIFICATION
# ==========================================

class BANTScore(BaseModel):
    """BANT scoring for lead qualification"""
    budget_score: int = 0      # 0-30 points
    authority_score: int = 0   # 0-25 points
    need_score: int = 0        # 0-25 points
    timeline_score: int = 0    # 0-20 points
    total_score: int = 0       # 0-100
    lead_type: LeadType = LeadType.UNQUALIFIED
    lead_priority: LeadPriority = LeadPriority.LOW
    reasoning: List[str] = []
    recommended_agent: AgentType = AgentType.GENERAL
    calculated_at: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.calculated_at:
            self.calculated_at = datetime.now()

class LeadAction(BaseModel):
    """Recommended action for a lead"""
    action: str
    priority: LeadPriority
    suggested_sla_hours: int
    agent_type: AgentType
    message: str
    next_steps: List[str]
    escalate: bool = False

# ==========================================
# NEW MODELS - CONVERSATION MEMORY
# ==========================================

class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: MessageRole
    content: str
    timestamp: datetime
    intent: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = {}

class UserPreferences(BaseModel):
    """User preferences and settings"""
    preferred_language: str = "en"
    communication_style: str = "professional"
    preferred_contact_method: str = "whatsapp"
    timezone: str = "Asia/Dubai"
    marketing_consent: bool = False

class ConversationContext(BaseModel):
    """Complete conversation context and session state"""
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
# NEW MODELS - MULTILINGUAL
# ==========================================

class TranslationResult(BaseModel):
    """Translation result with metadata"""
    original_text: str
    translated_text: str
    source_language: Language
    target_language: Language
    confidence: float
    quality: TranslationQuality
    cached: bool = False
    timestamp: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()

# ==========================================
# NEW MODELS - SMART ROUTING
# ==========================================

class Agent(BaseModel):
    """Agent profile with expertise and availability"""
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
    working_hours_start: Optional[str] = "09:00"  # Changed from time to str for JSON serialization
    working_hours_end: Optional[str] = "18:00"
    working_days: List[int] = [0, 1, 2, 3, 4]  # Mon-Fri
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
    """Result of agent routing decision"""
    assigned_agent: Agent
    routing_strategy: RoutingStrategy
    confidence: float
    reasoning: List[str]
    alternative_agents: List[Agent] = []
    escalated: bool = False
    timestamp: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()

class RoutingRule(BaseModel):
    """Routing rule definition"""
    name: str
    priority: int
    condition: str
    weight: float = 1.0

# ==========================================
# NEW MODELS - DUBAI KNOWLEDGE
# ==========================================

class CommunityTier(str, Enum):
    ULTRA_LUXURY = "ultra_luxury"
    LUXURY = "luxury"
    PREMIUM = "premium"
    AFFORDABLE = "affordable"

class Community(BaseModel):
    """Dubai community/area information"""
    name: str
    tier: CommunityTier
    price_range_min: int
    price_range_max: int
    property_types: List[str]
    amenities: List[str]
    nearby_landmarks: List[str]
    coordinates: Optional[Tuple[float, float]] = None
    developer: Optional[str] = None
    handover_year: Optional[int] = None
    district: Optional[str] = None
    rental_yield: Optional[str] = None
    investment_score: Optional[int] = None
    family_friendly: bool = True
    beach_access: bool = False
    metro_access: bool = False

class MarketInsight(BaseModel):
    """Market insights for a community"""
    community: str
    avg_price_per_sqft: Optional[int] = None
    price_trend: str = "stable"
    demand_level: str = "medium"
    rental_yield: str = "5-7%"
    investment_potential: str = "medium"
    best_for: List[str] = []
    updated_at: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.updated_at:
            self.updated_at = datetime.now()

# ==========================================
# NEW MODELS - SENTIMENT ANALYSIS
# ==========================================

class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    sentiment: str  # positive, neutral, negative
    score: float  # -1.0 to 1.0
    urgency: int  # 0-10
    escalate: bool
    reason: str = ""
    indicators: Dict[str, Any] = {}

class FrustrationLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ==========================================
# NEW MODELS - VIP DETECTION
# ==========================================

class VIPTier(str, Enum):
    STANDARD = "standard"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class VIPProfile(BaseModel):
    """VIP client profile"""
    phone: str
    name: str
    tier: VIPTier
    registered_at: datetime
    total_transactions: int = 0
    total_value_aed: float = 0.0
    portfolio_size: int = 0
    preferred_agent: Optional[str] = None
    notes: str = ""
    metadata: Dict[str, Any] = {}

class VIPDetectionResult(BaseModel):
    """VIP detection result"""
    is_vip: bool
    vip_tier: VIPTier = VIPTier.STANDARD
    confidence: float
    indicators: List[str]
    auto_escalate: bool
    vip_name: Optional[str] = None

# ==========================================
# NEW MODELS - ANALYTICS
# ==========================================

class AnalyticsMetrics(BaseModel):
    """Real-time analytics metrics"""
    timestamp: datetime
    messages_processed: int = 0
    tickets_created: int = 0
    tickets_resolved: int = 0
    vip_interactions: int = 0
    escalations: int = 0
    average_response_time_ms: int = 0
    active_users: int = 0
    error_rate: float = 0.0

class CostSummary(BaseModel):
    """Cost tracking summary"""
    date: str
    openai_cost: float = 0.0
    gallabox_cost: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    total_messages: int = 0
    avg_cost_per_message: float = 0.0

# ==========================================
# NEW MODELS - ENHANCED PROMPTS
# ==========================================

class PromptCategory(str, Enum):
    INTENT_CLASSIFICATION = "intent_classification"
    PROPERTY_EXTRACTION = "property_extraction"
    LEAD_QUALIFICATION = "lead_qualification"
    RESPONSE_GENERATION = "response_generation"
    TRANSLATION = "translation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TICKET_GENERATION = "ticket_generation"

class PromptTemplate(BaseModel):
    """Prompt template definition"""
    category: PromptCategory
    system_prompt: str
    user_template: str
    examples: List[Dict[str, str]] = []
    variables: List[str] = []

# ==========================================
# UTILITY MODELS
# ==========================================

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    metrics: Optional[Dict[str, Any]] = None

class SessionSummary(BaseModel):
    """Conversation session summary"""
    conversation_id: str
    user_phone: str
    user_name: str
    state: ConversationState
    duration_seconds: int
    message_count: int
    lead_score: Optional[int] = None
    lead_type: Optional[LeadType] = None
    is_vip: bool = False
    tickets_created: int = 0
    properties_viewed: int = 0

# ==========================================
# PROPERTY LISTING MODELS (for future use)
# ==========================================

class PropertyListing(BaseModel):
    """Property listing details"""
    property_id: str
    name: str
    property_type: PropertyType
    bedrooms: int
    bathrooms: int
    size_sqft: int
    price_aed: float
    location: str
    community: str
    amenities: List[str]
    description: str
    images: List[str] = []
    video_url: Optional[str] = None
    brochure_url: Optional[str] = None
    virtual_tour_url: Optional[str] = None
    available: bool = True
    listed_date: datetime
    agent_id: str
    coordinates: Optional[Tuple[float, float]] = None

class ViewingAppointment(BaseModel):
    """Property viewing appointment"""
    appointment_id: str
    property_id: str
    user_phone: str
    user_name: str
    agent_id: str
    scheduled_date: str
    scheduled_time: str
    status: str = "scheduled"  # scheduled, confirmed, completed, cancelled
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

# ==========================================
# WEBHOOK MODELS (Enhanced)
# ==========================================

class IncomingWebhook(BaseModel):
    """Incoming webhook payload"""
    event: str
    data: Dict[str, Any]
    timestamp: Optional[int] = None
    signature: Optional[str] = None

class OutgoingMessage(BaseModel):
    """Outgoing message payload"""
    to: str
    message: str
    message_type: str = "text"
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None

# ==========================================
# ERROR MODELS
# ==========================================

class ErrorLog(BaseModel):
    """Error logging model"""
    timestamp: datetime
    error_type: str
    error_message: str
    context: Dict[str, Any] = {}
    user_phone: Optional[str] = None
    stack_trace: Optional[str] = None

class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    value: Any

# ==========================================
# EXPORT ALL MODELS
# ==========================================

__all__ = [
    # Enums
    "IntentType", "Priority", "PropertyType", "Timeline", "Purpose",
    "LeadType", "LeadPriority", "AgentType", "ConversationState", "MessageRole",
    "Language", "TranslationQuality", "AgentStatus", "Specialization", "RoutingStrategy",
    "CommunityTier", "VIPTier", "FrustrationLevel", "PromptCategory",
    
    # Existing Models
    "WebhookMessage", "IntentClassification", "JiraProject", "TicketPreview",
    "PendingTicket", "ConversationLog",
    
    # Property Intelligence
    "BudgetRange", "PropertyRequirements",
    
    # Lead Qualification
    "BANTScore", "LeadAction",
    
    # Conversation Memory
    "ConversationMessage", "UserPreferences", "ConversationContext",
    
    # Multilingual
    "TranslationResult",
    
    # Smart Routing
    "Agent", "RoutingResult", "RoutingRule",
    
    # Dubai Knowledge
    "Community", "MarketInsight",
    
    # Sentiment & VIP
    "SentimentResult", "VIPProfile", "VIPDetectionResult",
    
    # Analytics
    "AnalyticsMetrics", "CostSummary",
    
    # Prompts
    "PromptTemplate",
    
    # Utility
    "APIResponse", "HealthCheck", "SessionSummary",
    
    # Property Listings
    "PropertyListing", "ViewingAppointment",
    
    # Webhooks
    "IncomingWebhook", "OutgoingMessage",
    
    # Errors
    "ErrorLog", "ValidationError"
]