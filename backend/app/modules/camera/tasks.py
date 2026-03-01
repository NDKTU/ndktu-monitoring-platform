import logging
from datetime import datetime, date
from sqlalchemy import select, update
from app.core.db_helper import db_helper
from app.models.users.model import User
from app.models.user_events.model import UserEvents

logger = logging.getLogger(__name__)

async def close_open_events_at_midnight():
    """
    Finds all users marked as in_work=True.
    Sets in_work=False.
    Finds their open UserEvents (exit_time is NULL) from the previous day.
    Sets exit_time to None (already None, but ensures it stays open appropriately or closes it).
    Since the requirement is 'exit_time need be null and next day open new event',
    we just need to set in_work = False so the next morning it creates a new Enter event.
    """
    logger.info("Running scheduled midnight task: Closing open events and resetting user in_work status...")
    
    try:
        async for session in db_helper.session_getter():
            # Update all users to in_work = False
            await session.execute(
                update(User)
                .where(User.in_work == True)
                .values(in_work=False)
            )
            await session.commit()
            logger.info("Successfully reset 'in_work' status for all active users.")
            return # Only execute once
            
    except Exception as e:
        logger.error(f"Failed to run midnight reset task: {e}")
