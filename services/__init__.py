"""
Services Initialization Module
Handles dynamic loading of messaging service (Gallabox/Twilio/Mock)
"""

from config.settings import settings
from typing import Any

print(f"\n{'='*70}")
print("🔧 SERVICES INITIALIZATION")
print(f"{'='*70}")

# Display configuration
print(f"📋 Configuration:")
print(f"   USE_TWILIO: {settings.USE_TWILIO}")
print(f"   MOCK_MODE: {settings.MOCK_MODE}")
print(f"   NODE_ENV: {settings.NODE_ENV}")

# Validate credentials
twilio_configured = bool(
    settings.TWILIO_ACCOUNT_SID and 
    settings.TWILIO_AUTH_TOKEN and 
    settings.TWILIO_PHONE_NUMBER
)
gallabox_configured = bool(
    settings.GALLABOX_API_KEY and 
    settings.GALLABOX_API_SECRET and 
    settings.GALLABOX_CHANNEL_ID
)

print(f"   Twilio: {'✅ Configured' if twilio_configured else '❌ Not configured'}")
print(f"   Gallabox: {'✅ Configured' if gallabox_configured else '❌ Not configured'}")
print(f"{'='*70}")

# Initialize messaging service
gallabox_service: Any = None

try:
    # PRIORITY 1: Mock Mode (for testing)
    if settings.MOCK_MODE:
        print("🧪 Loading MOCK Service (Test Mode)...")
        from services.gallabox_service_mock import MockGallaboxService
        gallabox_service = MockGallaboxService()
        print("✅ Mock service loaded successfully")
        print(f"   Type: {type(gallabox_service).__name__}")
    
    # PRIORITY 2: Twilio (for sandbox testing)
    elif settings.USE_TWILIO:
        print("📱 Loading TWILIO Service...")
        
        if not twilio_configured:
            raise ValueError(
                "Twilio credentials missing! Set: TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER"
            )
        
        from services.twilio_service import twilio_service
        gallabox_service = twilio_service
        print("✅ Twilio service loaded successfully")
        print(f"   Type: {type(gallabox_service).__name__}")
        print(f"   From: {settings.TWILIO_PHONE_NUMBER}")
    
    # PRIORITY 3: Gallabox (production)
    else:
        print("🔌 Loading GALLABOX Service (Production)...")
        
        if not gallabox_configured:
            raise ValueError(
                "Gallabox credentials missing! Set: GALLABOX_API_KEY, "
                "GALLABOX_API_SECRET, GALLABOX_CHANNEL_ID"
            )
        
        from services.gallabox_service import gallabox_service as gb_service
        gallabox_service = gb_service
        print("✅ Gallabox service loaded successfully")
        print(f"   Type: {type(gallabox_service).__name__}")
        print(f"   Channel: {settings.GALLABOX_CHANNEL_ID}")

except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print(f"   Failed to import messaging service")
    print(f"   Check if service file exists and has no syntax errors")
    import traceback
    traceback.print_exc()
    
    # Fallback to mock service
    print("\n⚠️ FALLBACK: Loading Mock Service as emergency fallback")
    try:
        from services.gallabox_service_mock import MockGallaboxService
        gallabox_service = MockGallaboxService()
        print("✅ Fallback mock service loaded")
    except:
        print("❌ Even fallback failed - critical error!")
        raise

except ValueError as e:
    print(f"\n❌ CONFIGURATION ERROR: {e}")
    print(f"   Check your .env file for missing credentials")
    
    # Fallback to mock
    print("\n⚠️ FALLBACK: Using Mock Service due to missing credentials")
    from services.gallabox_service_mock import MockGallaboxService
    gallabox_service = MockGallaboxService()
    print("✅ Fallback mock service loaded")

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    # Last resort fallback
    print("\n⚠️ EMERGENCY FALLBACK: Attempting mock service")
    try:
        from services.gallabox_service_mock import MockGallaboxService
        gallabox_service = MockGallaboxService()
        print("✅ Emergency fallback successful")
    except:
        print("❌ All fallbacks failed - cannot initialize messaging service")
        raise RuntimeError("Failed to initialize any messaging service")

# Final validation
if gallabox_service is None:
    raise RuntimeError("Messaging service is None - initialization failed")

print(f"\n{'='*70}")
print(f"✅ ACTIVE SERVICE: {type(gallabox_service).__name__}")
print(f"{'='*70}\n")

# Export
__all__ = ['gallabox_service']