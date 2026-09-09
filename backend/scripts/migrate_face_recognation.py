"""One-off ETL: legacy `face_recognation` database -> `camera_base`.

The legacy database belongs to the older NSUMT face-recognition system. It is not a
schema ancestor of this platform, so nothing here is an Alembic migration: it is a data
transfer that maps the legacy shape onto the current models.

Usage (from backend/ dir, or inside the ndktu_backend container):

    # 1. Bring the legacy snapshot up (it is PostgreSQL 16) on a reachable host/port.
    # 2. Dry run - runs every phase for real inside a transaction, then rolls back:
    uv run python scripts/migrate_face_recognation.py --source postgresql://db@127.0.0.1:5457/db
    # 3. Apply:
    uv run python scripts/migrate_face_recognation.py --source ... --apply

Re-runnable: every phase skips rows that already exist (by unique key), so a second
run is a no-op.

The goal is to carry over everything the target schema can hold. Where the legacy data
cannot be represented as-is it is defaulted, not dropped:

  * employees.jshir <- legacy users.username, which is where that system kept the JSHIR.
    672 of 704 rows are a clean 14-digit number. Of the rest, anything that still fits
    the 14-char column is kept verbatim (typos included - 12 digits, a trailing dot, a
    trailing letter), and only values that cannot fit at all get a synthetic
    `LGC<legacy id>`, so the person and their logs still come across. Synthetic ids are
    listed at the end of the run so they can be corrected by hand.
  * Two legacy rows sharing a JSHIR are the same person entered twice: both map onto one
    employee, so neither one's attendance is lost.
  * passport_series is UNIQUE here. Where two different people share a passport number in
    the legacy data, the later one keeps everything except the passport.
  * Logs whose enter_time is epoch-0 junk but whose exit_time is real are imported as
    NO_ENTER segments - the shape the platform already uses for an exit with no entry.
    Rows where both timestamps are junk carry no position in time and are skipped.
  * Exits more than --max-segment-hours after their entry (34% of the legacy closed rows,
    some of them days apart) are treated as never closed, which is what they are.
  * attendance.camera_id is NOT NULL and the legacy logs record no camera, so every
    imported segment points at one inactive placeholder camera (0.0.0.0).
  * Imported departments are attached to a work schedule (--schedule-id, default: the
    first one). Without a schedule compute_status() returns None and every imported day
    would show a blank status.
  * Photos: --photos-dest names a directory (relative to the working directory) that
    already holds the legacy image files. Any employee whose legacy image_path names a
    file present there gets image_path rewritten to the local path the frontend expects.
    The absolute https://face.nsumt.uz/... URLs cannot be kept: buildImageUrl() prefixes
    VITE_API_URL, so an absolute URL renders broken.
  * Legacy login accounts (the few with a password hash) are imported into users as
    inactive and role-less: the record is preserved without granting anyone access.

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
from app.models.users.model import User
from app.models.work_schedules.model import WorkSchedule
from app.modules.attendance.status_service import compute_status

# Six real cameras read out of volumes/ndktu-monitoring-platform_postgres_data on
# 2026-09-09. Skipped by device_ip wherever they already exist.
SNAPSHOT_CAMERAS = [
    ("192.168.88.101", "admin", "nokia113", DirectionType.ENTER, True),
    ("192.168.88.102", "admin", "nokia113", DirectionType.EXIT, True),
    ("192.168.88.103", "admin", "nokia113", DirectionType.ENTER, True),
    ("192.168.88.104", "admin", "nokia113", DirectionType.EXIT, True),
    ("192.168.88.105", "admin", "nokia113", DirectionType.ENTER, False),
    ("192.168.88.106", "admin", "nokia113", DirectionType.EXIT, False),
]

IMPORT_CAMERA_IP = "0.0.0.0"
MIN_VALID_TS = datetime(1990, 1, 1)

JSHIR_LEN = 14
MAX_NAME = 50
MAX_PASSPORT = 20
MAX_DEPARTMENT = 120
MAX_USERNAME = 50


class _Rollback(Exception):
    """Raised to unwind the transaction after a dry run."""


COUNTED = {
    "cameras": Cameras,
    "departments": Department,
    "employees": Employee,
    "attendance": Attendance,
    "daily_attendance": DailyAttendance,
    "users": User,
}


async def _counts(conn) -> dict[str, int]:
    """Row counts per target table. executemany + ON CONFLICT reports rowcount -1,
    so deltas measured this way are the only trustworthy numbers."""
    return {
        name: await conn.scalar(select(func.count()).select_from(model))
        for name, model in COUNTED.items()
    }


def _clip(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value[:limit] if value else None


def _to_naive(value: datetime | None, offset_hours: int) -> datetime | None:
    """Legacy columns are timestamptz; the platform stores naive local time."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone(timedelta(hours=offset_hours))).replace(tzinfo=None)


def _assign_jshir(raw: str | None, legacy_id: str, used: set[str]) -> tuple[str, bool]:
    """Return (jshir, is_synthetic). A clean 14-digit value is returned as-is, and a
    repeat is intentional: two rows carrying the same JSHIR are one person."""
    text = (raw or "").strip()
    if len(text) == JSHIR_LEN and text.isdigit():
        return text, False
    if 1 <= len(text) <= JSHIR_LEN and text not in used:
        return text, False
    return f"LGC{legacy_id.strip()[-11:].rjust(11, '0')}"[:JSHIR_LEN], True


async def fetch_source(dsn: str, tz_offset: int, max_segment_hours: float):
    """Pull and clean the legacy rows."""
    conn = await asyncpg.connect(dsn)
    try:
        raw_people = await conn.fetch(
            """
            SELECT u.id AS legacy_id, u.username, u.password, u.image_path,
                   i.first_name, i.last_name, i.third_name,
                   i.passport_serial, i.department
              FROM users u
              LEFT JOIN user_infos i ON i.user_id = u.id
             ORDER BY length(u.id), u.id
            """
        )
        raw_logs = await conn.fetch(
            "SELECT user_id, enter_time, exit_time FROM user_logs ORDER BY user_id, enter_time"
        )
    finally:
        await conn.close()

    stats = {
        "synthetic_jshir": 0,
        "merged_duplicates": 0,
        "dup_passport": 0,
        "no_enter_segment": 0,
        "unclosed_long": 0,
        "unusable_ts": 0,
        "orphan_log": 0,
    }
    synthetic_ids: list[str] = []

    people: dict[str, dict] = {}
    used_jshir: set[str] = set()
    seen_passport: set[str] = set()
    accounts: list[dict] = []

    for row in raw_people:
        legacy_id = row["legacy_id"]
        jshir, synthetic = _assign_jshir(row["username"], legacy_id, used_jshir)
        if synthetic:
            stats["synthetic_jshir"] += 1
            synthetic_ids.append(f"{jshir} <- {(row['username'] or '').strip()!r}")
        if jshir in used_jshir:
            stats["merged_duplicates"] += 1
        used_jshir.add(jshir)

        passport = _clip(row["passport_serial"], MAX_PASSPORT)
        if passport and passport in seen_passport:
            # Two different people sharing a passport number is a legacy data-entry
            # error; passport_series is UNIQUE here, so the later one loses it.
            stats["dup_passport"] += 1
            passport = None
        elif passport:
            seen_passport.add(passport)

        people[legacy_id] = {
            "jshir": jshir,
            "first_name": _clip(row["first_name"], MAX_NAME),
            "last_name": _clip(row["last_name"], MAX_NAME),
            "third_name": _clip(row["third_name"], MAX_NAME),
            "passport_series": passport,
            "department": _clip(row["department"], MAX_DEPARTMENT),
            "photo": Path(row["image_path"]).name if row["image_path"] else None,
        }

        if row["password"]:
            accounts.append({
                "username": _clip(row["username"], MAX_USERNAME) or f"legacy_{legacy_id}",
                "password": row["password"],
                "is_active": False,
                "role_id": None,
            })

    logs: list[tuple[str, datetime | None, datetime | None]] = []
    for row in raw_logs:
        if row["user_id"] not in people:
            stats["orphan_log"] += 1
            continue
        enter = _to_naive(row["enter_time"], tz_offset)
        exit_ = _to_naive(row["exit_time"], tz_offset)
        if enter is not None and enter < MIN_VALID_TS:
            enter = None
        if exit_ is not None and exit_ < MIN_VALID_TS:
            exit_ = None

        if enter is None and exit_ is None:
            stats["unusable_ts"] += 1
            continue
        if enter is None:
            # Junk entry, real exit: the platform already models this as NO_ENTER.
            stats["no_enter_segment"] += 1
        elif exit_ is not None:
            if exit_ < enter:
                exit_ = None
            elif (exit_ - enter) > timedelta(hours=max_segment_hours):
                # The legacy system routinely paired an enter with an exit days later.
                # Keeping those would poison working_hours; they were never closed.
                exit_ = None
                stats["unclosed_long"] += 1
        logs.append((row["user_id"], enter, exit_))

    return people, logs, accounts, stats, synthetic_ids


async def run(args) -> None:
    people, logs, accounts, stats, synthetic_ids = await fetch_source(
        args.source, args.tz_offset, args.max_segment_hours
    )
    print(f"source: {len(people)} people, {len(logs)} usable logs, {len(accounts)} accounts")
    print("  " + ", ".join(f"{k}={v}" for k, v in stats.items() if v))

    photos_dir = Path(args.photos_dest) if args.photos_dest else None
    if photos_dir and not photos_dir.is_dir():
        print(f"  photos: {photos_dir} does not exist - image_path left empty")
        photos_dir = None

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
                {"device_ip": ip, "login": lg, "password": pw,
                 "direction": direction, "is_active": active}
                for ip, lg, pw, direction, active in SNAPSHOT_CAMERAS
            ]
            rows.append({"device_ip": IMPORT_CAMERA_IP, "login": "import",
                         "password": "import", "direction": DirectionType.ENTER,
                         "is_active": False})
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
            dept_ids = dict((await conn.execute(select(Department.name, Department.id))).all())

            # ---- phase 3: employees ----------------------------------------------
            existing_jshir = set((await conn.execute(select(Employee.jshir))).scalars().all())
            existing_passports = set(
                (await conn.execute(select(Employee.passport_series))).scalars().all()
            ) - {None}

            emp_rows: list[dict] = []
            emitted: set[str] = set()
            photos_linked = 0
            for payload in people.values():
                jshir = payload["jshir"]
                if jshir in existing_jshir or jshir in emitted:
                    continue          # a duplicate legacy row for a person already queued
                emitted.add(jshir)

                passport = payload["passport_series"]
                if passport and passport in existing_passports:
                    passport = None

                image_path = None
                if photos_dir and payload["photo"]:
                    if (photos_dir / payload["photo"]).is_file():
                        image_path = f"{args.photos_dest.strip('/')}/{payload['photo']}"
                        photos_linked += 1

                emp_rows.append({
                    "jshir": jshir,
                    "first_name": payload["first_name"],
                    "last_name": payload["last_name"],
                    "third_name": payload["third_name"],
                    "passport_series": passport,
                    "image_path": image_path,
                    "department_id": dept_ids.get(payload["department"]),
                    "in_work": False,
                    "work_rate": 1.0,
                })
            if emp_rows:
                await conn.execute(
                    pg_insert(Employee).on_conflict_do_nothing(index_elements=["jshir"]),
                    emp_rows,
                )
            candidates["employees"] = len(emp_rows)
            if photos_dir:
                notes.append(f"photos linked to employees: {photos_linked}")

            emp_by_jshir = dict((await conn.execute(select(Employee.jshir, Employee.id))).all())
            legacy_to_emp = {
                lid: emp_by_jshir[p["jshir"]]
                for lid, p in people.items()
                if p["jshir"] in emp_by_jshir
            }

            # ---- phase 4: legacy login accounts ----------------------------------
            if accounts:
                taken = set((await conn.execute(select(User.username))).scalars().all())
                fresh, seen = [], set()
                for a in accounts:
                    if a["username"] in taken or a["username"] in seen:
                        continue
                    seen.add(a["username"])
                    fresh.append(a)
                if fresh:
                    await conn.execute(
                        pg_insert(User).on_conflict_do_nothing(index_elements=["username"]),
                        fresh,
                    )
                candidates["users"] = len(fresh)

            # ---- phase 5: attendance segments ------------------------------------
            already = await conn.scalar(
                select(Attendance.id).where(Attendance.camera_id == import_camera_id).limit(1)
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
                        if enter is not None and exit_ is not None
                        else None
                    )
                    batch.append({
                        "employee_id": emp_id,
                        "camera_id": import_camera_id,
                        "enter_time": enter,
                        "exit_time": exit_,
                        "working_hours": hours,
                    })
                    if len(batch) >= args.batch_size:
                        await conn.execute(pg_insert(Attendance), batch)
                        total += len(batch)
                        batch = []
                if batch:
                    await conn.execute(pg_insert(Attendance), batch)
                    total += len(batch)
                candidates["attendance"] = total

            # ---- phase 6: daily aggregation --------------------------------------
            # A Core connection yields plain rows, so rebuild the ORM object that
            # compute_status() expects.
            schedule = None
            if schedule_id is not None:
                row = (await conn.execute(
                    select(WorkSchedule.start_time, WorkSchedule.end_time,
                           WorkSchedule.grace_minutes).where(WorkSchedule.id == schedule_id)
                )).first()
                if row is not None:
                    schedule = WorkSchedule(
                        start_time=row.start_time,
                        end_time=row.end_time,
                        grace_minutes=row.grace_minutes,
                    )

            agg: dict[tuple[int, object], dict] = defaultdict(
                lambda: {"first_enter": None, "last_exit": None, "hours": 0.0,
                         "open": False, "no_enter": False}
            )
            for legacy_id, enter, exit_ in logs:
                emp_id = legacy_to_emp.get(legacy_id)
                if emp_id is None:
                    continue
                day = (enter or exit_).date()
                cell = agg[(emp_id, day)]
                if enter is None:
                    cell["no_enter"] = True
                else:
                    if cell["first_enter"] is None or enter < cell["first_enter"]:
                        cell["first_enter"] = enter
                    if exit_ is None:
                        cell["open"] = True
                if exit_ is not None:
                    if cell["last_exit"] is None or exit_ > cell["last_exit"]:
                        cell["last_exit"] = exit_
                    if enter is not None:
                        cell["hours"] += (exit_ - enter).total_seconds() / 3600.0

            daily_rows = []
            for (emp_id, day), cell in agg.items():
                no_enter = cell["no_enter"] and cell["first_enter"] is None
                probe = DailyAttendance(
                    employee_id=emp_id, date=day,
                    total_working_hours=cell["hours"],
                    first_enter_time=cell["first_enter"],
                    last_exit_time=cell["last_exit"],
                    has_no_enter=no_enter,
                    has_no_exit=cell["open"],
                )
                daily_rows.append({
                    "employee_id": emp_id, "date": day,
                    "status": compute_status(schedule, probe),
                    "total_working_hours": cell["hours"],
                    "first_enter_time": cell["first_enter"],
                    "last_exit_time": cell["last_exit"],
                    "has_no_enter": no_enter,
                    "has_no_exit": cell["open"],
                })

            for start in range(0, len(daily_rows), args.batch_size):
                await conn.execute(
                    pg_insert(DailyAttendance).on_conflict_do_nothing(
                        index_elements=["employee_id", "date"]
                    ),
                    daily_rows[start : start + args.batch_size],
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
    if synthetic_ids:
        print(f"\n  synthetic JSHIRs ({len(synthetic_ids)}) - correct these by hand:")
        for line in synthetic_ids:
            print(f"    {line}")
    print()
    print("APPLIED" if args.apply else "DRY RUN - rolled back, nothing written")


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--source", required=True, help="DSN of the legacy face_recognation DB")
    p.add_argument("--target", default=None, help="DSN of camera_base (default: backend .env)")
    p.add_argument("--apply", action="store_true", help="commit; without it the run rolls back")
    p.add_argument("--photos-dest", default="uploads/faces",
                   help="directory already holding the legacy photos (default uploads/faces)")
    p.add_argument("--tz-offset", type=int, default=5,
                   help="legacy timestamptz -> local hours (default 5)")
    p.add_argument("--schedule-id", type=int, default=None,
                   help="work schedule for imported departments")
    p.add_argument("--max-segment-hours", type=float, default=24.0,
                   help="exits later than this after the enter are dropped as never-closed")
    p.add_argument("--batch-size", type=int, default=5000)
    args = p.parse_args()
    if args.target is None:
        args.target = settings.database.url
    elif args.target.startswith("postgresql://"):
        args.target = args.target.replace("postgresql://", "postgresql+asyncpg://", 1)
    return args


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
