"""
Advanced OpenAI Service with RAG, Caching, and Enhanced Prompts - FIXED
ENHANCED VERSION - Integrated with enhanced_prompts.py
"""

from openai import AsyncOpenAI
from config.settings import settings
from models.schemas import IntentType, IntentClassification, Priority
from services.cost_tracker import cost_tracker
from typing import Dict, List, Optional, Any
import json
import hashlib
from datetime import datetime, timedelta
from collections import OrderedDict
import re

# ==========================================
# NEW IMPORT - ENHANCED PROMPTS
# ==========================================
from services.enhanced_prompts import enhanced_prompts, PromptCategory

class ResponseCache:
    """LRU Cache for AI responses"""
    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(minutes=ttl_minutes)
        self._timestamps: Dict[str, datetime] = {}
    
    def _generate_key(self, prompt: str, context: dict = None) -> str:
        """Generate cache key"""
        data = f"{prompt}:{json.dumps(context or {}, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, prompt: str, context: dict = None) -> Optional[str]:
        """Get cached response"""
        key = self._generate_key(prompt, context)
        
        if key in self._cache:
            # Check TTL
            if datetime.now() - self._timestamps[key] < self._ttl:
                # Move to end (LRU)
                self._cache.move_to_end(key)
                print(f"💰 Cache HIT - Saved OpenAI call")
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
        
        return None
    
    def set(self, prompt: str, response: str, context: dict = None):
        """Store response in cache"""
        key = self._generate_key(prompt, context)
        
        # Remove oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = response
        self._timestamps[key] = datetime.now()


class OpenAIService:
    """
    🔥 ENHANCED: Advanced OpenAI integration with optimized prompts
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
        # Response cache
        self._cache = ResponseCache(max_size=1000, ttl_minutes=60)
        
        print("✅ OpenAI service initialized with enhanced prompts")
    
    # ==========================================
    # INTENT CLASSIFICATION - ENHANCED
    # ==========================================
    
    async def classify_intent(
        self,
        message: str,
        user_name: str,
        user_phone: str,
        conversation_history: List[Dict] = None
    ) -> IntentClassification:
        """
        🔥 ENHANCED: Intent classification with optimized prompts
        """
        
        # Check cache
        cache_context = {
            "user": user_phone,
            "history_count": len(conversation_history) if conversation_history else 0
        }
        cached = self._cache.get(message, cache_context)
        
        if cached:
            try:
                result = json.loads(cached)
                return self._parse_intent_result(result)
            except:
                pass
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_intent_classification_prompt(
            message=message,
            user_name=user_name,
            user_phone=user_phone,
            conversation_history=conversation_history
        )
        
        try:
            # Call OpenAI with enhanced prompts
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.3,  # Low temp for classification
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Track cost
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone,
                intent="classify_intent"
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            # Cache result
            self._cache.set(message, result_text, cache_context)
            
            print(f"🤖 AI Classification: {result.get('intent')} (confidence: {result.get('confidence', 0):.2f})")
            
            return self._parse_intent_result(result)
            
        except Exception as e:
            print(f"❌ Intent classification error: {e}")
            # Fallback to rule-based
            return self._fallback_intent_classification(message)
    
    def _parse_intent_result(self, result: dict) -> IntentClassification:
        """Parse API response to IntentClassification"""
        
        intent_str = result.get("intent", "general_inquiry")
        
        # Map to IntentType enum
        intent_map = {
            "create_ticket": IntentType.CREATE_TICKET,
            "check_status": IntentType.CHECK_STATUS,
            "update_ticket": IntentType.UPDATE_TICKET,
            "close_ticket": IntentType.CLOSE_TICKET,
            "property_inquiry": IntentType.PROPERTY_INQUIRY,
            "schedule_viewing": IntentType.SCHEDULE_VIEWING,
            "general_inquiry": IntentType.GENERAL_INQUIRY,
            "check_budget": IntentType.PROPERTY_INQUIRY,  # Map to property inquiry
        }
        
        intent = intent_map.get(intent_str, IntentType.GENERAL_INQUIRY)
        confidence = float(result.get("confidence", 0.5))
        entities = result.get("entities", {})
        
        # Parse priority
        priority = None
        priority_str = entities.get("priority")
        if priority_str:
            try:
                # Map common priority terms
                priority_map = {
                    "highest": Priority.HIGHEST,
                    "critical": Priority.HIGHEST,
                    "high": Priority.HIGH,
                    "urgent": Priority.HIGH,
                    "medium": Priority.MEDIUM,
                    "low": Priority.LOW,
                    "lowest": Priority.LOWEST
                }
                priority = priority_map.get(priority_str.lower(), Priority.MEDIUM)
            except:
                pass
        
        return IntentClassification(
            intent=intent,
            confidence=confidence,
            entities=entities,
            ticket_key=entities.get("ticket_key"),
            priority=priority
        )
    
    def _fallback_intent_classification(self, message: str) -> IntentClassification:
        """Rule-based fallback classification"""
        message_lower = message.lower()
        
        # Ticket number detection
        ticket_match = re.search(r'\b([A-Z]{2,}-\d+)\b', message, re.IGNORECASE)
        ticket_key = ticket_match.group(1).upper() if ticket_match else None
        
        # Intent detection
        if any(word in message_lower for word in ['villa', 'apartment', 'property', 'bedroom', 'buy', 'rent', 'price']):
            intent = IntentType.PROPERTY_INQUIRY
        elif ticket_key and any(word in message_lower for word in ['status', 'update', 'check', 'progress']):
            intent = IntentType.CHECK_STATUS
        elif ticket_key and any(word in message_lower for word in ['close', 'resolved', 'fixed', 'done']):
            intent = IntentType.CLOSE_TICKET
        elif any(word in message_lower for word in ['issue', 'problem', 'error', 'bug', 'not working', 'broken', 'failed']):
            intent = IntentType.CREATE_TICKET
        else:
            intent = IntentType.GENERAL_INQUIRY
        
        print(f"⚠️ Using fallback classification: {intent.value}")
        
        return IntentClassification(
            intent=intent,
            confidence=0.6,
            entities={},
            ticket_key=ticket_key
        )
    
    # ==========================================
    # TICKET GENERATION - ENHANCED
    # ==========================================
    
    async def generate_ticket_summary(
        self,
        message: str,
        user_name: str,
        team: str,
        user_phone: str
    ) -> str:
        """
        🔥 ENHANCED: Generate ticket summary with optimized prompt
        """
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_ticket_summary_prompt(
            user_message=message,
            team=team,
            user_name=user_name
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.5,
                max_tokens=100
            )
            
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone,
                intent="generate_summary"
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            summary = summary.strip('"').strip("'")
            
            # Truncate if too long
            if len(summary) > 100:
                summary = summary[:97] + "..."
            
            return summary
            
        except Exception as e:
            print(f"❌ Summary generation error: {e}")
            # Fallback
            return f"{team} - Issue reported by {user_name}"[:100]
    
    async def generate_ticket_description(
        self,
        message: str,
        user_name: str,
        user_phone: str
    ) -> str:
        """
        🔥 ENHANCED: Generate detailed ticket description
        """
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_ticket_description_prompt(
            user_message=message,
            team="Support Team",
            user_name=user_name,
            user_phone=user_phone
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.6,
                max_tokens=400
            )
            
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone,
                intent="generate_description"
            )
            
            description = response.choices[0].message.content.strip()
            return description
            
        except Exception as e:
            print(f"❌ Description generation error: {e}")
            # Fallback
            return f"""**Issue Reported:**
{message}

**Reported By:** {user_name} ({user_phone})
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

**Original Message:** "{message}"
"""
    
    # ==========================================
    # CONVERSATIONAL RESPONSE - FIXED
    # ==========================================
    
    async def generate_conversational_response(
        self,
        intent: IntentType,
        message: str,
        context: Dict[str, Any],
        user_phone: str
    ) -> str:
        """
        🔥 FIXED: Simple conversational response (no unnecessary API calls)
        """
        
        user_name = context.get("user_name", "there")
        company = context.get("company", "Support Team")
        
        # ==========================================
        # HANDLE PROPERTY INQUIRIES
        # ==========================================
        if intent == IntentType.PROPERTY_INQUIRY:
            return f"""Thank you for your interest! 🏠

For property inquiries, viewings, and pricing, please contact our sales team:

📧 Email: {settings.WHATSAPP_BUSINESS_EMAIL}
🌐 Website: {settings.WHATSAPP_BUSINESS_WEBSITE}

I specialize in Jira technical support. Can I help you with a system issue?"""
        
        # ==========================================
        # HANDLE GENERAL INQUIRIES / GREETINGS
        # ==========================================
        elif intent == IntentType.GENERAL_INQUIRY:
            # Check if it's a greeting
            greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                        'good evening', 'مرحبا', 'السلام']
            
            message_lower = message.lower()
            is_greeting = any(greeting in message_lower for greeting in greetings)
            
            if is_greeting:
                return f"""Hello {user_name}! 👋

I'm your Jira Support Assistant. How can I help you today?

I can assist with:
• Creating support tickets
• Checking ticket status
• Updating existing tickets

What would you like to do?"""
            
            # For non-greeting general inquiries, use AI
            try:
                prompts = enhanced_prompts.get_conversational_prompt(
                    intent=intent.value,
                    message=message,
                    context=context
                )
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompts["system"]},
                        {"role": "user", "content": prompts["user"]}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                usage = response.usage
                cost_tracker.track_openai_usage(
                    model=self.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    user_phone=user_phone,
                    intent="conversational"
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"❌ Conversational response error: {e}")
                return f"How can I assist you with your support needs today?"
        
        # ==========================================
        # DEFAULT RESPONSE
        # ==========================================
        return "How can I assist you with your support needs?"
    
    # ==========================================
    # PROPERTY EXTRACTION (delegated to property_intelligence)
    # ==========================================
    
    async def extract_property_requirements(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        user_phone: Optional[str] = None
    ) -> Dict:
        """
        Extract property requirements - delegates to property_intelligence_service
        This is a wrapper for backward compatibility
        """
        
        try:
            from services.property_intelligence import property_intelligence_service
            
            result = await property_intelligence_service.extract_requirements(
                message=message,
                conversation_history=conversation_history,
                user_phone=user_phone
            )
            
            return result.dict() if result else {}
            
        except Exception as e:
            print(f"❌ Property extraction error: {e}")
            return {
                "property_type": None,
                "bedrooms": None,
                "budget": None,
                "locations": [],
                "confidence": 0.5
            }
    
    # ==========================================
    # SENTIMENT ANALYSIS
    # ==========================================
    
    async def analyze_sentiment(
        self,
        message: str,
        conversation_history: Optional[str] = None,
        user_phone: Optional[str] = None
    ) -> Dict:
        """Analyze sentiment and urgency"""
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_sentiment_analysis_prompt(
            message=message,
            history=conversation_history
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone or "unknown",
                intent="sentiment_analysis"
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"❌ Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "urgency": 5,
                "frustration": False,
                "escalate": False,
                "reasoning": []
            }
    
    # ==========================================
    # TRANSLATION (delegated to multilingual service)
    # ==========================================
    
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
        user_phone: Optional[str] = None
    ) -> str:
        """
        Translate text - delegates to multilingual_service
        This is a wrapper for backward compatibility
        """
        
        try:
            from services.multilingual import multilingual_service, Language
            
            # Map language codes
            lang_map = {
                "en": Language.ENGLISH,
                "ar": Language.ARABIC,
                "english": Language.ENGLISH,
                "arabic": Language.ARABIC
            }
            
            source = lang_map.get(source_language.lower(), Language.ENGLISH)
            target = lang_map.get(target_language.lower(), Language.ARABIC)
            
            result = await multilingual_service.translate(
                text=text,
                target_language=target,
                source_language=source,
                user_phone=user_phone,
                context=context
            )
            
            return result.translated_text
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return text
    
    # ==========================================
    # PROPERTY RECOMMENDATION
    # ==========================================
    
    async def generate_property_recommendations(
        self,
        requirements: Dict,
        available_properties: List[Dict],
        max_recommendations: int = 3,
        user_phone: Optional[str] = None
    ) -> str:
        """Generate property recommendations"""
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_property_recommendation_prompt(
            requirements=requirements,
            available_properties=available_properties,
            max_recommendations=max_recommendations
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone or "unknown",
                intent="property_recommendation"
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Property recommendation error: {e}")
            return "I can help you find the perfect property. Please contact our sales team for personalized recommendations."
    
    # ==========================================
    # MARKET INSIGHTS
    # ==========================================
    
    async def generate_market_insights(
        self,
        area: str,
        property_type: str,
        user_phone: Optional[str] = None
    ) -> str:
        """Generate market insights for area"""
        
        # Get enhanced prompt
        prompts = enhanced_prompts.get_market_insight_prompt(
            area=area,
            property_type=property_type
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": prompts["user"]}
                ],
                temperature=0.6,
                max_tokens=300
            )
            
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone or "unknown",
                intent="market_insights"
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Market insights error: {e}")
            return f"Market data for {area} is currently being updated. Please contact our team for the latest insights."
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "size": len(self._cache._cache),
            "max_size": self._cache._max_size,
            "utilization": f"{len(self._cache._cache) / self._cache._max_size * 100:.1f}%",
            "hit_rate": "Tracked via cost savings"
        }
    
    def clear_cache(self):
        """Clear response cache"""
        self._cache._cache.clear()
        self._cache._timestamps.clear()
        print("🧹 OpenAI cache cleared")
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def get_token_budget(self, message: str, context: Optional[List[Dict]] = None) -> Dict:
        """Estimate token usage for a request"""
        
        message_tokens = self.estimate_tokens(message)
        
        context_tokens = 0
        if context:
            context_text = " ".join([msg.get('message', '') for msg in context])
            context_tokens = self.estimate_tokens(context_text)
        
        # System prompt estimate (varies by category)
        system_tokens = 500  # Average system prompt size
        
        total_input = message_tokens + context_tokens + system_tokens
        
        # Estimate cost (gpt-4o-mini pricing)
        input_cost = total_input * (0.150 / 1_000_000)
        output_cost = self.max_tokens * (0.600 / 1_000_000)
        total_cost = input_cost + output_cost
        
        return {
            "message_tokens": message_tokens,
            "context_tokens": context_tokens,
            "system_tokens": system_tokens,
            "total_input_tokens": total_input,
            "max_output_tokens": self.max_tokens,
            "estimated_cost": round(total_cost, 6)
        }


# Global instance
openai_service = OpenAIService()