"""
Multiplayer game room API end points.
Teachers create rooms, students join, compete on same dataset.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, timedelta

from ..db import get_db
from ..models.multiplayer import GameRoom, Player
from ..models.agents import StockRecommendation
from ..schemas.multiplayer import (
    CreateRoomRequest,
    JoinRoomRequest,
    RoomResponse,
    RoomSummary,
    PlayerResponse,
    LeaderboardEntry,
    UpdatePlayerStateRequest,
    StartGameRequest,
    AdvanceDayRequest,
    EndGameRequest,
    SetTimerRequest,
    RoomStateResponse,
    PlayerReadyRequest,
)

router = APIRouter(prefix="/api/v1/multiplayer", tags=["multiplayer"])


@router.post("/rooms", response_model=RoomResponse)
async def create_room(request: CreateRoomRequest, db: Session = Depends(get_db)):
    """
    Create a new multiplayer game room.
    Teacher/creator specifies game configuration.
    """
    # Determine game date range
    if request.end_date:
        end_dt = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    else:
        # Use latest available data
        latest_rec = db.query(StockRecommendation).order_by(
            StockRecommendation.as_of_date.desc()
        ).first()
        if not latest_rec:
            raise HTTPException(
                status_code=404,
                detail="No market data available"
            )
        end_dt = latest_rec.as_of_date

    if request.start_date:
        start_dt = datetime.strptime(request.start_date, "%Y-%m-%d").date()
    else:
        # Calculate from end_date and num_days
        start_dt = end_dt - timedelta(days=request.config.num_days - 1)

    # Create room
    room = GameRoom(
        created_by=request.created_by,
        room_name=request.room_name,
        config={
            "initialCash": request.config.initial_cash,
            "numDays": request.config.num_days,
            "tickers": request.config.tickers,
            "difficulty": request.config.difficulty,
        },
        start_date=start_dt.isoformat(),
        end_date=end_dt.isoformat(),
        status="waiting",
        game_mode=request.game_mode,
        day_duration_seconds=request.day_duration_seconds,
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return _build_room_response(room)


@router.post("/rooms/join", response_model=PlayerResponse)
async def join_room(request: JoinRoomRequest, db: Session = Depends(get_db)):
    """
    Join an existing game room as a player.
    """
    # Find room by code
    room = db.query(GameRoom).filter(
        GameRoom.room_code == request.room_code.upper()
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with code {request.room_code} not found"
        )

    if room.status == "finished":
        raise HTTPException(
            status_code=400,
            detail="This room has already finished. Cannot join."
        )

    # Check if player name already exists in this room
    existing_player = db.query(Player).filter(
        Player.room_id == room.id,
        Player.player_name == request.player_name
    ).first()

    if existing_player:
        raise HTTPException(
            status_code=400,
            detail=f"Player name '{request.player_name}' is already taken in this room"
        )

    # Create player
    initial_cash = room.config.get("initialCash", 100000)
    player = Player(
        room_id=room.id,
        player_name=request.player_name,
        player_email=request.player_email,
        current_day=0,
        cash=initial_cash,
        holdings={},
        trades=[],
        portfolio_value=initial_cash,
        total_return_pct=0.0,
        total_return_usd=0.0,
        score=0.0,
        grade='C',
        portfolio_history=[],
        is_finished=False,
    )

    db.add(player)

    # Auto-start room if it's first player joining (async mode only)
    # In sync mode, teacher explicitly starts via /start endpoint
    if room.status == "waiting" and len(room.players) == 0 and room.game_mode == "async":
        room.status = "in_progress"
        room.started_at = datetime.utcnow()

    db.commit()
    db.refresh(player)

    return PlayerResponse(
        id=str(player.id),
        player_name=player.player_name,
        player_email=player.player_email,
        current_day=player.current_day,
        is_finished=player.is_finished,
        cash=player.cash,
        portfolio_value=player.portfolio_value,
        total_return_pct=player.total_return_pct,
        total_return_usd=player.total_return_usd,
        score=player.score,
        grade=player.grade,
        joined_at=player.joined_at.isoformat(),
        last_action_at=player.last_action_at.isoformat(),
    )


@router.get("/rooms/{room_code}", response_model=RoomResponse)
async def get_room(room_code: str, db: Session = Depends(get_db)):
    """
    Get complete room information including all players.
    """
    room = db.query(GameRoom).filter(
        GameRoom.room_code == room_code.upper()
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with code {room_code} not found"
        )

    return _build_room_response(room)


@router.get("/rooms/{room_code}/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(room_code: str, db: Session = Depends(get_db)):
    """
    Get leaderboard for a room, sorted by score.
    """
    room = db.query(GameRoom).filter(
        GameRoom.room_code == room_code.upper()
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with code {room_code} not found"
        )

    # Get all players, sorted by score descending
    players = db.query(Player).filter(
        Player.room_id == room.id
    ).order_by(Player.score.desc()).all()

    leaderboard = []
    for rank, player in enumerate(players, start=1):
        leaderboard.append(LeaderboardEntry(
            rank=rank,
            player_id=str(player.id),
            player_name=player.player_name,
            score=player.score,
            grade=player.grade,
            portfolio_value=player.portfolio_value,
            total_return_pct=player.total_return_pct,
            current_day=player.current_day,
            is_finished=player.is_finished,
        ))

    return leaderboard


@router.put("/players/{player_id}", response_model=PlayerResponse)
async def update_player_state(
    player_id: str,
    request: UpdatePlayerStateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a player's game state after completing a day.
    Called by frontend after each day's trading.
    """
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        raise HTTPException(
            status_code=404,
            detail=f"Player {player_id} not found"
        )

    # Update player state
    player.current_day = request.current_day
    player.cash = request.cash
    player.holdings = request.holdings
    player.trades = request.trades
    player.portfolio_value = request.portfolio_value
    player.total_return_pct = request.total_return_pct
    player.total_return_usd = request.total_return_usd
    player.score = request.score
    player.grade = request.grade
    player.score_breakdown = request.score_breakdown
    player.portfolio_history = request.portfolio_history
    player.is_finished = request.is_finished
    player.last_action_at = datetime.utcnow()

    if request.is_finished:
        player.finished_at = datetime.utcnow()

    # Update AI benchmark performance in the room (if provided)
    if request.ai_portfolio_value is not None and request.ai_total_return_pct is not None:
        room = db.query(GameRoom).filter(GameRoom.id == player.room_id).first()
        if room:
            room.ai_portfolio_value = request.ai_portfolio_value
            room.ai_total_return_pct = request.ai_total_return_pct
            room.ai_current_day = request.current_day

    db.commit()
    db.refresh(player)

    return PlayerResponse(
        id=str(player.id),
        player_name=player.player_name,
        player_email=player.player_email,
        current_day=player.current_day,
        is_finished=player.is_finished,
        cash=player.cash,
        portfolio_value=player.portfolio_value,
        total_return_pct=player.total_return_pct,
        total_return_usd=player.total_return_usd,
        score=player.score,
        grade=player.grade,
        joined_at=player.joined_at.isoformat(),
        last_action_at=player.last_action_at.isoformat(),
    )


@router.get("/rooms", response_model=List[RoomSummary])
async def list_rooms(
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all game rooms, optionally filtered by status.
    """
    query = db.query(GameRoom)

    if status:
        query = query.filter(GameRoom.status == status)

    rooms = query.order_by(GameRoom.created_at.desc()).limit(limit).all()

    return [
        RoomSummary(
            id=str(r.id),
            room_code=r.room_code,
            created_by=r.created_by,
            room_name=r.room_name,
            status=r.status,
            game_mode=r.game_mode,
            player_count=len(r.players),
            created_at=r.created_at.isoformat(),
            config=r.config,
        )
        for r in rooms
    ]

# ============================================================================
# Sync Mode (Kahoot-style) End points
# ============================================================================

@router.post("/rooms/{room_code}/start", response_model=RoomResponse)
async def start_game(
    room_code: str,
    request: StartGameRequest,
    db: Session = Depends(get_db)
):
    """
    Start the game for all players (teacher control).
    Transitions from 'waiting' to 'in_progress'.
    For sync mode, this initializes the game at day 0.
    """
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.status != "waiting":
        raise HTTPException(status_code=400, detail=f"Game already {room.status}")

    # Start the game at Day 1 (not Day 0)
    # Day 0 was previously used as a lobby state, but this caused confusion
    # Now game starts immediately at the first trading day
    room.status = "in_progress"
    room.game_started_at = datetime.utcnow()

    # Start at the start_date, which should be a trading day
    # The advance-day endpoint will skip weekends when advancing
    start_date_obj = datetime.fromisoformat(room.start_date).date()
    room.current_date = start_date_obj.isoformat()
    room.current_day = 0  # Day 0 is now the first actual trading day (not a lobby)

    if room.game_mode in ("sync", "sync_auto"):
        room.day_started_at = datetime.utcnow()

    db.commit()
    db.refresh(room)

    return _build_room_response(room)


@router.post("/rooms/{room_code}/advance-day", response_model=RoomResponse)
async def advance_day(
    room_code: str,
    request: AdvanceDayRequest,
    db: Session = Depends(get_db)
):
    """
    Advance all players to the next day (teacher control, sync mode only).
    Resets all players' ready status.
    """
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.game_mode == "async":
        raise HTTPException(status_code=400, detail="Only available in sync mode")

    if room.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Game is not in progress (status: {room.status})")

    # Advance to next day
    # room.current_day += 1
    if room.current_date is None:
        current_date_obj = datetime.fromisoformat(room.start_date).date()
    else:
        current_date_obj = datetime.fromisoformat(room.current_date).date()

    start_dt = datetime.fromisoformat(room.start_date).date()
    current_date_obj = _next_trading_day(current_date_obj)
    room.current_date = current_date_obj.isoformat()
    room.current_day = (current_date_obj - start_dt).days
    room.day_started_at = datetime.utcnow()
    
    # After computing room.current_day
    total_days = room.config.get("numDays")

    if room.current_day >= total_days:
        room.status = "finished"
        room.game_ended_at = datetime.utcnow()

    for player in room.players:
        player.is_finished = True
    
    if request.day_time_limit:
        room.day_time_limit = request.day_time_limit

    # Reset all players' ready status
    for player in room.players:
        player.is_ready = False
        player.last_sync_day = room.current_day

    db.commit()
    db.refresh(room)

    return _build_room_response(room)


@router.post("/rooms/{room_code}/end-game", response_model=RoomResponse)
async def end_game(
    room_code: str,
    request: EndGameRequest,
    db: Session = Depends(get_db)
):
    """
    End the game for all players (teacher control).
    Transitions to 'finished' status.
    """
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.status == "finished":
        raise HTTPException(status_code=400, detail="Game already finished")

    room.status = "finished"
    room.game_ended_at = datetime.utcnow()
    
    # Mark all players as finished
    for player in room.players:
        player.is_finished = True

    db.commit()
    db.refresh(room)

    return _build_room_response(room)


@router.post("/rooms/{room_code}/set-timer", response_model=RoomResponse)
async def set_timer(
    room_code: str,
    request: SetTimerRequest,
    db: Session = Depends(get_db)
):
    """
    Set or update the timer for the current day (sync mode only).
    """
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.game_mode == "async":
        raise HTTPException(status_code=400, detail="Only available in sync mode")

    room.day_time_limit = request.duration_seconds

    # Keep auto-advance duration in sync so scheduler respects updated timer immediately
    if room.game_mode == "sync_auto":
        room.day_duration_seconds = request.duration_seconds
    
    # Reset day start time when timer is set
    if request.duration_seconds > 0:
        room.day_started_at = datetime.utcnow()

    db.commit()
    db.refresh(room)

    return _build_room_response(room)


@router.get("/rooms/{room_code}/state", response_model=RoomStateResponse)
async def get_room_state(room_code: str, db: Session = Depends(get_db)):
    """
    Get current room state for sync mode (polled by students).
    Returns current day, timer info, and ready count.
    """
    room = db.query(GameRoom).filter(GameRoom.room_code == room_code.upper()).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    ready_count = sum(1 for p in room.players if p.is_ready)
    total_players = len(room.players)

    # Calculate time remaining
    time_remaining = None
    # Prefer explicit day_time_limit; fall back to sync_auto day_duration_seconds; default 30s for sync_auto
    timer_limit = room.day_time_limit or (
        room.game_mode == "sync_auto" and (room.day_duration_seconds or 30)
    )
    if timer_limit and room.day_started_at:
        elapsed = (datetime.utcnow() - room.day_started_at).total_seconds()
        time_remaining = max(0, int(timer_limit - elapsed))
    elif timer_limit:
        time_remaining = int(timer_limit)

    return RoomStateResponse(
        room_code=room.room_code,
        status=room.status,
        game_mode=room.game_mode,
        current_day=room.current_day,
        day_started_at=room.day_started_at.isoformat() if room.day_started_at else None,
        day_time_limit=room.day_time_limit,
        time_remaining=time_remaining,
        waiting_for_teacher=room.game_mode == "sync" and room.status == "in_progress",
        ready_count=ready_count,
        total_players=total_players,
    )


@router.post("/players/{player_id}/ready", response_model=PlayerResponse)
async def mark_player_ready(player_id: str, db: Session = Depends(get_db)):
    """
    Mark a player as ready for the next day (sync mode only).
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    room = player.room
    if room.game_mode == "async":
        raise HTTPException(status_code=400, detail="Only available in sync mode")

    player.is_ready = True
    db.commit()
    db.refresh(player)
    
    print("READY:", player.player_name, "room status:", room.status)


    return _build_player_response(player)


# Helper function to build RoomResponse
def _build_room_response(room: GameRoom) -> RoomResponse:
    """Build RoomResponse from GameRoom model."""
    return RoomResponse(
        id=str(room.id),
        room_code=room.room_code,
        created_by=room.created_by,
        room_name=room.room_name,
        config=room.config,
        start_date=room.start_date,
        end_date=room.end_date,
        status=room.status,
        game_mode=room.game_mode,
        current_day=room.current_day,
        current_date=room.current_date,
        day_time_limit=room.day_time_limit,
        day_duration_seconds=room.day_duration_seconds,
        day_started_at=room.day_started_at.isoformat() if room.day_started_at else None,
        created_at=room.created_at.isoformat(),
        started_at=room.started_at.isoformat() if room.started_at else None,
        game_started_at=room.game_started_at.isoformat() if room.game_started_at else None,
        game_ended_at=room.game_ended_at.isoformat() if room.game_ended_at else None,
        finished_at=room.finished_at.isoformat() if room.finished_at else None,
        player_count=len(room.players),
        players=[_build_player_response(p) for p in room.players],
    )


def _build_player_response(player: Player) -> PlayerResponse:
    """Build PlayerResponse from Player model."""
    return PlayerResponse(
        id=str(player.id),
        player_name=player.player_name,
        player_email=player.player_email,
        current_day=player.current_day,
        is_finished=player.is_finished,
        cash=player.cash,
        portfolio_value=player.portfolio_value,
        total_return_pct=player.total_return_pct,
        total_return_usd=player.total_return_usd,
        score=player.score,
        grade=player.grade,
        is_ready=player.is_ready,
        last_sync_day=player.last_sync_day,
        joined_at=player.joined_at.isoformat(),
        last_action_at=player.last_action_at.isoformat(),
    )
    
def _next_trading_day(d: date) -> date:
    d += timedelta(days=1)
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d
