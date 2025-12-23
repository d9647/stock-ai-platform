"""
Background scheduler for sync_auto mode auto-advancing.
Checks every 5 seconds for rooms that need to advance to the next day.
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from .db import SessionLocal
from .models.multiplayer import GameRoom, Player
from .routes.multiplayer import _next_trading_day


scheduler = AsyncIOScheduler()


async def check_and_advance_rooms():
    """
    Check all sync_auto rooms and advance them if their day_duration_seconds has elapsed.
    """
    db = SessionLocal()
    try:
        # Find all rooms that are:
        # 1. In progress
        # 2. Using sync_auto mode
        # 3. Have day_duration_seconds set
        # 4. Have day_started_at set
        rooms = db.query(GameRoom).filter(
            GameRoom.status == "in_progress",
            GameRoom.game_mode == "sync_auto",
            GameRoom.day_duration_seconds.isnot(None),
            GameRoom.day_started_at.isnot(None)
        ).all()

        now = datetime.utcnow()

        for room in rooms:
            # Calculate elapsed time since day started
            elapsed_seconds = (now - room.day_started_at).total_seconds()

            # Check if we should advance
            if elapsed_seconds >= room.day_duration_seconds:
                logger.info(f"Auto-advancing room {room.room_code} (elapsed: {elapsed_seconds:.1f}s, limit: {room.day_duration_seconds}s)")

                # Advance to next day
                try:
                    # Parse current date
                    current_date_obj = datetime.fromisoformat(room.current_date).date()
                    end_date_obj = datetime.fromisoformat(room.end_date).date()

                    # Find next trading day
                    next_date = _next_trading_day(current_date_obj)

                    # Check if we've reached the end
                    #if next_date > end_date_obj:
                    if room.current_day > room.config["numDays"]:
                        logger.info(f"Room {room.room_code} has reached the end date. Ending game.")
                        room.status = "finished"
                        room.game_ended_at = now
                        room.day_started_at = None
                    else:
                        # Advance to next day
                        room.current_date = next_date.isoformat()
                        room.current_day += 1
                        room.day_started_at = now  # Reset timer for next day

                        # Reset all players' ready status
                        for player in room.players:
                            player.is_ready = False

                        logger.info(f"Room {room.room_code} advanced to day {room.current_day} ({next_date})")

                    db.commit()

                except Exception as e:
                    logger.error(f"Error advancing room {room.room_code}: {e}")
                    db.rollback()

    except Exception as e:
        logger.error(f"Error in auto-advance scheduler: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    # Check every 5 seconds for rooms that need advancing
    scheduler.add_job(
        check_and_advance_rooms,
        'interval',
        seconds=5,
        id='auto_advance_rooms',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Auto-advance scheduler started (checking every 5 seconds)")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Auto-advance scheduler stopped")
