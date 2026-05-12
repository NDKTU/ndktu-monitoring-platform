import logging
from datetime import date

from sqlalchemy import update

from app.core.db_helper import db_helper
from app.models.employees.model import Employee
from app.modules.attendance.status_service import mark_open_segments_no_exit

logger = logging.getLogger(__name__)


async def close_open_events_at_midnight():
    """At midnight: flag yesterday's unclosed attendance as NO_EXIT and reset in_work."""

    logger.info("Running scheduled midnight task: NO_EXIT flagging and in_work reset...")

    try:
        async for session in db_helper.session_getter():
            updated = await mark_open_segments_no_exit(session, today=date.today())
            await session.execute(
                update(Employee)
                .where(Employee.in_work == True)
                .values(in_work=False)
            )
            await session.commit()
            logger.info(
                f"Midnight task done: flagged {updated} daily rows as NO_EXIT, "
                f"reset in_work for all employees."
            )
            return

    except Exception as e:
        logger.error(f"Failed to run midnight reset task: {e}")
