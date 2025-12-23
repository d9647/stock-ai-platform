"""
Pydantic schemas for multiplayer API end points.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class GameConfigSchema(BaseModel):
    """Game configuration for a room."""
    initial_cash: int = Field(default=10000, description="Starting cash for each player")
    num_days: int = Field(default=30, ge=1, le=90, description="Number of calendar days")
    tickers: List[str] = Field(default=["AAPL", "MSFT", "GOOGL", "AMZN"], description="Stock tickers to trade")
    difficulty: str = Field(default="medium", description="Game difficulty: easy, medium, hard")


class CreateRoomRequest(BaseModel):
    """Request to create a new game room."""
    created_by: str = Field(..., min_length=1, max_length=100, description="Teacher/creator name")
    room_name: Optional[str] = Field(None, max_length=200, description="Optional friendly room name")
    config: GameConfigSchema = Field(default_factory=GameConfigSchema)
    start_date: Optional[str] = Field(None, description="Game start date (YYYY-MM-DD), defaults to latest data minus numDays")
    end_date: Optional[str] = Field(None, description="Game end date (YYYY-MM-DD), defaults to latest available data")
    game_mode: str = Field(default="async", description="Game mode: 'async' or 'sync_auto' or 'sync'")
    day_duration_seconds: Optional[int] = None

class JoinRoomRequest(BaseModel):
    """Request to join an existing game room."""
    room_code: str = Field(..., min_length=6, max_length=6, description="6-character room code")
    player_name: str = Field(..., min_length=1, max_length=100, description="Player name")
    player_email: Optional[str] = Field(None, max_length=200, description="Optional email")


class PlayerResponse(BaseModel):
    """Player information in a room."""
    id: str
    player_name: str
    player_email: Optional[str]
    current_day: int
    is_finished: bool
    cash: float
    portfolio_value: float
    total_return_pct: float
    total_return_usd: float
    score: float
    grade: str
    is_ready: bool = False
    last_sync_day: int = 0
    joined_at: str
    last_action_at: str

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Leaderboard entry for a player."""
    rank: int
    player_id: str
    player_name: str
    score: float
    grade: str
    portfolio_value: float
    total_return_pct: float
    current_day: int
    is_finished: bool


class RoomResponse(BaseModel):
    """Complete room information."""
    id: str
    room_code: str
    created_by: str
    room_name: Optional[str]
    config: Dict[str, Any]
    # The `start_date` field in the `CreateRoomRequest` schema is used to specify the start date for
    # the game. It is an optional field that allows the user to set a specific start date for the game
    # in the format "YYYY-MM-DD". If this field is not provided, the game will default to starting
    # with the latest available data minus the number of days specified in the `num_days` field of the
    # `GameConfigSchema`.
    start_date: str
    end_date: str
    status: str
    game_mode: str = "async"  # 'async', 'sync', or 'sync_auto'
    current_day: int = 0
    current_date: Optional[str] = None
    day_time_limit: Optional[int] = None
    day_duration_seconds: Optional[int] = None
    day_started_at: Optional[str] = None
    created_at: str
    started_at: Optional[str]
    game_started_at: Optional[str] = None
    game_ended_at: Optional[str] = None
    finished_at: Optional[str]
    player_count: int
    players: List[PlayerResponse]

    class Config:
        from_attributes = True


class RoomSummary(BaseModel):
    """Brief room information for listings."""
    id: str
    room_code: str
    created_by: str
    room_name: Optional[str]
    status: str
    game_mode: str = "async"  # 'async', 'sync', or 'sync_auto'
    player_count: int
    created_at: str
    config: Dict[str, Any]

    class Config:
        from_attributes = True


class UpdatePlayerStateRequest(BaseModel):
    """Update player's game state (called after each day)."""
    current_day: int
    cash: float
    holdings: Dict[str, Any]  # {ticker: {shares, avgCost}}
    trades: List[Dict[str, Any]]  # List of all trades
    portfolio_value: float
    total_return_pct: float
    total_return_usd: float
    score: float
    grade: str
    score_breakdown: Optional[Dict[str, Any]]
    portfolio_history: List[Dict[str, Any]]
    is_finished: bool = False


# New schemas for sync mode

class StartGameRequest(BaseModel):
    """Request to start the game (teacher only)."""
    started_by: str = Field(..., description="Teacher ID or name")


class AdvanceDayRequest(BaseModel):
    """Request to advance all players to next day (teacher only)."""
    initiated_by: str = Field(..., description="Teacher ID or name")
    day_time_limit: Optional[int] = Field(None, description="Optional time limit in seconds for next day")


class EndGameRequest(BaseModel):
    """Request to end the game for everyone (teacher only)."""
    ended_by: str = Field(..., description="Teacher ID or name")


class SetTimerRequest(BaseModel):
    """Request to set/update timer for current day."""
    duration_seconds: int = Field(..., ge=0, le=3600, description="Timer duration in seconds (0 = no timer)")


class RoomStateResponse(BaseModel):
    """Current state of the room for sync mode."""
    room_code: str
    status: str  # 'waiting', 'in_progress', 'finished'
    game_mode: str  # 'async' or 'sync'
    current_day: int
    day_started_at: Optional[str]
    day_time_limit: Optional[int]
    time_remaining: Optional[int]  # Calculated from day_started_at + day_time_limit
    waiting_for_teacher: bool
    ready_count: int  # Number of players ready
    total_players: int


class PlayerReadyRequest(BaseModel):
    """Mark player as ready for next day."""
    pass  # No fields needed, player ID comes from URL
