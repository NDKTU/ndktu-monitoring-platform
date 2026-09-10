"""Domain logic for attendance segments, daily aggregation and status."""

from __future__ import annotations

import logging
from datetime import date, datetime, time as time_type, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance.model import Attendance
from app.models.daily_attendance.model import AttendanceStatus, DailyAttendance
from app.models.employees.model import Employee
from app.models.departments.model import Department
from app.models.work_schedules.model import WorkSchedule

logger = logging.getLogger(__name__)


def compute_status(
    schedule: WorkSchedule | None,
    daily: DailyAttendance,
) -> AttendanceStatus | None:
    """Decide the daily status given a schedule and the aggregated daily row."""

    if daily.has_no_enter and daily.first_enter_time is None:
        return AttendanceStatus.NO_ENTER
    if daily.has_no_exit:
        return AttendanceStatus.NO_EXIT

    if schedule is None:
        return None

    grace = timedelta(minutes=schedule.grace_minutes)
    expected_start = datetime.combine(daily.date, schedule.start_time) + grace
    expected_end = datetime.combine(daily.date, schedule.end_time) - grace

    is_late = (
        daily.first_enter_time is not None and daily.first_enter_time > expected_start
    )
    is_early = (
        daily.last_exit_time is not None and daily.last_exit_time < expected_end
    )

    if is_late and is_early:
        return AttendanceStatus.LATE_AND_EARLY
    if is_late:
        return AttendanceStatus.LATE_ARRIVAL
    if is_early:
        return AttendanceStatus.EARLY_LEAVE
    return AttendanceStatus.ON_TIME


async def _get_or_create_daily(
    session: AsyncSession, employee_id: int, day: date
) -> DailyAttendance:
    stmt = select(DailyAttendance).where(
        DailyAttendance.employee_id == employee_id,
        DailyAttendance.date == day,
    )
    result = await session.execute(stmt)
    daily = result.scalar_one_or_none()
    if daily is None:
        daily = DailyAttendance(employee_id=employee_id, date=day, total_working_hours=0.0)
        session.add(daily)
        await session.flush()
    return daily


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time_type.min)
    return start, start + timedelta(days=1)


async def _open_segment_today(
    session: AsyncSession, employee_id: int, day: date
) -> Attendance | None:
    """The person's still-open entry for that day, if any.

    Scoped to the day on purpose: an entry left open because its exit was never
    captured must not be closed by an exit days later — that produced segments
    of 56 hours and daily totals in the thousands.
    """
    start, end = _day_bounds(day)
    stmt = (
        select(Attendance)
        .where(
            Attendance.employee_id == employee_id,
            Attendance.exit_time.is_(None),
            Attendance.enter_time.is_not(None),
            Attendance.enter_time >= start,
            Attendance.enter_time < end,
        )
        .order_by(Attendance.enter_time.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def _get_schedule(session: AsyncSession, employee_id: int) -> WorkSchedule | None:
    stmt = (
        select(WorkSchedule)
        .join(Department, Department.work_schedule_id == WorkSchedule.id)
        .join(Employee, Employee.department_id == Department.id)
        .where(Employee.id == employee_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def apply_enter(
    session: AsyncSession,
    employee: Employee,
    camera_id: int,
    event_time: datetime,
    image_path: str | None,
) -> None:
    """Handle an enter event: create segment, upsert daily, recompute status."""

    day = event_time.date()
    daily = await _get_or_create_daily(session, employee.id, day)

    # The terminals re-identify whoever stands in front of them, firing the same
    # person a dozen times in a minute. One entry stays open per person per day;
    # the repeats would each open another segment that no exit ever closes.
    if await _open_segment_today(session, employee.id, day) is None:
        session.add(
            Attendance(
                employee_id=employee.id,
                camera_id=camera_id,
                enter_time=event_time,
                enter_image_path=image_path,
            )
        )

    if daily.first_enter_time is None:
        daily.first_enter_time = event_time
    daily.has_no_exit = False

    employee.in_work = True

    schedule = await _get_schedule(session, employee.id)
    daily.status = compute_status(schedule, daily)


async def apply_exit(
    session: AsyncSession,
    employee: Employee,
    camera_id: int,
    event_time: datetime,
    image_path: str | None,
) -> None:
    """Handle an exit event: close the latest open segment or create NO_ENTER segment."""

    day = event_time.date()
    daily = await _get_or_create_daily(session, employee.id, day)

    open_segment = await _open_segment_today(session, employee.id, day)

    # An exit stamped earlier than the entry it would close is not that person's
    # exit: events can reach us out of order, and pairing them yields negative
    # working_hours. Record it as an exit with no entry, which is already modelled.
    if (
        open_segment is not None
        and open_segment.enter_time is not None
        and event_time < open_segment.enter_time
    ):
        open_segment = None

    if open_segment is not None and open_segment.enter_time is not None:
        open_segment.exit_time = event_time
        open_segment.exit_image_path = image_path
        hours = (event_time - open_segment.enter_time).total_seconds() / 3600.0
        open_segment.working_hours = hours
        daily.total_working_hours = (daily.total_working_hours or 0.0) + hours
    else:
        no_enter_segment = Attendance(
            employee_id=employee.id,
            camera_id=camera_id,
            enter_time=None,
            exit_time=event_time,
            exit_image_path=image_path,
            working_hours=None,
        )
        session.add(no_enter_segment)
        daily.has_no_enter = True

    daily.last_exit_time = event_time
    daily.has_no_exit = False
    employee.in_work = False

    schedule = await _get_schedule(session, employee.id)
    daily.status = compute_status(schedule, daily)


async def mark_open_segments_no_exit(
    session: AsyncSession, today: date, lookback_days: int = 7
) -> int:
    """Flag days that ended with an entry still open as NO_EXIT.

    Only the last `lookback_days` are examined. The previous version re-read every
    open segment ever recorded — tens of thousands of rows, each with its own
    schedule query — which grows without bound and re-flags days already settled.
    Anything older than the window has been through this sweep already.

    Returns the number of daily rows updated.
    """
    window_start = datetime.combine(today - timedelta(days=lookback_days), time_type.min)
    day_start = datetime.combine(today, time_type.min)

    stmt = select(Attendance.employee_id, Attendance.enter_time).where(
        Attendance.exit_time.is_(None),
        Attendance.enter_time.is_not(None),
        Attendance.enter_time >= window_start,
        Attendance.enter_time < day_start,
    )
    rows = (await session.execute(stmt)).all()

    # One pass per (employee, day) rather than per segment: a day with a dozen
    # repeat entries used to be handled a dozen times.
    pending = {(employee_id, when.date()) for employee_id, when in rows}

    updated = 0
    for employee_id, seg_day in sorted(pending):
        daily = await _get_or_create_daily(session, employee_id, seg_day)
        if daily.has_no_exit:
            continue
        daily.has_no_exit = True
        schedule = await _get_schedule(session, employee_id)
        daily.status = compute_status(schedule, daily)
        updated += 1

    return updated
