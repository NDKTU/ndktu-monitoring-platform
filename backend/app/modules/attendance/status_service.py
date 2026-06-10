"""Domain logic for attendance segments, daily aggregation and status."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

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

    segment = Attendance(
        employee_id=employee.id,
        camera_id=camera_id,
        enter_time=event_time,
        enter_image_path=image_path,
    )
    session.add(segment)

    day = event_time.date()
    daily = await _get_or_create_daily(session, employee.id, day)

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

    open_stmt = (
        select(Attendance)
        .where(
            Attendance.employee_id == employee.id,
            Attendance.exit_time.is_(None),
            Attendance.enter_time.is_not(None),
        )
        .order_by(Attendance.enter_time.desc())
        .limit(1)
    )
    open_result = await session.execute(open_stmt)
    open_segment = open_result.scalar_one_or_none()

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


async def mark_open_segments_no_exit(session: AsyncSession, today: date) -> int:
    """Find Attendance rows with no exit from past days; flag their daily row as NO_EXIT.

    Returns the number of daily rows updated.
    """
    stmt = (
        select(Attendance)
        .where(
            Attendance.exit_time.is_(None),
            Attendance.enter_time.is_not(None),
        )
    )
    result = await session.execute(stmt)
    open_segments = result.scalars().all()

    updated_daily_ids: set[int] = set()
    for seg in open_segments:
        assert seg.enter_time is not None
        seg_day = seg.enter_time.date()
        if seg_day >= today:
            continue

        daily = await _get_or_create_daily(session, seg.employee_id, seg_day)
        if daily.id in updated_daily_ids:
            continue
        daily.has_no_exit = True
        schedule = await _get_schedule(session, seg.employee_id)
        daily.status = compute_status(schedule, daily)
        updated_daily_ids.add(daily.id)

    return len(updated_daily_ids)
