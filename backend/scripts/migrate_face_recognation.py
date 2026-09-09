"""One-off ETL: legacy `face_recognation` database -> `camera_base`.

The legacy database belongs to the older NSUMT face-recognition system. It is not a
schema ancestor of this platform, so nothing here is an Alembic migration: it is a data
transfer that maps the legacy shape onto the current models.

Usage (from backend/ dir):

    # 1. Bring the legacy snapshot up on a throwaway port (it is PostgreSQL 16):
    #      cp -a volumes/face_recognation_postgres_data/_data /tmp/frdb
    #      sed -i 's/scram-sha-256\\|md5\\|peer/trust/' /tmp/frdb/pg_hba.conf
    #      docker run -d --name frdb -v /tmp/frdb:/var/lib/postgresql/data \\
    #             -p 127.0.0.1:5457:5432 postgres:16-alpine
    #
    # 2. Dry run - runs every phase for real inside a transaction, then rolls back:
    uv run python scripts/migrate_face_recognation.py --source postgresql://db@127.0.0.1:5457/db
    #
    # 3. Apply:
    uv run python scripts/migrate_face_recognation.py --source postgresql://db@127.0.0.1:5457/db --apply

Re-runnable: every phase skips rows that already exist (by unique key), so a second
run is a no-op.

Decisions baked in (migration plan, 2026-09-09):
  * employees.jshir  <- legacy users.username, but only rows matching ^[0-9]{14}$
    (672 of 704 - the legacy system stored the JSHIR in the username field).
  * The 32 users without a valid JSHIR are skipped: 20 are test rows (21222222222222,
    12121212112121, ...), 3 are service accounts, the rest are malformed numbers.
    Their 3939 logs go with them.
  * attendance.camera_id is NOT NULL and the legacy logs record no camera, so every
    imported segment points at one inactive placeholder camera (0.0.0.0).
  * Imported departments are attached to a work schedule (--schedule-id, default: the
    09:00-18:00 one). Without a schedule compute_status() returns None and every
    imported day would show a blank status.
  * employees.image_path keeps the legacy absolute URLs (https://face.nsumt.uz/...).
    Pass --images=null to drop them instead.
  * Legacy roles and passwords are NOT imported. Those rows are recognised people, not
    platform accounts: 701 of 704 have a NULL password.

Daily statuses are computed by importing the platform's own compute_status(), so an
imported day behaves exactly like one the running app would have produced.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running as `python scripts/migrate_face_recognation.py` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncpg
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models.attendance.model import Attendance
from app.models.cameras.model import Cameras, DirectionType
from app.models.daily_attendance.model import DailyAttendance
from app.models.departments.model import Department
from app.models.employees.model import Employee
from app.models.work_schedules.model import WorkSchedule
from app.modules.attendance.status_service import compute_status

# Six real cameras read out of volumes/ndktu-monitoring-platform_postgres_data on
# 2026-09-09. That snapshot holds nothing else worth moving.
SNAPSHOT_CAMERAS = [
    ("192.168.88.101", "admin", "nokia113", DirectionType.ENTER, True),
    ("192.168.88.102", "admin", "nokia113", DirectionType.EXIT, True),
    ("192.168.88.103", "admin", "nokia113", DirectionType.ENTER, True),
    ("192.168.88.104", "admin", "nokia113", DirectionType.EXIT, True),
    ("192.168.88.105", "admin", "nokia113", DirectionType.ENTER, False),
    ("192.168.88.106", "admin", "nokia113", DirectionType.EXIT, False),
]

# Placeholder every imported attendance segment points at.
IMPORT_CAMERA_IP = "0.0.0.0"

# Legacy rows carry epoch-0 timestamps; anything older than this is junk.
MIN_VALID_TS = datetime(1990, 1, 1)

JSHIR_LEN = 14
MAX_NAME = 50
MAX_PASSPORT = 20
MAX_DEPARTMENT = 120


class _Rollback(Exception):
    """Raised to unwind the transaction after a dry run."""


COUNTED = {
    "cameras": Cameras,
    "departments": Department,
    "employees": Employee,
    "attendance": Attendance,
    "daily_attendance": DailyAttendance,
}


async def _counts(conn) -> dict[str, int]:
    """Row counts per target table. executemany + ON CONFLICT reports rowcount -1,
    so deltas measured this way are the only trustworthy numbers."""
    out = {}
    for name, model in COUNTED.items():
        out[name] = await conn.scalar(select(func.count()).select_from(model))
    return out


def _clip(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return value[:limit]


def _to_naive(value: datetime | None, offset_hours: int) -> datetime | None:
    """Legacy columns are timestamptz; the platform stores naive local time."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone(timedelta(hours=offset_hours))).replace(tzinfo=None)


async def fetch_source(dsn: str, images: str, tz_offset: int, max_segment_hours: float):
    """Pull and clean the legacy rows. Returns (people, logs, skipped)."""
    conn = await asyncpg.connect(dsn)
    try:
        raw_people = await conn.fetch(
            """
            SELECT u.id            AS legacy_id,
                   trim(u.username) AS jshir,
                   i.first_name, i.last_name, i.third_name,
                   i.passport_serial, i.department, u.image_path
              FROM users u
              LEFT JOIN user_infos i ON i.user_id = u.id
             ORDER BY length(u.id), u.id
            """
        )
        raw_logs = await conn.fetch(
            """
            SELECT user_id, enter_time, exit_time
              FROM user_logs
             ORDER BY user_id, enter_time
            """
        )
    finally:
        await conn.close()

    skipped = {
        "no_jshir": 0,
        "dup_jshir": 0,
        "dup_passport": 0,
        "junk_ts": 0,
        "orphan_log": 0,
        "unclosed_long": 0,
    }

    people: dict[str, dict] = {}  # legacy_id -> payload
    seen_jshir: set[str] = set()
    seen_passport: set[str] = set()

    for row in raw_people:
        jshir = (row["jshir"] or "").strip()
        if len(jshir) != JSHIR_LEN or not jshir.isdigit():
            skipped["no_jshir"] += 1
            continue
        if jshir in seen_jshir:
            skipped["dup_jshir"] += 1
            continue
        seen_jshir.add(jshir)

        passport = _clip(row["passport_serial"], MAX_PASSPORT)
        if passport and passport in seen_passport:
            # Two different people sharing a passport number is a legacy data-entry
            # error; passport_series is UNIQUE here, so the later one loses it.
            skipped["dup_passport"] += 1
            passport = None
        elif passport:
            seen_passport.add(passport)

        people[row["legacy_id"]] = {
            "jshir": jshir,
            "first_name": _clip(row["first_name"], MAX_NAME),
            "last_name": _clip(row["last_name"], MAX_NAME),
            "third_name": _clip(row["third_name"], MAX_NAME),
            "passport_series": passport,
            "department": _clip(row["department"], MAX_DEPARTMENT),
            "image_path": row["image_path"] if images == "keep" else None,
        }

    logs: list[tuple[str, datetime, datetime | None]] = []
    for row in raw_logs:
        enter = _to_naive(row["enter_time"], tz_offset)
        if enter is None or enter < MIN_VALID_TS:
            skipped["junk_ts"] += 1
            continue
        if row["user_id"] not in people:
            skipped["orphan_log"] += 1
            continue
        exit_ = _to_naive(row["exit_time"], tz_offset)
        if exit_ is not None and exit_ < enter:
            exit_ = None
        elif exit_ is not None and (exit_ - enter) > timedelta(hours=max_segment_hours):
            # The legacy system routinely paired an enter with an exit days later
            # (34% of its closed rows). Keeping those would poison working_hours, so
            # treat them as what they actually are: a segment that was never closed.
            exit_ = None
            skipped["unclosed_long"] += 1
        logs.append((row["user_id"], enter, exit_))

    return people, logs, skipped


async def run(args) -> None:
    people, logs, skipped = await fetch_source(
        args.source, args.images, args.tz_offset, args.max_segment_hours
    )
    print(f"source: {len(people)} people, {len(logs)} usable logs")
    print(
        "  skipped: "
        + ", ".join(f"{k}={v}" for k, v in skipped.items() if v)
    )

    engine = create_async_engine(args.target, echo=False)
    candidates: dict[str, int] = {}
    before: dict[str, int] = {}
    after: dict[str, int] = {}
    notes: list[str] = []

    try:
        async with engine.begin() as conn:
            before = await _counts(conn)
            # ---- phase 1: cameras -------------------------------------------------
            rows = [
                {
                    "device_ip": ip,
                    "login": login,
                    "password": pwd,
                    "direction": direction,
                    "is_active": active,
                }
                for ip, login, pwd, direction, active in SNAPSHOT_CAMERAS
            ]
            rows.append(
                {
                    "device_ip": IMPORT_CAMERA_IP,
                    "login": "import",
                    "password": "import",
                    "direction": DirectionType.ENTER,
                    "is_active": False,
                }
            )
            await conn.execute(
                pg_insert(Cameras).on_conflict_do_nothing(index_elements=["device_ip"]),
                rows,
            )
            candidates["cameras"] = len(rows)

            import_camera_id = await conn.scalar(
                select(Cameras.id).where(Cameras.device_ip == IMPORT_CAMERA_IP)
            )

            # ---- phase 2: departments --------------------------------------------
            schedule_id = args.schedule_id
            if schedule_id is None:
                schedule_id = await conn.scalar(
                    select(WorkSchedule.id).order_by(WorkSchedule.id).limit(1)
                )
            names = sorted({p["department"] for p in people.values() if p["department"]})
            candidates["departments"] = len(names)
            if names:
                await conn.execute(
                    pg_insert(Department).on_conflict_do_nothing(index_elements=["name"]),
                    [{"name": n, "work_schedule_id": schedule_id} for n in names],
                )
            dept_ids = {
                name: did
                for name, did in (await conn.execute(select(Department.name, Department.id))).all()
            }

            # ---- phase 3: employees ----------------------------------------------
            existing_jshir = set(
                (await conn.execute(select(Employee.jshir))).scalars().all()
            )
            existing_passports = set(
                (await conn.execute(select(Employee.passport_series))).scalars().all()
            ) - {None}

            new_people = {
                lid: p for lid, p in people.items() if p["jshir"] not in existing_jshir
            }
            emp_rows = []
            for payload in new_people.values():
                passport = payload["passport_series"]
                if passport and passport in existing_passports:
                    passport = None
                emp_rows.append(
                    {
                        "jshir": payload["jshir"],
                        "first_name": payload["first_name"],
                        "last_name": payload["last_name"],
                        "third_name": payload["third_name"],
                        "passport_series": passport,
                        "image_path": payload["image_path"],
                        "department_id": dept_ids.get(payload["department"]),
                        "in_work": False,
                        "work_rate": 1.0,
                    }
                )
            if emp_rows:
                await conn.execute(
                    pg_insert(Employee).on_conflict_do_nothing(index_elements=["jshir"]),
                    emp_rows,
                )
            candidates["employees"] = len(people)

            emp_by_jshir = {
                j: eid
                for j, eid in (await conn.execute(select(Employee.jshir, Employee.id))).all()
            }
            legacy_to_emp = {
                lid: emp_by_jshir[p["jshir"]]
                for lid, p in people.items()
                if p["jshir"] in emp_by_jshir
            }

            # ---- phase 4: attendance segments ------------------------------------
            already = await conn.scalar(
                select(Attendance.id)
                .where(Attendance.camera_id == import_camera_id)
                .limit(1)
            )
            if already is not None:
                notes.append("attendance: already imported, phase skipped")
            else:
                batch: list[dict] = []
                total = 0
                for legacy_id, enter, exit_ in logs:
                    emp_id = legacy_to_emp.get(legacy_id)
                    if emp_id is None:
                        continue
                    hours = (
                        (exit_ - enter).total_seconds() / 3600.0
                        if exit_ is not None
                        else None
                    )
                    batch.append(
                        {
                            "employee_id": emp_id,
                            "camera_id": import_camera_id,
                            "enter_time": enter,
                            "exit_time": exit_,
                            "working_hours": hours,
                        }
                    )
                    if len(batch) >= args.batch_size:
                        await conn.execute(pg_insert(Attendance), batch)
                        total += len(batch)
                        batch = []
                if batch:
                    await conn.execute(pg_insert(Attendance), batch)
                    total += len(batch)
                candidates["attendance"] = total

            # ---- phase 5: daily aggregation --------------------------------------
            # A Core connection yields plain rows, so rebuild the ORM object that
            # compute_status() expects.
            schedule = None
            if schedule_id is not None:
                row = (
                    await conn.execute(
                        select(
                            WorkSchedule.start_time,
                            WorkSchedule.end_time,
                            WorkSchedule.grace_minutes,
                        ).where(WorkSchedule.id == schedule_id)
                    )
                ).first()
                if row is not None:
                    schedule = WorkSchedule(
                        start_time=row.start_time,
                        end_time=row.end_time,
                        grace_minutes=row.grace_minutes,
                    )

            agg: dict[tuple[int, object], dict] = defaultdict(
                lambda: {
                    "first_enter": None,
                    "last_exit": None,
                    "hours": 0.0,
                    "open": False,
                }
            )
            for legacy_id, enter, exit_ in logs:
                emp_id = legacy_to_emp.get(legacy_id)
                if emp_id is None:
                    continue
                cell = agg[(emp_id, enter.date())]
                if cell["first_enter"] is None or enter < cell["first_enter"]:
                    cell["first_enter"] = enter
                if exit_ is None:
                    cell["open"] = True
                else:
                    if cell["last_exit"] is None or exit_ > cell["last_exit"]:
                        cell["last_exit"] = exit_
                    cell["hours"] += (exit_ - enter).total_seconds() / 3600.0

            daily_rows = []
            for (emp_id, day), cell in agg.items():
                probe = DailyAttendance(
                    employee_id=emp_id,
                    date=day,
                    total_working_hours=cell["hours"],
                    first_enter_time=cell["first_enter"],
                    last_exit_time=cell["last_exit"],
                    has_no_enter=False,
                    has_no_exit=cell["open"],
                )
                status = compute_status(schedule, probe)
                daily_rows.append(
                    {
                        "employee_id": emp_id,
                        "date": day,
                        "status": status,
                        "total_working_hours": cell["hours"],
                        "first_enter_time": cell["first_enter"],
                        "last_exit_time": cell["last_exit"],
                        "has_no_enter": False,
                        "has_no_exit": cell["open"],
                    }
                )

            for start in range(0, len(daily_rows), args.batch_size):
                chunk = daily_rows[start : start + args.batch_size]
                await conn.execute(
                    pg_insert(DailyAttendance).on_conflict_do_nothing(
                        index_elements=["employee_id", "date"]
                    ),
                    chunk,
                )
            candidates["daily_attendance"] = len(daily_rows)
            after = await _counts(conn)

            if not args.apply:
                raise _Rollback
    except _Rollback:
        pass
    finally:
        await engine.dispose()

    print()
    print(f"  {'table':<18} {'before':>8} {'after':>8} {'added':>8}   candidates")
    for name in COUNTED:
        b, a = before.get(name, 0), after.get(name, 0)
        print(f"  {name:<18} {b:>8} {a:>8} {a - b:>+8}   {candidates.get(name, '-')}")
    for note in notes:
        print(f"  {note}")
    print()
    print("APPLIED" if args.apply else "DRY RUN - rolled back, nothing written")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, help="DSN of the legacy face_recognation DB")
    p.add_argument("--target", default=None, help="DSN of camera_base (default: backend .env)")
    p.add_argument("--apply", action="store_true", help="commit; without it the run rolls back")
    p.add_argument("--images", choices=["keep", "null"], default="keep")
    p.add_argument("--tz-offset", type=int, default=5, help="legacy timestamptz -> local hours (default 5)")
    p.add_argument("--schedule-id", type=int, default=None, help="work schedule for imported departments")
    p.add_argument(
        "--max-segment-hours",
        type=float,
        default=24.0,
        help="exits later than this after the enter are dropped as never-closed (default 24)",
    )
    p.add_argument("--batch-size", type=int, default=5000)
    args = p.parse_args()
    if args.target is None:
        args.target = settings.database.url
    elif args.target.startswith("postgresql://"):
        args.target = args.target.replace("postgresql://", "postgresql+asyncpg://", 1)
    return args


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
