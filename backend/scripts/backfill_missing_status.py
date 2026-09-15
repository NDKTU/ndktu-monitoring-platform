"""Give a status to the days that came out without one.

A day's status is decided against a work schedule, and a schedule could only be
reached through a department. Anyone with no department therefore had no
schedule, so every one of their days was stored with status NULL — blank in the
employee card, blank in the reports, and indistinguishable from a day the system
had not got round to judging.

An employee can now hold a schedule of their own. This script hands the default
schedule to whoever still has none, then recomputes the status of every day left
blank, using the same domain logic the live stream uses.

Usage (from backend/ dir, or inside the ndktu_backend container):

    # Dry run — recomputes in a transaction, then rolls back:
    uv run python scripts/backfill_missing_status.py
    # Apply:
    uv run python scripts/backfill_missing_status.py --apply

Re-runnable: it only touches employees with no schedule and days with no status,
so a second run over the same data changes nothing.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.daily_attendance.model import DailyAttendance
from app.models.departments.model import Department
from app.models.employees.model import Employee
from app.models.work_schedules.model import WorkSchedule
from app.modules.attendance.status_service import compute_status


async def _schedule_for(session: AsyncSession, employee_id: int) -> WorkSchedule | None:
    """The same precedence the live stream applies: own first, department second."""
    own = await session.scalar(
        select(WorkSchedule)
        .join(Employee, Employee.work_schedule_id == WorkSchedule.id)
        .where(Employee.id == employee_id)
    )
    if own is not None:
        return own
    return await session.scalar(
        select(WorkSchedule)
        .join(Department, Department.work_schedule_id == WorkSchedule.id)
        .join(Employee, Employee.department_id == Department.id)
        .where(Employee.id == employee_id)
    )


async def run(args) -> None:
    engine = create_async_engine(args.target, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        blank_before = await session.scalar(
            select(func.count()).select_from(DailyAttendance).where(
                DailyAttendance.status.is_(None)
            )
        )

        default_schedule_id = args.schedule_id
        if default_schedule_id is None:
            ids = (await session.execute(select(WorkSchedule.id).order_by(WorkSchedule.id))).scalars().all()
            if len(ids) != 1:
                print(
                    f"  {len(ids)} work schedules exist — name one with "
                    f"--schedule-id, there is no obvious default."
                )
                return
            default_schedule_id = ids[0]
        print(f"  default schedule : {default_schedule_id}")

        # Whoever can reach no schedule at all gets the default one of their own.
        orphans = (
            await session.execute(
                select(Employee.id).where(
                    Employee.work_schedule_id.is_(None),
                    Employee.department_id.is_(None),
                )
            )
        ).scalars().all()
        if orphans:
            await session.execute(
                update(Employee)
                .where(Employee.id.in_(orphans))
                .values(work_schedule_id=default_schedule_id)
            )
        print(f"  employees given a schedule : {len(orphans)}")

        rows = (
            await session.execute(
                select(DailyAttendance).where(DailyAttendance.status.is_(None))
            )
        ).scalars().all()

        cache: dict[int, WorkSchedule | None] = {}
        filled = 0
        still_blank = 0
        for daily in rows:
            if daily.employee_id not in cache:
                cache[daily.employee_id] = await _schedule_for(session, daily.employee_id)
            status = compute_status(cache[daily.employee_id], daily)
            if status is None:
                still_blank += 1
                continue
            daily.status = status
            filled += 1

        await session.flush()
        blank_after = await session.scalar(
            select(func.count()).select_from(DailyAttendance).where(
                DailyAttendance.status.is_(None)
            )
        )

        print(f"\n  days without status, before : {blank_before}")
        print(f"  filled in                   : {filled}")
        print(f"  still without status        : {still_blank}")
        print(f"  days without status, after  : {blank_after}")

        if args.apply:
            await session.commit()
            print("\nAPPLIED")
        else:
            await session.rollback()
            print("\nDRY RUN - rolled back, nothing written")

    await engine.dispose()


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--schedule-id",
        type=int,
        default=None,
        help="schedule to hand out; required when more than one exists",
    )
    p.add_argument("--target", default=None, help="DSN of camera_base (default: .env)")
    p.add_argument("--apply", action="store_true", help="commit; without it, rolls back")
    args = p.parse_args()
    if args.target is None:
        args.target = settings.database.url
    elif args.target.startswith("postgresql://"):
        args.target = args.target.replace("postgresql://", "postgresql+asyncpg://", 1)
    return args


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
