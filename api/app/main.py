"""
FastAPI main application.

CRITICAL DESIGN PRINCIPLES:
1. This API is READ-ONLY and deterministic
2. NO AI/LLM calls in request handlers
3. NO agent execution in request path
4. All recommendations are pre-computed offline
5. Responses are cacheable for performance

If it can "think", it cannot block a request.
If it serves a request, it must not think.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .core.config import settings
from .routes import health_router, recommendations_router, game_router, news_router, multiplayer_router
from .scheduler import start_scheduler, stop_scheduler

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Stock AI Platform API - Serves pre-computed AI recommendations. "
        "All AI processing happens offline. This API is read-only and deterministic."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(recommendations_router, prefix=settings.API_PREFIX)
app.include_router(game_router)
app.include_router(news_router)
app.include_router(multiplayer_router)


@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API docs available at: http://192.168.5.126:{settings.API_PORT}/docs")

    # Start auto-advance scheduler for sync_auto mode
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks."""
    logger.info("Shutting down application")

    # Stop scheduler
    stop_scheduler()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
