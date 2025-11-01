"""
📝 Enhanced Prompt Engineering for Dubai Real Estate
Optimized prompts for property extraction, intent classification, and response generation
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

# ==========================================
# PROMPT CATEGORIES
# ==========================================

class PromptCategory(str, Enum):
    INTENT_CLASSIFICATION = "intent_classification"
    PROPERTY_EXTRACTION = "property_extraction"
    LEAD_QUALIFICATION = "lead_qualification"
    RESPONSE_GENERATION = "response_generation"
    TRANSLATION = "translation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TICKET_GENERATION = "ticket_generation"

# ==========================================
# ENHANCED PROMPTS SERVICE
# ==========================================

class EnhancedPromptsService:
    """
    Centralized prompt management for Dubai real estate AI
    Token-optimized, context-aware prompts
    """
    
    def __init__(self):
        self.prompts = self._initialize_prompts()
        
        # Dubai market context (shared across prompts)
        self.dubai_context = """
**Dubai Real Estate Market Context:**
- Currency: AED (UAE Dirham)
- Popular luxury areas: Palm Jumeirah, Emirates Hills, Downtown Dubai, Dubai Marina
- Mid-range areas: JVC, Dubai Sports City, Arabian Ranches
- Affordable: Dubai Silicon Oasis, Discovery Gardens, International City
- Typical prices:
  • Studio: 400K-800K AED
  • 1BR: 800K-1.5M AED
  • 2BR: 1.5M-3M AED
  • 3BR Villa: 3M-8M AED
  • Luxury villa: 10M-100M+ AED
- Rental yield: 4-10% depending on area
- Peak buying season: October-March
- Business language: English & Arabic
"""
    
    def _initialize_prompts(self) -> Dict[str, Dict]:
        """Initialize all prompt templates"""
        
        return {
            # ==========================================
            # INTENT CLASSIFICATION
            # ==========================================
            PromptCategory.INTENT_CLASSIFICATION: {
                "system": """You are an AI assistant for Dubai Sotheby's International Realty.

**Your Role:**
Classify customer intents for:
1. Property inquiries (buy/rent/invest)
2. Technical support (CRM/system issues)
3. General questions

**Available Intents:**
- property_inquiry: Looking for properties
- schedule_viewing: Want to see a property
- check_budget: Budget/pricing questions
- create_ticket: Report technical issue
- check_status: Check support ticket status
- update_ticket: Update existing ticket
- close_ticket: Close resolved ticket
- general_inquiry: Greetings, questions

**Output Format:** JSON only
{
  "intent": "intent_name",
  "confidence": 0.0-1.0,
  "entities": {
    "ticket_key": "SUP-123 or null",
    "priority": "High/Medium/Low or null",
    "team": "Salesforce/Development/Data Team or null",
    "keywords": ["extracted", "words"]
  }
}""",
                
                "user_template": """**Message:** "{message}"

**User:** {user_name} ({user_phone})

{conversation_history}

Classify intent (JSON only):""",
                
                "examples": [
                    {
                        "input": "I want to buy a 3-bedroom villa in Palm Jumeirah",
                        "output": '{"intent": "property_inquiry", "confidence": 0.95, "entities": {"keywords": ["buy", "villa", "palm jumeirah", "3-bedroom"]}}'
                    },
                    {
                        "input": "Can I schedule a viewing for tomorrow?",
                        "output": '{"intent": "schedule_viewing", "confidence": 0.92, "entities": {"keywords": ["viewing", "tomorrow"]}}'
                    },
                    {
                        "input": "Salesforce is not syncing leads",
                        "output": '{"intent": "create_ticket", "confidence": 0.93, "entities": {"team": "Salesforce Team", "keywords": ["salesforce", "sync", "leads"]}}'
                    }
                ]
            },
            
            # ==========================================
            # PROPERTY EXTRACTION
            # ==========================================
            PromptCategory.PROPERTY_EXTRACTION: {
                "system": """You are a Dubai real estate data extraction specialist.

Extract property requirements accurately and return structured JSON.

**Extract:**
- Property type (villa, apartment, penthouse, townhouse, studio, office)
- Bedrooms (0 for studio)
- Budget (in AED)
- Locations (Dubai areas)
- Must-haves (amenities)
- Timeline (urgent, 1_month, 3_months, exploring)
- Purpose (buy, rent, invest)

**Output Format:** JSON only""",
                
                "user_template": """**Message:** "{message}"

{dubai_context}

{conversation_history}

**Extract requirements (JSON):**
{{
  "property_type": "villa|apartment|...|null",
  "bedrooms": 0-10 or null,
  "budget": {{"min": AED, "max": AED, "confidence": 0-1}},
  "locations": ["area1", "area2"],
  "must_haves": ["sea view", "pool"],
  "timeline": "urgent|1_month|3_months|exploring",
  "purpose": "buy|rent|invest",
  "confidence": 0.0-1.0
}}""",
                
                "examples": [
                    {
                        "input": "Looking for 2BR apartment in Marina, budget 2-3 million",
                        "output": '{"property_type": "apartment", "bedrooms": 2, "budget": {"min": 2000000, "max": 3000000, "confidence": 0.9}, "locations": ["Dubai Marina"], "purpose": "buy", "confidence": 0.88}'
                    },
                    {
                        "input": "Need luxury villa with pool and sea view ASAP",
                        "output": '{"property_type": "villa", "must_haves": ["pool", "sea view"], "timeline": "urgent", "confidence": 0.75}'
                    }
                ]
            },
            
            # ==========================================
            # LEAD QUALIFICATION
            # ==========================================
            PromptCategory.LEAD_QUALIFICATION: {
                "system": """You are a lead qualification specialist for Dubai real estate.

Analyze conversation and rate lead quality (0-100) based on BANT:
- **Budget (30pts):** Clear budget? Realistic?
- **Authority (25pts):** Decision maker? Investor?
- **Need (25pts):** Specific requirements?
- **Timeline (20pts):** Urgency?

**Output:** JSON only""",
                
                "user_template": """**Conversation:**
{conversation_summary}

**Property Requirements:**
{property_requirements}

**Rate this lead (JSON):**
{{
  "budget_score": 0-30,
  "authority_score": 0-25,
  "need_score": 0-25,
  "timeline_score": 0-20,
  "total_score": 0-100,
  "lead_type": "hot|warm|cold|unqualified",
  "reasoning": ["reason1", "reason2"]
}}"""
            },
            
            # ==========================================
            # RESPONSE GENERATION
            # ==========================================
            PromptCategory.RESPONSE_GENERATION: {
                "greeting": {
                    "system": "You are a friendly Dubai Sotheby's Realty assistant. Greet warmly and professionally.",
                    "user_template": """Greet this user:
**Name:** {user_name}
**Language:** {language}
**VIP:** {is_vip}

Generate warm greeting (max 100 words):"""
                },
                
                "property_redirect": {
                    "system": "You are redirecting property inquiry to sales team. Be helpful and professional.",
                    "user_template": """User asked about properties but you handle technical support only.

**User:** {user_name}
**Query:** {user_message}
**Sales Email:** {sales_email}
**Website:** {website}

Politely redirect to sales team (max 150 words):"""
                },
                
                "hot_lead_response": {
                    "system": "You're responding to a hot lead. Be enthusiastic and create urgency.",
                    "user_template": """Hot lead detected!

**Requirements:** {property_requirements}
**Budget:** {budget}
**Timeline:** {timeline}

Generate enthusiastic response promising quick callback (max 120 words):"""
                },
                
                "clarification": {
                    "system": "Ask clarifying questions to better understand property needs.",
                    "user_template": """User gave vague requirements:
"{user_message}"

**Missing info:** {missing_fields}

Ask 2-3 friendly clarifying questions (max 100 words):"""
                },
                
                "viewing_confirmation": {
                    "system": "Confirm property viewing appointment professionally.",
                    "user_template": """Confirm viewing:
**Property:** {property_name}
**Date:** {date}
**Time:** {time}
**Agent:** {agent_name}
**Phone:** {agent_phone}

Generate confirmation message (max 150 words):"""
                }
            },
            
            # ==========================================
            # TRANSLATION
            # ==========================================
            PromptCategory.TRANSLATION: {
                "system": """You are a professional translator for Dubai real estate.

**Guidelines:**
- Use formal Arabic (not dialect)
- Keep property terms accurate
- Maintain professional tone
- Preserve formatting and emojis
- Be culturally appropriate

**Context:** Real estate communication in Dubai""",
                
                "user_template": """Translate from {source_language} to {target_language}:

**Text:**
{text}

{context}

**Translation:**"""
            },
            
            # ==========================================
            # SENTIMENT ANALYSIS
            # ==========================================
            PromptCategory.SENTIMENT_ANALYSIS: {
                "system": """Analyze customer sentiment and urgency.

**Detect:**
- Sentiment: positive, neutral, negative
- Urgency level: 0-10
- Frustration indicators
- Deal risk factors

**Output:** JSON only""",
                
                "user_template": """**Message:** "{message}"

**Conversation history:**
{history}

**Analyze sentiment (JSON):**
{{
  "sentiment": "positive|neutral|negative",
  "score": -1.0 to 1.0,
  "urgency": 0-10,
  "frustration": true|false,
  "escalate": true|false,
  "reasoning": ["reason1", "reason2"]
}}"""
            },
            
            # ==========================================
            # TICKET GENERATION
            # ==========================================
            PromptCategory.TICKET_GENERATION: {
                "summary": {
                    "system": "Generate concise Jira ticket summary (max 100 chars) for technical issues.",
                    "user_template": """**Issue:** "{user_message}"
**Team:** {team}
**User:** {user_name}

**Generate summary (1 line, action-oriented):**"""
                },
                
                "description": {
                    "system": "Generate detailed Jira ticket description with structure.",
                    "user_template": """**User message:** "{user_message}"
**Team:** {team}
**User:** {user_name} ({user_phone})

**Generate structured description:**

**Issue Reported:**
[Clear description]

**User Impact:**
[How this affects work]

**Technical Context:**
[System/module affected]

**Reported By:** {user_name} ({user_phone})
**Timestamp:** {timestamp}"""
                }
            }
        }
    
    # ==========================================
    # PROMPT RETRIEVAL
    # ==========================================
    
    def get_intent_classification_prompt(
        self,
        message: str,
        user_name: str,
        user_phone: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """Get intent classification prompt"""
        
        prompts = self.prompts[PromptCategory.INTENT_CLASSIFICATION]
        
        # Build conversation history text
        history_text = ""
        if conversation_history:
            history_text = "**Recent conversation:**\n"
            for msg in conversation_history[-3:]:
                role = msg.get('role', 'user')
                content = msg.get('message', '')[:100]
                history_text += f"- {role}: {content}\n"
        
        user_prompt = prompts["user_template"].format(
            message=message,
            user_name=user_name,
            user_phone=user_phone,
            conversation_history=history_text
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_property_extraction_prompt(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """Get property extraction prompt"""
        
        prompts = self.prompts[PromptCategory.PROPERTY_EXTRACTION]
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_text = "**Previous messages:**\n"
            for msg in conversation_history[-3:]:
                content = msg.get('message', '')[:80]
                history_text += f"- {content}\n"
        
        user_prompt = prompts["user_template"].format(
            message=message,
            dubai_context=self.dubai_context,
            conversation_history=history_text
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_lead_qualification_prompt(
        self,
        conversation_summary: str,
        property_requirements: str
    ) -> Dict[str, str]:
        """Get lead qualification prompt"""
        
        prompts = self.prompts[PromptCategory.LEAD_QUALIFICATION]
        
        user_prompt = prompts["user_template"].format(
            conversation_summary=conversation_summary,
            property_requirements=property_requirements
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_response_generation_prompt(
        self,
        response_type: str,
        **kwargs
    ) -> Dict[str, str]:
        """Get response generation prompt"""
        
        prompts = self.prompts[PromptCategory.RESPONSE_GENERATION]
        
        if response_type not in prompts:
            response_type = "greeting"
        
        template = prompts[response_type]
        
        user_prompt = template["user_template"].format(**kwargs)
        
        return {
            "system": template["system"],
            "user": user_prompt
        }
    
    def get_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> Dict[str, str]:
        """Get translation prompt"""
        
        prompts = self.prompts[PromptCategory.TRANSLATION]
        
        context_text = f"\n**Context:** {context}" if context else ""
        
        user_prompt = prompts["user_template"].format(
            source_language=source_language,
            target_language=target_language,
            text=text,
            context=context_text
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_sentiment_analysis_prompt(
        self,
        message: str,
        history: Optional[str] = None
    ) -> Dict[str, str]:
        """Get sentiment analysis prompt"""
        
        prompts = self.prompts[PromptCategory.SENTIMENT_ANALYSIS]
        
        history_text = history if history else "No previous context"
        
        user_prompt = prompts["user_template"].format(
            message=message,
            history=history_text
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_ticket_summary_prompt(
        self,
        user_message: str,
        team: str,
        user_name: str
    ) -> Dict[str, str]:
        """Get ticket summary generation prompt"""
        
        prompts = self.prompts[PromptCategory.TICKET_GENERATION]["summary"]
        
        user_prompt = prompts["user_template"].format(
            user_message=user_message,
            team=team,
            user_name=user_name
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    def get_ticket_description_prompt(
        self,
        user_message: str,
        team: str,
        user_name: str,
        user_phone: str
    ) -> Dict[str, str]:
        """Get ticket description generation prompt"""
        
        prompts = self.prompts[PromptCategory.TICKET_GENERATION]["description"]
        
        user_prompt = prompts["user_template"].format(
            user_message=user_message,
            team=team,
            user_name=user_name,
            user_phone=user_phone,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        )
        
        return {
            "system": prompts["system"],
            "user": user_prompt
        }
    
    # ==========================================
    # TOKEN OPTIMIZATION
    # ==========================================
    
    def get_optimized_history(
        self,
        conversation_history: List[Dict],
        max_messages: int = 5,
        max_chars_per_message: int = 150
    ) -> str:
        """Get token-optimized conversation history"""
        
        if not conversation_history:
            return ""
        
        recent = conversation_history[-max_messages:]
        
        history_text = "**Context:**\n"
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('message', '')[:max_chars_per_message]
            history_text += f"{role}: {content}\n"
        
        return history_text
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    # ==========================================
    # PROMPT EXAMPLES (for few-shot learning)
    # ==========================================
    
    def get_few_shot_examples(
        self,
        category: PromptCategory,
        count: int = 3
    ) -> List[Dict]:
        """Get few-shot examples for a category"""
        
        if category in self.prompts and "examples" in self.prompts[category]:
            return self.prompts[category]["examples"][:count]
        
        return []
    
    # ==========================================
    # CUSTOM PROMPT BUILDER
    # ==========================================
    
    def build_custom_prompt(
        self,
        system_instruction: str,
        user_context: Dict[str, Any],
        include_dubai_context: bool = True,
        include_examples: bool = False,
        category: Optional[PromptCategory] = None
    ) -> Dict[str, str]:
        """Build custom prompt with optional context"""
        
        # Build system prompt
        system = system_instruction
        
        if include_dubai_context:
            system += f"\n\n{self.dubai_context}"
        
        # Build user prompt
        user_parts = []
        
        for key, value in user_context.items():
            if value:
                user_parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
        
        user_prompt = "\n\n".join(user_parts)
        
        # Add examples if requested
        if include_examples and category:
            examples = self.get_few_shot_examples(category)
            if examples:
                examples_text = "\n\n**Examples:**\n"
                for i, example in enumerate(examples, 1):
                    examples_text += f"\n{i}. Input: {example['input']}\n   Output: {example['output']}\n"
                user_prompt += examples_text
        
        return {
            "system": system,
            "user": user_prompt
        }
    
    # ==========================================
    # REAL ESTATE SPECIFIC HELPERS
    # ==========================================
    
    def get_property_recommendation_prompt(
        self,
        requirements: Dict,
        available_properties: List[Dict],
        max_recommendations: int = 3
    ) -> Dict[str, str]:
        """Generate property recommendation prompt"""
        
        system = f"""You are a Dubai Sotheby's property consultant.

Recommend the best {max_recommendations} properties based on client requirements.

**Consider:**
- Budget match
- Location preference
- Property type
- Size requirements
- Must-have amenities
- Investment potential

{self.dubai_context}"""

        properties_text = ""
        for i, prop in enumerate(available_properties[:10], 1):
            properties_text += f"\n{i}. {prop.get('name', 'Property')} - {prop.get('location', '')} - {prop.get('price', '')} AED"
        
        user = f"""**Client Requirements:**
{requirements}

**Available Properties:**
{properties_text}

**Recommend top {max_recommendations} with reasoning (max 200 words):**"""

        return {
            "system": system,
            "user": user
        }
    
    def get_market_insight_prompt(
        self,
        area: str,
        property_type: str
    ) -> Dict[str, str]:
        """Generate market insight prompt"""
        
        system = f"""You are a Dubai real estate market analyst.

Provide market insights for specific areas and property types.

{self.dubai_context}

**Focus on:**
- Current market trends
- Price movements
- Investment potential
- Rental yields
- Future developments"""

        user = f"""**Area:** {area}
**Property Type:** {property_type}

**Provide market insight (max 150 words):**"""

        return {
            "system": system,
            "user": user
        }


# Global instance
enhanced_prompts = EnhancedPromptsService()