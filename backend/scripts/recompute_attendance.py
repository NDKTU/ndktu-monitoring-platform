"""Rebuild attendance and daily_attendance from the events already recorded.

History was accumulated under rules the platform no longer follows: an entry was
opened for every repeat the terminals fired, and an exit could close an entry from
days earlier. That left 1 569 days over 24 hours (the worst at 137 903), 2 097
segments longer than a day, and days labelled NO_EXIT beside a perfectly good exit.

Nothing needs re-reading from the cameras — every timestamp is already here. This
takes each segment apart into the enter and exit events it was built from, then
replays them in order through apply_enter/apply_exit, the same functions the live
stream uses. What comes out is what the platform would have recorded had the current
rules been in place all along.

Usage (from backend/ dir, or inside the ndktu_backend container):

    # Dry run — rebuilds in a transaction, reports, then rolls back:
    uv run python scripts/recompute_attendance.py
    # Apply:
    uv run python scripts/recompute_attendance.py --apply
    # A single period:
    uv run python scripts/recompute_attendance.py --from 2026-06-01 --apply

Take a database dump first. Rows in range are rebuilt, not patched: ids change.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, time as time_type, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.attendance.model import Attendance
from app.models.daily_attendance.model import DailyAttendance
from app.models.employees.model import Employee
from app.modules.attendance.status_service import apply_enter, apply_exit

BATCH_LOG = 20000


async def _stats(session: AsyncSession) -> dict[str, int | float]:
    async def scalar(stmt):
        return await session.scalar(stmt) or 0

    return {
        "segments": await scalar(select(func.count()).select_from(Attendance)),
        "days": await scalar(select(func.count()).select_from(DailyAttendance)),
        "days>24h": await scalar(
            select(func.count()).select_from(DailyAttendance).where(
                DailyAttendance.total_working_hours > 24
            )
        ),
        "days>12h": await scalar(
            select(func.count()).select_from(DailyAttendance).where(
                DailyAttendance.total_working_hours > 12
            )
        ),
        "segments>24h": await scalar(
            select(func.count()).select_from(Attendance).where(
                Attendance.working_hours > 24
            )
        ),
        "max_day_hours": round(
            float(
                await scalar(select(func.max(DailyAttendance.total_working_hours)))
            ),
            1,
        ),
        "no_exit_with_hours": await scalar(
            select(func.count()).select_from(DailyAttendance).where(
                DailyAttendance.status == "NO_EXIT",
                DailyAttendance.total_working_hours > 0,
            )
        ),
    }


def _report(label: str, before: dict, after: dict) -> None:
    print(f"\n  {label:<22} {'before':>12} {'after':>12}")
    for key in before:
        print(f"  {key:<22} {before[key]:>12} {after[key]:>12}")


async def run(args) -> None:
    engine = create_async_engine(args.target, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    lo = datetime.combine(date.fromisoformat(args.date_from), time_type.min)
    hi = datetime.combine(
        date.fromisoformat(args.date_to) + timedelta(days=1), time_type.min
    )

    async with factory() as session:
        before = await _stats(session)

        rows = (
            await session.execute(
                select(
                    Attendance.employee_id,
                    Attendance.camera_id,
                    Attendance.enter_time,
                    Attendance.exit_time,
                    Attendance.enter_image_path,
                    Attendance.exit_image_path,
                ).where(
                    func.greatest(
                        func.coalesce(Attendance.enter_time, Attendance.exit_time),
                        func.coalesce(Attendance.exit_time, Attendance.enter_time),
                    )
                    >= lo,
                    func.least(
                        func.coalesce(Attendance.enter_time, Attendance.exit_time),
                        func.coalesce(Attendance.exit_time, Attendance.enter_time),
                    )
                    < hi,
                )
            )
        ).all()

        # A segment is two events that were joined together; the join is what went
        # wrong, so take them apart and let the current rules re-pair them.
        events: list[tuple[datetime, int, int, str, str | None]] = []
        for employee_id, camera_id, enter_time, exit_time, enter_img, exit_img in rows:
            if enter_time is not None:
                events.append((enter_time, employee_id, camera_id, "enter", enter_img))
            if exit_time is not None:
                events.append((exit_time, employee_id, camera_id, "exit", exit_img))
        events.sort(key=lambda e: e[0])
        print(f"  segments read : {len(rows)}")
        print(f"  events to replay: {len(events)}")
        if not events:
            print("\nnothing in range")
            return

        await session.execute(
            delete(DailyAttendance).where(
                DailyAttendance.date >= lo.date(), DailyAttendance.date < hi.date()
            )
        )
        await session.execute(
            delete(Attendance).where(
                func.coalesce(Attendance.enter_time, Attendance.exit_time) >= lo,
                func.coalesce(Attendance.enter_time, Attendance.exit_time) < hi,
            )
        )
        await session.flush()

        cache: dict[int, Employee] = {}
        done = 0
        for when, employee_id, camera_id, kind, image in events:
            employee = cache.get(employee_id)
            if employee is None:
                employee = await session.get(Employee, employee_id)
                if employee is None:
                    continue
                cache[employee_id] = employee
            if kind == "enter":
                await apply_enter(session, employee, camera_id, when, image)
            else:
                await apply_exit(session, employee, camera_id, when, image)
            done += 1
            if done % BATCH_LOG == 0:
                await session.flush()
                print(f"    …{done} replayed")

        await session.flush()
        after = await _stats(session)
        _report("metric", before, after)

        if args.apply:
            await session.commit()
        else:
            await session.rollback()

    await engine.dispose()
    print()
    print("APPLIED" if args.apply else "DRY RUN - rolled back, nothing written")


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--from", dest="date_from", default="2000-01-01", help="YYYY-MM-DD")
    p.add_argument(
        "--to", dest="date_to", default=date.today().isoformat(), help="YYYY-MM-DD"
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
