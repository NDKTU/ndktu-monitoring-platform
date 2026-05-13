"""Seed script: populates all tables with test data.

Usage (from backend/ dir):
    uv run python scripts/seed.py

Re-runnable: skips rows that already exist (by unique key).
"""
from __future__ import annotations

import asyncio
import hashlib
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

# Allow running as `python scripts/seed.py` from backend/ — make `app` importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.models.attendance.model import Attendance
from app.models.cameras.model import Cameras, DirectionType
from app.models.daily_attendance.model import AttendanceStatus, DailyAttendance
from app.models.employees.model import Employee
from app.models.users.model import User
from app.models.work_schedules.model import WorkSchedule


# ── static data ─────────────────────────────────────────────────────────

USERS: list[dict] = [
    {"username": "admin",    "password": "admin",    "is_active": True,  "is_superuser": True},
    {"username": "manager",  "password": "manager",  "is_active": True,  "is_superuser": False},
    {"username": "operator", "password": "operator", "is_active": True,  "is_superuser": False},
    {"username": "viewer",   "password": "viewer",   "is_active": True,  "is_superuser": False},
    {"username": "disabled", "password": "disabled", "is_active": False, "is_superuser": False},
]

CAMERAS: list[dict] = [
    {"device_ip": "192.168.10.1", "login": "admin", "password": "admin12345", "direction": DirectionType.ENTER, "is_active": False},
    {"device_ip": "192.168.10.2", "login": "admin", "password": "admin12345", "direction": DirectionType.ENTER, "is_active": False},
    {"device_ip": "192.168.10.3", "login": "admin", "password": "admin12345", "direction": DirectionType.ENTER, "is_active": False},
    {"device_ip": "192.168.20.1", "login": "admin", "password": "admin12345", "direction": DirectionType.EXIT,  "is_active": False},
    {"device_ip": "192.168.20.2", "login": "admin", "password": "admin12345", "direction": DirectionType.EXIT,  "is_active": False},
    {"device_ip": "192.168.20.3", "login": "admin", "password": "admin12345", "direction": DirectionType.EXIT,  "is_active": False},
]

LAST_NAMES = [
    "Valiyev", "Karimov", "Yusupov", "Saidov", "Tursunov",
    "Abdullayev", "Rahimov", "Nazarov", "O'rinov", "Mirzayev",
    "Mahmudov", "Shukurov", "Toshpo'latov", "Bekmurodov", "Sharipov",
]
FIRST_NAMES = [
    "Akmal", "Bobur", "Davron", "Elbek", "Farrux",
    "G'ayrat", "Husan", "Ibrohim", "Javlon", "Komil",
    "Latif", "Murod", "Nodir", "Otabek", "Po'lat",
]
THIRD_NAMES = [
    "Akmal o'g'li", "Bobur o'g'li", "Davron o'g'li", "Elbek o'g'li",
    "Farrux o'g'li", "Husan o'g'li", "Ibrohim o'g'li",
    "Javlon o'g'li", "Komil o'g'li", "Nodir o'g'li",
]

SCHEDULES: list[tuple[time, time, int]] = [
    (time(9, 0),  time(18, 0), 15),
    (time(8, 30), time(17, 30), 10),
    (time(10, 0), time(19, 0), 20),
]

LUNCH_START = time(12, 0)   # end of morning segment
LUNCH_END = time(13, 0)     # start of afternoon segment

EMPLOYEE_COUNT = 70
HISTORY_DAYS = 60
BATCH_SIZE = 500


# ── helpers ─────────────────────────────────────────────────────────────

def _stable_pct(emp_id: int, d: date) -> int:
    """Return a deterministic int in [0, 99] for (employee, date)."""
    key = f"{emp_id}-{d.isoformat()}".encode()
    return int(hashlib.md5(key).hexdigest(), 16) % 100


def _employee_schedule_index(emp: Employee) -> int:
    """Pick a SCHEDULES slot for an employee based on jshir suffix (stable)."""
    try:
        idx = int(emp.jshir[-8:])
    except ValueError:
        idx = emp.id
    return idx % len(SCHEDULES)


def gen_employee(i: int) -> dict:
    return {
        "first_name": FIRST_NAMES[i % len(FIRST_NAMES)],
        "last_name":  LAST_NAMES[i % len(LAST_NAMES)],
        "third_name": THIRD_NAMES[i % len(THIRD_NAMES)],
        "passport_series": f"AA{1000000 + i:07d}" if i % 2 == 0 else None,
        "jshir": f"301019{i:08d}",
        "in_work": i % 5 != 0,
        "image_path": None,
    }


def pick_status_and_offsets(emp_id: int, d: date) -> tuple[AttendanceStatus, int, int]:
    """Return (status, enter_minutes_offset, exit_minutes_offset) for a weekday.

    Offsets are minutes relative to scheduled start/end. -1 means "no event".
    """
    p = _stable_pct(emp_id, d)
    if p < 85:
        return AttendanceStatus.ON_TIME, 0, 0
    if p < 94:
        return AttendanceStatus.LATE_ARRIVAL, 25, 0
    if p < 97:
        return AttendanceStatus.EARLY_LEAVE, 0, -30
    if p == 97:
        return AttendanceStatus.LATE_AND_EARLY, 25, -30
    if p == 98:
        return AttendanceStatus.NO_ENTER, -1, 0
    return AttendanceStatus.NO_EXIT, 0, -1


def combine(d: date, t: time, offset_minutes: int) -> datetime:
    return datetime.combine(d, t) + timedelta(minutes=offset_minutes)


# ── async seeders ───────────────────────────────────────────────────────

async def seed_users(session: AsyncSession) -> int:
    target_names = [u["username"] for u in USERS]
    existing = await session.execute(
        select(User.username).where(User.username.in_(target_names))
    )
    existing_set = set(existing.scalars().all())
    to_add = [User(**u) for u in USERS if u["username"] not in existing_set]
    if to_add:
        session.add_all(to_add)
        await session.commit()
    print(f"[users]     added={len(to_add)} kept={len(existing_set)}")
    return len(USERS)


async def seed_cameras(session: AsyncSession) -> list[Cameras]:
    target_ips = [c["device_ip"] for c in CAMERAS]
    existing = await session.execute(
        select(Cameras).where(Cameras.device_ip.in_(target_ips))
    )
    existing_map = {c.device_ip: c for c in existing.scalars().all()}
    to_add = [
        Cameras(**c) for c in CAMERAS if c["device_ip"] not in existing_map
    ]
    if to_add:
        session.add_all(to_add)
        await session.commit()
        for cam in to_add:
            await session.refresh(cam)
        for cam in to_add:
            existing_map[cam.device_ip] = cam
    print(f"[cameras]   added={len(to_add)} kept={len(existing_map) - len(to_add)}")
    # preserve original order
    return [existing_map[c["device_ip"]] for c in CAMERAS]


async def seed_employees(session: AsyncSession) -> list[Employee]:
    target_jshirs = [f"301019{i:08d}" for i in range(EMPLOYEE_COUNT)]
    existing = await session.execute(
        select(Employee).where(Employee.jshir.in_(target_jshirs))
    )
    existing_map = {e.jshir: e for e in existing.scalars().all()}
    to_add: list[Employee] = []
    for i in range(EMPLOYEE_COUNT):
        data = gen_employee(i)
        if data["jshir"] in existing_map:
            continue
        to_add.append(Employee(**data))
    if to_add:
        session.add_all(to_add)
        await session.commit()
        for emp in to_add:
            await session.refresh(emp)
            existing_map[emp.jshir] = emp
    print(f"[employees] added={len(to_add)} kept={len(existing_map) - len(to_add)}")
    # preserve index order
    return [existing_map[f"301019{i:08d}"] for i in range(EMPLOYEE_COUNT)]


async def seed_schedules(
    session: AsyncSession, employees: list[Employee]
) -> None:
    # 1. Upsert the 3 schedule templates.
    existing = await session.execute(select(WorkSchedule))
    by_key: dict[tuple[time, time, int], WorkSchedule] = {
        (s.start_time, s.end_time, s.grace_minutes): s
        for s in existing.scalars().all()
    }

    added_templates = 0
    for start, end, grace in SCHEDULES:
        key = (start, end, grace)
        if key in by_key:
            continue
        ws = WorkSchedule(start_time=start, end_time=end, grace_minutes=grace)
        session.add(ws)
        added_templates += 1
        by_key[key] = ws

    if added_templates:
        await session.commit()
        # refresh new rows to populate their .id
        for ws in by_key.values():
            if ws.id is None:
                await session.refresh(ws)

    # 2. Assign templates to employees who don't yet have one.
    assigned = 0
    for emp in employees:
        if emp.work_schedule_id is not None:
            continue
        start, end, grace = SCHEDULES[_employee_schedule_index(emp)]
        ws = by_key[(start, end, grace)]
        await session.execute(
            update(Employee)
            .where(Employee.id == emp.id)
            .values(work_schedule_id=ws.id)
        )
        emp.work_schedule_id = ws.id
        assigned += 1

    if assigned:
        await session.commit()

    print(
        f"[schedules] templates_added={added_templates} "
        f"employees_assigned={assigned} kept={len(employees) - assigned}"
    )


async def seed_attendance(
    session: AsyncSession,
    employees: list[Employee],
    enter_cam_ids: list[int],
    exit_cam_ids: list[int],
) -> None:
    # Determine the date window (exclude today).
    today = date.today()
    window = [today - timedelta(days=d) for d in range(1, HISTORY_DAYS + 1)]

    # Pull all already-seeded (employee_id, date) pairs in one query.
    emp_ids = [e.id for e in employees]
    existing = await session.execute(
        select(DailyAttendance.employee_id, DailyAttendance.date).where(
            DailyAttendance.employee_id.in_(emp_ids),
            DailyAttendance.date.in_(window),
        )
    )
    have_pairs = {(eid, d) for eid, d in existing.all()}

    # Map employee_id -> schedule tuple (by index used when seeding).
    sched_by_emp: dict[int, tuple[time, time, int]] = {
        emp.id: SCHEDULES[_employee_schedule_index(emp)] for emp in employees
    }

    daily_buf: list[DailyAttendance] = []
    att_buf: list[Attendance] = []
    added_daily = 0
    added_att = 0

    async def flush() -> None:
        nonlocal daily_buf, att_buf, added_daily, added_att
        if daily_buf:
            session.add_all(daily_buf)
            added_daily += len(daily_buf)
            daily_buf = []
        if att_buf:
            session.add_all(att_buf)
            added_att += len(att_buf)
            att_buf = []
        await session.commit()

    for emp in employees:
        start_t, end_t, _grace = sched_by_emp[emp.id]
        for d in window:
            if (emp.id, d) in have_pairs:
                continue

            if d.weekday() >= 5:
                # Weekend — single DailyAttendance with no events.
                daily_buf.append(
                    DailyAttendance(
                        employee_id=emp.id,
                        date=d,
                        status=None,
                        total_working_hours=0.0,
                        first_enter_time=None,
                        last_exit_time=None,
                        has_no_enter=True,
                        has_no_exit=True,
                    )
                )
            else:
                status, enter_off, exit_off = pick_status_and_offsets(emp.id, d)

                first_enter = (
                    combine(d, start_t, enter_off) if enter_off != -1 else None
                )
                last_exit = (
                    combine(d, end_t, exit_off) if exit_off != -1 else None
                )
                # Lunch break splits the day into two segments. We only emit
                # two segments when both ends of the day are present (the
                # NO_ENTER / NO_EXIT statuses keep a single broken segment).
                cam_a = enter_cam_ids[emp.id % 3]
                cam_b = enter_cam_ids[(emp.id + 1) % 3]
                exit_cam_a = exit_cam_ids[emp.id % 3]

                if first_enter is not None and last_exit is not None:
                    seg1_exit = combine(d, LUNCH_START, 0)
                    seg2_enter = combine(d, LUNCH_END, 0)
                    hours1 = round(
                        (seg1_exit - first_enter).total_seconds() / 3600, 2
                    )
                    hours2 = round(
                        (last_exit - seg2_enter).total_seconds() / 3600, 2
                    )
                    att_buf.append(
                        Attendance(
                            employee_id=emp.id,
                            camera_id=cam_a,
                            enter_time=first_enter,
                            exit_time=seg1_exit,
                            enter_image_path=None,
                            exit_image_path=None,
                            working_hours=hours1,
                        )
                    )
                    att_buf.append(
                        Attendance(
                            employee_id=emp.id,
                            camera_id=cam_b,
                            enter_time=seg2_enter,
                            exit_time=last_exit,
                            enter_image_path=None,
                            exit_image_path=None,
                            working_hours=hours2,
                        )
                    )
                    total_hours = round(hours1 + hours2, 2)
                elif first_enter is not None or last_exit is not None:
                    # Broken day (NO_ENTER or NO_EXIT) — keep a single row.
                    att_buf.append(
                        Attendance(
                            employee_id=emp.id,
                            camera_id=cam_a if first_enter else exit_cam_a,
                            enter_time=first_enter,
                            exit_time=last_exit,
                            enter_image_path=None,
                            exit_image_path=None,
                            working_hours=None,
                        )
                    )
                    total_hours = 0.0
                else:
                    total_hours = 0.0

                daily_buf.append(
                    DailyAttendance(
                        employee_id=emp.id,
                        date=d,
                        status=status,
                        total_working_hours=total_hours,
                        first_enter_time=first_enter,
                        last_exit_time=last_exit,
                        has_no_enter=(first_enter is None),
                        has_no_exit=(last_exit is None),
                    )
                )

            if len(daily_buf) + len(att_buf) >= BATCH_SIZE:
                await flush()

    await flush()
    print(
        f"[daily]     added={added_daily} kept={len(have_pairs)}\n"
        f"[attendance] added={added_att}"
    )


async def main() -> None:
    async for session in db_helper.session_getter():
        await seed_users(session)
        cameras = await seed_cameras(session)
        employees = await seed_employees(session)
        await seed_schedules(session, employees)

        enter_ids = [c.id for c in cameras if c.direction == DirectionType.ENTER]
        exit_ids = [c.id for c in cameras if c.direction == DirectionType.EXIT]
        if not enter_ids or not exit_ids:
            raise RuntimeError(
                "Expected at least one ENTER and one EXIT camera after seeding."
            )

        await seed_attendance(session, employees, enter_ids, exit_ids)
        print("Done.")
        break


if __name__ == "__main__":
    asyncio.run(main())
