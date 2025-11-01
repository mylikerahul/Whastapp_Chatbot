from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from datetime import datetime

# Import settings first
from config.settings import settings

# Import routes
from routes.webhook import router as webhook_router

# Import services (gallabox_service will be loaded via centralized loader)
from services.jira_service import jira_service
from services import gallabox_service  # ⬅️ CENTRALIZED IMPORT
from services.openai_service import openai_service
from services.intent_service import intent_service
from services.cost_tracker import cost_tracker
from services.analytics_service import analytics_service
from services.sentiment_service import sentiment_analyzer
from services.vip_detection import vip_detection_service
from services.response_service import response_service

print(f"🎯 Main.py loaded gallabox: {type(gallabox_service).__name__}")

# ==========================================
# LIFECYCLE MANAGEMENT
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    # Startup
    print("\n" + "="*70)
    print("🚀 WhatsApp Support Agent - Starting Up")
    print("="*70)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏢 Company: {settings.COMPANY_NAME}")
    print(f"📱 WhatsApp: {settings.WHATSAPP_BUSINESS_NUMBER}")
    print(f"🌐 Environment: {settings.NODE_ENV}")
    print(f"🧪 Mock Mode: {settings.MOCK_MODE}")
    print(f"📦 Gallabox Service: {type(gallabox_service).__name__}")
    print("="*70)
    
    # Test Jira connection
    print("\n🔍 Testing integrations...")
    jira_connected = await jira_service.test_jira_connection()
    print(f"   {'✅' if jira_connected else '❌'} Jira: {settings.JIRA_HOST}")
    print(f"   ✅ OpenAI: {settings.OPENAI_MODEL}")
    print(f"   ✅ Gallabox: {settings.GALLABOX_API_URL}")
    
    # Load Jira projects
    if jira_connected:
        print("\n📊 Loading Jira projects...")
        projects = await jira_service.get_all_projects()
        print(f"   ✅ Loaded {len(projects)} projects")
    
    print("\n" + "="*70)
    print("✅ System Ready - Listening for webhooks")
    print("="*70 + "\n")
    
    yield
    
    # Shutdown
    print("\n" + "="*70)
    print("🛑 WhatsApp Support Agent - Shutting Down")
    print("="*70)
    
    # Export analytics
    print("\n📊 Exporting analytics...")
    analytics = analytics_service.export_analytics()
    print(f"   Total messages processed: {analytics['realtime_metrics']['current_hour']['messages']}")
    print(f"   Total tickets created: {analytics['realtime_metrics']['current_hour']['tickets_created']}")
    
    # Export cost data
    print("\n💰 Cost summary:")
    daily_cost = cost_tracker.get_daily_summary()
    print(f"   OpenAI: ${daily_cost['openai_cost']:.4f}")
    print(f"   Gallabox: ${daily_cost['gallabox_cost']:.4f}")
    print(f"   Total: ${daily_cost['total_cost']:.4f}")
    
    print("\n" + "="*70)
    print("👋 Goodbye!")
    print("="*70 + "\n")

# ==========================================
# CREATE FASTAPI APP
# ==========================================

app = FastAPI(
    title="WhatsApp Support Agent API",
    description="AI-powered WhatsApp support with Jira integration",
    version="2.0.0",
    lifespan=lifespan
)

# ==========================================
# MIDDLEWARE
# ==========================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGIN.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # Track in analytics
    analytics_service.track_response_time(duration_ms)
    
    # Log
    print(f"📡 {request.method} {request.url.path} - {response.status_code} - {duration_ms}ms")
    
    return response

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unhandled exception: {exc}")
    
    # Track error
    analytics_service.track_error(
        error_type=type(exc).__name__,
        error_message=str(exc),
        context={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.NODE_ENV == "development" else "An error occurred"
        }
    )

# ==========================================
# INCLUDE ROUTERS
# ==========================================

app.include_router(webhook_router, tags=["Webhook"])


# ==========================================
# HEALTH & STATUS ENDPOINTS
# ==========================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "WhatsApp Support Agent",
        "version": "2.0.0",
        "company": settings.COMPANY_NAME,
        "status": "operational",
        "mock_mode": settings.MOCK_MODE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    jira_status = await jira_service.test_jira_connection()
    
    return {
        "status": "healthy" if jira_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": settings.MOCK_MODE,
        "services": {
            "jira": "connected" if jira_status else "disconnected",
            "openai": "configured",
            "gallabox": "configured",
            "analytics": "operational"
        },
        "metrics": analytics_service.get_realtime_metrics()
    }

@app.get("/api/status")
async def system_status():
    """Detailed system status"""
    return {
        "server": {
            "environment": settings.NODE_ENV,
            "mock_mode": settings.MOCK_MODE,
            "uptime": "running"
        },
        "integrations": {
            "jira": {
                "host": settings.JIRA_HOST,
                "project": settings.JIRA_PROJECT_KEY
            },
            "openai": {
                "model": settings.OPENAI_MODEL,
                "cache_stats": openai_service.get_cache_stats()
            },
            "gallabox": {
                "number": settings.WHATSAPP_BUSINESS_NUMBER,
                "service_type": type(gallabox_service).__name__,
                "rate_limit_stats": gallabox_service.get_rate_limit_stats()
            }
        },
        "analytics": analytics_service.get_realtime_metrics(),
        "cost": cost_tracker.get_daily_summary()
    }

# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@app.get("/api/analytics/realtime")
async def get_realtime_analytics():
    """Get real-time metrics"""
    return analytics_service.get_realtime_metrics()

@app.get("/api/analytics/intents")
async def get_intent_analytics():
    """Get intent distribution"""
    return {
        "intent_distribution": analytics_service.get_intent_distribution(),
        "cost_by_intent": cost_tracker.get_intent_analytics()
    }

@app.get("/api/analytics/hourly")
async def get_hourly_analytics(hours: int = 24):
    """Get hourly breakdown"""
    return {
        "hours": min(hours, 168),  # Max 1 week
        "data": analytics_service.get_hourly_summary(hours)
    }

@app.get("/api/analytics/daily")
async def get_daily_analytics(date: str = None):
    """Get daily summary"""
    return analytics_service.get_daily_summary(date)

# ==========================================
# COST TRACKING ENDPOINTS
# ==========================================

@app.get("/api/cost/daily")
async def get_daily_cost(date: str = None):
    """Get daily cost breakdown"""
    return cost_tracker.get_daily_summary(date)

@app.get("/api/cost/monthly")
async def get_monthly_cost(year: int = None, month: int = None):
    """Get monthly cost summary"""
    return cost_tracker.get_monthly_summary(year, month)

@app.get("/api/cost/top-users")
async def get_top_cost_users(limit: int = 10):
    """Get users with highest costs"""
    return {
        "limit": limit,
        "users": cost_tracker.get_top_users_by_cost(limit)
    }

# ==========================================
# VIP MANAGEMENT ENDPOINTS
# ==========================================

@app.post("/api/vip/register")
async def register_vip(request: Request):
    """Register a VIP client"""
    data = await request.json()
    
    phone = data.get("phone")
    name = data.get("name")
    tier = data.get("tier", "gold")
    
    if not phone or not name:
        raise HTTPException(400, "Phone and name required")
    
    vip_detection_service.register_vip(phone, name, tier)
    
    return {
        "success": True,
        "message": f"VIP registered: {name}",
        "tier": tier
    }

@app.get("/api/vip/list")
async def list_vips():
    """Get all registered VIPs"""
    return {
        "vips": vip_detection_service.get_all_vips(),
        "count": len(vip_detection_service.get_all_vips())
    }

@app.delete("/api/vip/{phone}")
async def remove_vip(phone: str):
    """Remove VIP status"""
    vip_detection_service.remove_vip(phone)
    return {
        "success": True,
        "message": f"VIP removed: {phone}"
    }

# ==========================================
# ADMIN ENDPOINTS
# ==========================================

@app.post("/api/admin/clear-cache")
async def clear_cache():
    """Clear OpenAI response cache"""
    openai_service._cache._cache.clear()
    openai_service._cache._timestamps.clear()
    
    return {
        "success": True,
        "message": "Cache cleared"
    }

@app.post("/api/admin/reset-circuit-breaker")
async def reset_circuit_breaker():
    """Reset Gallabox circuit breaker"""
    gallabox_service.reset_circuit_breaker()
    
    return {
        "success": True,
        "message": "Circuit breaker reset"
    }

@app.get("/api/admin/pending-tickets")
async def get_pending_tickets():
    """Get all pending tickets"""
    tickets = response_service.get_all_pending_tickets()
    
    return {
        "count": len(tickets),
        "tickets": {
            phone: {
                "summary": ticket.summary,
                "team": ticket.team,
                "priority": ticket.priority.value,
                "timestamp": ticket.timestamp.isoformat()
            }
            for phone, ticket in tickets.items()
        }
    }

@app.post("/api/admin/cleanup")
async def cleanup_old_data():
    """Cleanup old pending tickets and data"""
    cleaned = response_service.cleanup_old_pending_tickets()
    
    return {
        "success": True,
        "pending_tickets_cleaned": cleaned
    }

@app.get("/api/admin/errors")
async def get_recent_errors(limit: int = 20):
    """Get recent errors"""
    return {
        "errors": analytics_service.get_recent_errors(limit),
        "count": len(analytics_service.get_recent_errors(limit))
    }

# ==========================================
# TESTING ENDPOINTS
# ==========================================

@app.post("/api/test/sentiment")
async def test_sentiment(request: Request):
    """Test sentiment analysis"""
    data = await request.json()
    message = data.get("message", "")
    
    if not message:
        raise HTTPException(400, "Message required")
    
    result = sentiment_analyzer.analyze_sentiment(message)
    
    return result

@app.post("/api/test/vip-detection")
async def test_vip_detection(request: Request):
    """Test VIP detection"""
    data = await request.json()
    message = data.get("message", "")
    phone = data.get("phone", "+971501234567")
    
    if not message:
        raise HTTPException(400, "Message required")
    
    result = vip_detection_service.detect_vip(message, phone)
    
    return result

# ==========================================
# 🧪 MOCK MODE ENDPOINTS - UPDATED
# ==========================================

@app.get("/api/mock/status")
async def mock_status():
    """Check if running in mock mode"""
    from services import gallabox_service
    
    return {
        "mock_mode": settings.MOCK_MODE,
        "service_type": type(gallabox_service).__name__,
        "has_message_store": hasattr(gallabox_service, '_message_store'),
        "stats": gallabox_service.get_stats() if hasattr(gallabox_service, 'get_stats') else {}
    }

@app.get("/api/mock/messages")
async def get_mock_messages(phone: str = None):
    """Get all mock messages sent"""
    from services import gallabox_service
    
    if not settings.MOCK_MODE:
        raise HTTPException(400, "Not in mock mode")
    
    try:
        if phone:
            messages = gallabox_service.get_messages_for_user(phone)
        else:
            messages = gallabox_service.get_all_messages()
        
        return {
            "mock_mode": True,
            "service_type": type(gallabox_service).__name__,
            "count": len(messages),
            "messages": messages
        }
    except AttributeError as e:
        return {
            "error": f"Method not available: {e}",
            "service_type": type(gallabox_service).__name__,
            "available_methods": dir(gallabox_service)
        }

@app.post("/api/mock/clear")
async def clear_mock_messages():
    """Clear all mock messages"""
    from services import gallabox_service
    
    if not settings.MOCK_MODE:
        raise HTTPException(400, "Not in mock mode")
    
    gallabox_service.clear_messages()
    
    return {
        "success": True,
        "message": "Mock messages cleared"
    }

@app.post("/api/mock/failures/enable")
async def enable_failure_simulation(rate: float = 0.1):
    """Enable failure simulation"""
    from services import gallabox_service
    
    if not settings.MOCK_MODE:
        raise HTTPException(400, "Not in mock mode")
    
    gallabox_service.enable_failure_simulation(rate)
    
    return {
        "success": True,
        "failure_rate": rate
    }

@app.post("/api/mock/failures/disable")
async def disable_failure_simulation():
    """Disable failure simulation"""
    from services import gallabox_service
    
    if not settings.MOCK_MODE:
        raise HTTPException(400, "Not in mock mode")
    
    gallabox_service.disable_failure_simulation()
    
    return {
        "success": True
    }

# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.NODE_ENV == "development",
        log_level=settings.LOG_LEVEL.lower()
    )