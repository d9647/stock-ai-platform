"""
Multiplayer game room models for classroom competition.
Teachers create rooms, students join and compete on same dataset.
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

import uuid
import random
import string

from ..db.base import Base


def generate_room_code() -> str:
    """Generate a 6-character room code (e.g., ABC123)."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class GameRoom(Base):
    """
    Multiplayer game room for classroom competition.
    All players in a room play the same game (same dates, same tickers).
    """
    __tablename__ = "game_rooms"
    __table_args__ = (
        Index("idx_room_code", "room_code", unique=True),
        Index("idx_room_status", "status"),
        {"schema": "multiplayer"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_code = Column(String(6), nullable=False, unique=True, default=generate_room_code)

    # Room metadata
    created_by = Column(String(100), nullable=False)  # Teacher/creator name
    room_name = Column(String(200))  # Optional friendly name

    # Game configuration (stored as JSON)
    config = Column(JSON, nullable=False)  # GameConfig: {initialCash, numDays, tickers, difficulty}

    # Game date range (all players use same data)
    start_date = Column(String(10), nullable=False)  # ISO date: YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # ISO date: YYYY-MM-DD
    current_date = Column(String(10), nullable=True)

    # Room status
    status = Column(
        String(20),
        nullable=False,
        default='waiting',
        # waiting: accepting players
        # in_progress: game started
        # finished: game completed
    )

    # Sync mode fields (for Kahoot-style synchronous gameplay)
    game_mode = Column(String(20), nullable=False, default='async')  # 'async', 'sync', or 'sync_auto'
    current_day = Column(Integer, nullable=False, default=0)  # Current day for sync mode
    day_time_limit = Column(Integer)  # Seconds per day (optional timer)
    day_duration_seconds = Column(Integer)  # Auto-advance interval for sync_auto mode
    day_started_at = Column(DateTime(timezone=True))  # When current day started

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))  # When game started (legacy)
    game_started_at = Column(DateTime(timezone=True))  # When teacher started game (sync mode)
    game_ended_at = Column(DateTime(timezone=True))  # When teacher ended game (sync mode)
    finished_at = Column(DateTime(timezone=True))  # When game ended (legacy)


    # Relationships
    players = relationship("Player", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameRoom(code={self.room_code}, status={self.status}, players={len(self.players)})>"


class Player(Base):
    """
    A player in a multiplayer game room.
    Stores complete game state for leaderboard and replay.
    """
    __tablename__ = "players"
    __table_args__ = (
        Index("idx_player_room", "room_id"),
        Index("idx_player_name", "player_name"),
        {"schema": "multiplayer"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("multiplayer.game_rooms.id", ondelete="CASCADE"), nullable=False)

    # Player identity
    player_name = Column(String(100), nullable=False)
    player_email = Column(String(200))  # Optional for teacher tracking

    # Game progress
    current_day = Column(Integer, nullable=False, default=0)  # 0-indexed
    is_finished = Column(Boolean, nullable=False, default=False)

    # Portfolio state (latest snapshot)
    cash = Column(Float, nullable=False)
    holdings = Column(JSON, nullable=False, default=dict)  # {ticker: {shares, avgCost}}
    trades = Column(JSON, nullable=False, default=list)  # List of all trades

    # Performance metrics
    portfolio_value = Column(Float, nullable=False)  # Cash + holdings value
    total_return_pct = Column(Float, nullable=False, default=0.0)  # % return
    total_return_usd = Column(Float, nullable=False, default=0.0)  # $ return

    # Scoring
    score = Column(Float, nullable=False, default=0.0)
    grade = Column(String(2), nullable=False, default='C')
    score_breakdown = Column(JSON)  # Detailed scoring breakdown

    # History for charts
    portfolio_history = Column(JSON, nullable=False, default=list)  # Daily snapshots

    # Sync mode fields
    is_ready = Column(Boolean, nullable=False, default=False)  # Ready for next day
    last_sync_day = Column(Integer, nullable=False, default=0)  # Last day synced to

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_action_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    finished_at = Column(DateTime(timezone=True))

    # Relationships
    room = relationship("GameRoom", back_populates="players")

    def __repr__(self):
        return f"<Player(name={self.player_name}, room={self.room_id}, day={self.current_day})>"
