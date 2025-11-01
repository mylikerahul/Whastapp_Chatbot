"""
🌍 Multilingual Support Service - Arabic & English for Dubai Market
Language detection, translation, and localized responses
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import re
from collections import OrderedDict

from services.openai_service import openai_service
from services.cost_tracker import cost_tracker

# ==========================================
# ENUMS & DATA MODELS
# ==========================================

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"
    MIXED = "mixed"  # Arabish (Arabic in Latin script)

class TranslationQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: Language
    target_language: Language
    confidence: float
    quality: TranslationQuality
    cached: bool = False
    timestamp: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now()

# ==========================================
# TRANSLATION CACHE
# ==========================================

class TranslationCache:
    """LRU cache for translations"""
    
    def __init__(self, max_size: int = 500):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
    
    def _generate_key(self, text: str, source: str, target: str) -> str:
        """Generate cache key"""
        return f"{source}:{target}:{text[:100]}"
    
    def get(self, text: str, source: str, target: str) -> Optional[str]:
        """Get cached translation"""
        key = self._generate_key(text, source, target)
        
        if key in self._cache:
            # Move to end (LRU)
            self._cache.move_to_end(key)
            return self._cache[key]
        
        return None
    
    def set(self, text: str, source: str, target: str, translation: str):
        """Store translation"""
        key = self._generate_key(text, source, target)
        
        # Remove oldest if at capacity
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = translation

# ==========================================
# MULTILINGUAL SERVICE
# ==========================================

class MultilingualService:
    """
    Comprehensive multilingual support for Dubai real estate
    Supports: English, Arabic, and Arabish (Arabic in Latin script)
    """
    
    def __init__(self):
        # Translation cache
        self._cache = TranslationCache(max_size=500)
        
        # Arabic keywords for detection
        self._arabic_keywords = [
            'مرحبا', 'السلام', 'شكرا', 'عقار', 'فيلا', 'شقة', 
            'غرفة', 'سعر', 'ميزانية', 'موقع', 'دبي', 'نوم',
            'حمام', 'مطلوب', 'أريد', 'بحث', 'استفسار'
        ]
        
        # Arabish (Arabic in Latin script) patterns
        self._arabish_patterns = {
            'marhaba': 'مرحبا',
            'shukran': 'شكراً',
            'afwan': 'عفواً',
            'na3am': 'نعم',
            'la': 'لا',
            '3akar': 'عقار',
            'villa': 'فيلا',
            'sha2a': 'شقة',
            'ghorfa': 'غرفة',
            'si3r': 'سعر',
            'maw2i3': 'موقع',
            'dubai': 'دبي'
        }
        
        # Common real estate phrases in Arabic
        self._arabic_phrases = {
            # Greetings
            "hello": "مرحباً",
            "good morning": "صباح الخير",
            "good evening": "مساء الخير",
            "how can I help you": "كيف يمكنني مساعدتك؟",
            "thank you": "شكراً لك",
            "you're welcome": "على الرحب والسعة",
            
            # Property types
            "villa": "فيلا",
            "apartment": "شقة",
            "penthouse": "بنتهاوس",
            "townhouse": "تاون هاوس",
            "studio": "استوديو",
            "office": "مكتب",
            
            # Common terms
            "bedroom": "غرفة نوم",
            "bedrooms": "غرف نوم",
            "bathroom": "حمام",
            "bathrooms": "حمامات",
            "price": "السعر",
            "budget": "الميزانية",
            "location": "الموقع",
            "area": "المنطقة",
            "property": "عقار",
            "properties": "عقارات",
            
            # Actions
            "buy": "شراء",
            "rent": "إيجار",
            "sell": "بيع",
            "search": "بحث",
            "view": "معاينة",
            "viewing": "معاينة",
            
            # Locations
            "Dubai Marina": "دبي مارينا",
            "Downtown Dubai": "وسط مدينة دبي",
            "Palm Jumeirah": "نخلة جميرا",
            "Business Bay": "الخليج التجاري",
            "JBR": "جي بي آر",
            
            # Status
            "available": "متاح",
            "sold": "مُباع",
            "rented": "مُؤجر",
            "urgent": "عاجل",
            
            # Responses
            "I understand": "أفهم",
            "Let me help you": "دعني أساعدك",
            "Please wait": "من فضلك انتظر",
            "I will contact you": "سأتصل بك",
            "Thank you for contacting us": "شكراً لتواصلك معنا"
        }
        
        # Pre-translated response templates
        self._response_templates = {
            Language.ARABIC: {
                "greeting": "مرحباً {name}! 👋\n\nأنا مساعدك في سوذبيز ريلتي دبي. كيف يمكنني مساعدتك اليوم في العقارات؟",
                
                "property_redirect": "شكراً لاهتمامك! 🏠\n\nللاستفسارات عن العقارات والأسعار والمعاينات، يرجى التواصل مع فريق المبيعات:\n\n📧 البريد: {email}\n🌐 الموقع: {website}\n\nهل يمكنني مساعدتك في شيء آخر؟",
                
                "ticket_created": "✅ تم إنشاء التذكرة بنجاح\n\n*رقم التذكرة:* {ticket_key}\n*الملخص:* {summary}\n\nسنقوم بإعلامك عند التحديثات. شكراً لك!",
                
                "ticket_status": "📊 *حالة التذكرة - {ticket_key}*\n\n*الملخص:* {summary}\n*الحالة:* {status}\n*الأولوية:* {priority}\n*المسؤول:* {assignee}\n\nرابط التفاصيل:\n{url}",
                
                "error": "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",
                
                "confirm_ticket": "📝 *معاينة التذكرة*\n\n*الملخص:* {summary}\n*الفريق:* {team}\n*الأولوية:* {priority}\n\nرد بـ \"نعم\" لإنشاء التذكرة أو صِف أي تغييرات مطلوبة.",
                
                "vip_greeting": "👑 مرحباً {name}!\n\nيسعدنا خدمتك. أنت من عملائنا المميزين VIP.\n\nكيف يمكنني مساعدتك اليوم؟",
                
                "viewing_scheduled": "✅ *تم تأكيد المعاينة*\n\n🏠 العقار: {property}\n📅 التاريخ: {date}\n⏰ الوقت: {time}\n👤 الوكيل: {agent}\n📞 الهاتف: {phone}\n\nنتطلع لرؤيتك!",
                
                "hot_lead": "🔥 شكراً لاهتمامك!\n\nفريقنا المتخصص سيتواصل معك خلال ساعة واحدة مع عروض مخصصة تناسب متطلباتك.\n\nهل لديك أي استفسارات إضافية؟",
                
                "budget_inquiry": "لمساعدتك بشكل أفضل، هل يمكنك مشاركة:\n\n1️⃣ نطاق ميزانيتك؟\n2️⃣ عدد غرف النوم المطلوبة؟\n3️⃣ المواقع المفضلة؟\n\nهذا سيساعدنا في إيجاد أفضل العقارات لك! 🏡"
            },
            
            Language.ENGLISH: {
                "greeting": "Hello {name}! 👋\n\nI'm your Sotheby's Realty Dubai assistant. How can I help you with properties today?",
                
                "property_redirect": "Thank you for your interest! 🏠\n\nFor property inquiries, pricing, and viewings, please contact our sales team:\n\n📧 Email: {email}\n🌐 Website: {website}\n\nCan I help you with anything else?",
                
                "ticket_created": "✅ Ticket Created Successfully\n\n*Ticket ID:* {ticket_key}\n*Summary:* {summary}\n\nWe'll notify you with updates. Thank you!",
                
                "ticket_status": "📊 *Ticket Status - {ticket_key}*\n\n*Summary:* {summary}\n*Status:* {status}\n*Priority:* {priority}\n*Assignee:* {assignee}\n\nDetails:\n{url}",
                
                "error": "Sorry, an error occurred. Please try again or contact support.",
                
                "confirm_ticket": "📝 *Ticket Preview*\n\n*Summary:* {summary}\n*Team:* {team}\n*Priority:* {priority}\n\nReply \"Yes\" to create this ticket or describe any changes.",
                
                "vip_greeting": "👑 Welcome {name}!\n\nDelighted to serve you. You're our valued VIP client.\n\nHow can I assist you today?",
                
                "viewing_scheduled": "✅ *Viewing Confirmed*\n\n🏠 Property: {property}\n📅 Date: {date}\n⏰ Time: {time}\n👤 Agent: {agent}\n📞 Phone: {phone}\n\nLooking forward to showing you!",
                
                "hot_lead": "🔥 Thank you for your interest!\n\nOur specialist team will contact you within one hour with personalized property matches.\n\nAny other questions?",
                
                "budget_inquiry": "To help you better, could you please share:\n\n1️⃣ Your budget range?\n2️⃣ Number of bedrooms needed?\n3️⃣ Preferred locations?\n\nThis will help us find the perfect properties for you! 🏡"
            }
        }
    
    # ==========================================
    # LANGUAGE DETECTION
    # ==========================================
    
    def detect_language(self, text: str) -> Tuple[Language, float]:
        """
        Detect language of text
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (Language, confidence_score)
        """
        
        if not text or len(text.strip()) == 0:
            return Language.ENGLISH, 0.5
        
        # Check for Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return Language.ENGLISH, 0.5
        
        arabic_ratio = arabic_chars / total_chars
        
        # If more than 30% Arabic characters, it's Arabic
        if arabic_ratio > 0.3:
            confidence = min(arabic_ratio * 1.5, 1.0)
            return Language.ARABIC, confidence
        
        # Check for Arabish patterns
        text_lower = text.lower()
        arabish_matches = sum(
            1 for pattern in self._arabish_patterns.keys()
            if pattern in text_lower
        )
        
        if arabish_matches >= 2:
            return Language.MIXED, 0.7
        
        # Check for Arabic keywords in Latin script
        if any(keyword in text_lower for keyword in ['3akar', 'sha2a', 'ghorfa']):
            return Language.MIXED, 0.6
        
        # Default to English
        return Language.ENGLISH, 0.8
    
    def is_arabic(self, text: str) -> bool:
        """Quick check if text is Arabic"""
        lang, confidence = self.detect_language(text)
        return lang == Language.ARABIC and confidence > 0.5
    
    # ==========================================
    # TRANSLATION
    # ==========================================
    
    async def translate(
        self,
        text: str,
        target_language: Language,
        source_language: Optional[Language] = None,
        user_phone: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)
            user_phone: User phone for cost tracking
            context: Additional context (e.g., "real estate inquiry")
        
        Returns:
            TranslationResult
        """
        
        # Detect source language if not provided
        if not source_language:
            source_language, _ = self.detect_language(text)
        
        # No translation needed if same language
        if source_language == target_language:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0,
                quality=TranslationQuality.HIGH,
                cached=True
            )
        
        # Check cache
        cached = self._cache.get(text, source_language.value, target_language.value)
        if cached:
            print(f"💰 Translation cache HIT")
            return TranslationResult(
                original_text=text,
                translated_text=cached,
                source_language=source_language,
                target_language=target_language,
                confidence=0.95,
                quality=TranslationQuality.HIGH,
                cached=True
            )
        
        # Convert Arabish to Arabic first if needed
        if source_language == Language.MIXED:
            text = self._convert_arabish_to_arabic(text)
            source_language = Language.ARABIC
        
        # Translate using OpenAI
        try:
            translated = await self._translate_with_openai(
                text, 
                source_language, 
                target_language,
                context,
                user_phone
            )
            
            # Cache result
            self._cache.set(text, source_language.value, target_language.value, translated)
            
            return TranslationResult(
                original_text=text,
                translated_text=translated,
                source_language=source_language,
                target_language=target_language,
                confidence=0.9,
                quality=TranslationQuality.HIGH,
                cached=False
            )
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            
            # Fallback to original text
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.5,
                quality=TranslationQuality.LOW,
                cached=False
            )
    
    async def _translate_with_openai(
        self,
        text: str,
        source: Language,
        target: Language,
        context: Optional[str],
        user_phone: Optional[str]
    ) -> str:
        """Translate using OpenAI"""
        
        # Language names
        lang_names = {
            Language.ENGLISH: "English",
            Language.ARABIC: "Arabic"
        }
        
        source_name = lang_names.get(source, "English")
        target_name = lang_names.get(target, "Arabic")
        
        # Build prompt
        context_text = f"\n\nContext: {context}" if context else ""
        
        prompt = f"""Translate this {source_name} text to {target_name}.

**Important:**
- This is for Dubai real estate communication
- Maintain professional and friendly tone
- Keep property-related terms accurate
- Preserve formatting (line breaks, emojis)
- Use formal Arabic (not dialect)

**Text to translate:**
{text}
{context_text}

**Translation ({target_name}):**"""

        try:
            response = await openai_service.client.chat.completions.create(
                model=openai_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in Dubai real estate. Translate accurately from {source_name} to {target_name}."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temp for consistent translation
                max_tokens=500
            )
            
            # Track cost
            usage = response.usage
            cost_tracker.track_openai_usage(
                model=openai_service.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                user_phone=user_phone or "unknown",
                intent="translation"
            )
            
            translated = response.choices[0].message.content.strip()
            
            print(f"🌍 Translated: {source_name} → {target_name}")
            
            return translated
            
        except Exception as e:
            print(f"❌ OpenAI translation failed: {e}")
            raise
    
    def _convert_arabish_to_arabic(self, text: str) -> str:
        """Convert Arabish (Arabic in Latin script) to Arabic"""
        
        result = text
        
        for arabish, arabic in self._arabish_patterns.items():
            # Case-insensitive replacement
            result = re.sub(
                f'\\b{arabish}\\b',
                arabic,
                result,
                flags=re.IGNORECASE
            )
        
        return result
    
    # ==========================================
    # RESPONSE TEMPLATES
    # ==========================================
    
    def get_template_response(
        self,
        template_key: str,
        language: Language,
        **kwargs
    ) -> str:
        """
        Get pre-translated template response
        
        Args:
            template_key: Template identifier
            language: Target language
            **kwargs: Template variables
        
        Returns:
            Formatted response string
        """
        
        # Default to English if language not supported
        if language not in [Language.ENGLISH, Language.ARABIC]:
            language = Language.ENGLISH
        
        # Get template
        templates = self._response_templates.get(language, {})
        template = templates.get(template_key, "")
        
        if not template:
            print(f"⚠️ Template '{template_key}' not found for {language.value}")
            # Fallback to English
            template = self._response_templates[Language.ENGLISH].get(template_key, "")
        
        # Format with variables
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"⚠️ Missing template variable: {e}")
            return template
    
    def translate_property_type(
        self,
        property_type: str,
        target_language: Language
    ) -> str:
        """Translate property type"""
        
        if target_language == Language.ARABIC:
            return self._arabic_phrases.get(property_type.lower(), property_type)
        
        return property_type
    
    def translate_location(
        self,
        location: str,
        target_language: Language
    ) -> str:
        """Translate location name"""
        
        if target_language == Language.ARABIC:
            return self._arabic_phrases.get(location, location)
        
        return location
    
    # ==========================================
    # SMART RESPONSE (Auto-detect language)
    # ==========================================
    
    async def get_smart_response(
        self,
        template_key: str,
        user_message: str,
        user_phone: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get response in user's language (auto-detected)
        
        Args:
            template_key: Template identifier
            user_message: User's original message (for language detection)
            user_phone: User phone for cost tracking
            **kwargs: Template variables
        
        Returns:
            Response in detected language
        """
        
        # Detect user's language
        detected_lang, confidence = self.detect_language(user_message)
        
        print(f"🌍 Detected language: {detected_lang.value} (confidence: {confidence:.2f})")
        
        # Get template in detected language
        if detected_lang == Language.ARABIC:
            response = self.get_template_response(template_key, Language.ARABIC, **kwargs)
        elif detected_lang == Language.MIXED:
            # For Arabish, respond in English
            response = self.get_template_response(template_key, Language.ENGLISH, **kwargs)
        else:
            response = self.get_template_response(template_key, Language.ENGLISH, **kwargs)
        
        return response
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def format_rtl(self, text: str) -> str:
        """
        Format text for right-to-left display (Arabic)
        Adds RTL Unicode markers if needed
        """
        
        # Check if text contains Arabic
        if re.search(r'[\u0600-\u06FF]', text):
            # Add RTL mark at start
            return '\u200F' + text
        
        return text
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [lang.value for lang in Language]
    
    def get_cache_stats(self) -> Dict:
        """Get translation cache statistics"""
        return {
            "size": len(self._cache._cache),
            "max_size": self._cache._max_size,
            "utilization": f"{len(self._cache._cache) / self._cache._max_size * 100:.1f}%"
        }


# Global instance
multilingual_service = MultilingualService()