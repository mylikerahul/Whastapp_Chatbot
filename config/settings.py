# config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # ===========================
    # 🔑 GALLABOX API CREDENTIALS
    # ===========================
    GALLABOX_API_URL: str
    GALLABOX_API_KEY: str
    GALLABOX_API_SECRET: str
    GALLABOX_CHANNEL_ID: str
    VERIFY_TOKEN: str
    GALLABOX_WEBHOOK_SECRET: Optional[str] = None

    # ===========================
    # 📱 TWILIO CREDENTIALS
    # ===========================
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # ===========================
    # 🎯 ADVANCED FEATURES
    # ===========================
    ENABLE_SENTIMENT_ANALYSIS: bool = False
    ENABLE_VIP_DETECTION: bool = False
    ENABLE_AUTO_ESCALATION: bool = False
    ENABLE_RESPONSE_CACHE: bool = False

    RESPONSE_CACHE_SIZE: int = 1000
    RESPONSE_CACHE_TTL_MINUTES: int = 60

    VIP_AUTO_ESCALATE: bool = False
    VIP_PRIORITY_BOOST: bool = False

    SENTIMENT_ESCALATION_THRESHOLD: int = 7
    FRUSTRATION_WINDOW_MINUTES: int = 30

    # ===========================
    # 💬 WHATSAPP BOT CONFIG
    # ===========================
    WHATSAPP_BUSINESS_NUMBER: str
    WHATSAPP_BUSINESS_NAME: str
    WHATSAPP_BUSINESS_WEBSITE: str
    WHATSAPP_BUSINESS_EMAIL: str
    WHATSAPP_WABA_ID: Optional[str] = None
    WHATSAPP_QUALITY: Optional[str] = None
    WHATSAPP_MESSAGE_LIMIT: Optional[int] = None

    # ===========================
    # 🤖 OPENAI/GPT CONFIG
    # ===========================
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 500
    OPENAI_TEMPERATURE: float = 0.7

    # ===========================
    # ⚙️ JIRA INTEGRATION
    # ===========================
    JIRA_HOST: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: str
    JIRA_PROJECT_KEY: str

    # ===========================
    # ☁️ AWS CONFIG
    # ===========================
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str
    AWS_S3_PREFIX: str
    AWS_ATHENA_DATABASE: Optional[str] = None
    AWS_ATHENA_OUTPUT_LOCATION: Optional[str] = None

    # ===========================
    # 🌐 SERVER & APP CONFIG
    # ===========================
    PORT: int = 8080
    BASE_URL: str
    NODE_ENV: str = "development"
    LOG_LEVEL: str = "debug"
    CORS_ORIGIN: str
    RATE_LIMIT_WINDOW_MS: int = 900000
    RATE_LIMIT_MAX_REQUESTS: int = 100
    WEBHOOK_URL: Optional[str] = None
    COMPANY_NAME: str = "Sothebys Real Estate"
    
    JWT_SECRET: Optional[str] = None
    JWT_EXPIRES_IN: Optional[str] = None

    # ===========================
    # 🧪 MODE CONFIGURATION
    # ===========================
    USE_TWILIO: bool = False  # ✅ ADD THIS LINE
    MOCK_MODE: bool = False
    MOCK_SIMULATE_FAILURES: bool = False
    MOCK_FAILURE_RATE: float = 0.1

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

# Print mode on startup
if settings.MOCK_MODE:
    print("\n" + "="*70)
    print("🧪 RUNNING IN MOCK MODE - NO REAL API CALLS")
    print("="*70 + "\n")
elif settings.USE_TWILIO:  # ✅ Use settings.USE_TWILIO instead of os.getenv
    print("\n" + "="*70)
    print("📱 TWILIO MODE - USING TWILIO FOR MESSAGING")
    print("="*70 + "\n")
else:
    print("\n" + "="*70)
    print("🚀 PRODUCTION MODE - REAL GALLABOX API")
    print("="*70 + "\n")