"""API routes."""

from .health import router as health_router
from .recommendations import router as recommendations_router
from .game import router as game_router
from .news import router as news_router
from .multiplayer import router as multiplayer_router

__all__ = ["health_router", "recommendations_router", "game_router", "news_router", "multiplayer_router"]
