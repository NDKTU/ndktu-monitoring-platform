"""Backfill attendance from the event log the Hikvision terminals keep themselves.

The terminals retain roughly a year of access events — about 257 000 across the six
devices — including everything that happened while the platform could not match
anyone. Those events carry the same identity fields as the live stream, so they can
be replayed through the very same domain logic and come out indistinguishable from
events recorded as they happened.

Usage (from backend/ dir, or inside the ndktu_backend container):

    # Dry run — replays everything in a transaction, then rolls back:
    uv run python scripts/import_camera_events.py --from 2026-06-05
    # Apply:
    uv run python scripts/import_camera_events.py --from 2026-06-05 --apply

Only `minor 75` records are imported: those are successful identifications. Door
open/close (21/22) carry no person and are not attendance.

Re-runnable: an event whose timestamp already exists for that employee and camera is
skipped, so overlapping ranges do not double-count.

Cameras are read over ISAPI with the credentials stored in the cameras table. Nothing
on the devices is modified.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.attendance.model import Attendance
from app.models.cameras.model import Cameras
from app.models.employees.model import Employee
from app.modules.attendance.status_service import apply_enter, apply_exit

LOCAL_TZ = timezone(timedelta(hours=5))
RECOGNITION_MINOR = 75
# The terminals cap a page at 30 regardless of what is asked for.
PAGE = 30
MAX_RETRIES = 5


class _Rollback(Exception):
    """Raised to unwind the transaction after a dry run."""


def _naive(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except Exception:  # noqa: BLE001
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(LOCAL_TZ).replace(tzinfo=None)
    return parsed


async def read_events(
    ip: str, login: str, password: str, start: str, end: str
) -> list[tuple[datetime, str, str]]:
    """Return [(time, employeeNo, name)] of identifications on one terminal."""
    url = f"http://{ip}/ISAPI/AccessControl/AcsEvent?format=json"
    out: list[tuple[datetime, str, str]] = []
    position = 0
    client: httpx.AsyncClient | None = None
    attempts = 0

    def _fresh() -> httpx.AsyncClient:
        # The device expires its digest nonce after roughly eighty requests and then
        # answers 401; a new client renegotiates instead of stalling the read.
        return httpx.AsyncClient(auth=httpx.DigestAuth(login, password), timeout=60)

    try:
        client = _fresh()
        while True:
            body = {
                "AcsEventCond": {
                    "searchID": "backfill",
                    "searchResultPosition": position,
                    "maxResults": PAGE,
                    "major": 5,
                    "minor": RECOGNITION_MINOR,
                    "startTime": start,
                    "endTime": end,
                }
            }
            try:
                response = await client.post(url, json=body)
                response.raise_for_status()
                block = json.loads(response.text)["AcsEvent"]
                attempts = 0
            except Exception:  # noqa: BLE001
                attempts += 1
                if attempts > MAX_RETRIES:
                    break
                await client.aclose()
                await asyncio.sleep(1.0)
                client = _fresh()
                continue

            rows = block.get("InfoList", []) or []
            for row in rows:
                when = _naive(row.get("time", ""))
                if when is None:
                    continue
                out.append(
                    (
                        when,
                        (row.get("employeeNoString") or "").strip(),
                        (row.get("name") or "").strip(),
                    )
                )
            if block.get("responseStatusStrg") != "MORE" or not rows:
                break
            # Advance by what was actually returned, not by what was requested:
            # overshooting the cursor makes the device reject the next query.
            position += len(rows)
    finally:
        if client is not None:
            await client.aclose()
    return out


async def run(args) -> None:
    start = f"{args.date_from}T00:00:00+05:00"
    end = f"{args.date_to}T23:59:59+05:00"
    engine = create_async_engine(args.target, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    report: list[str] = []

    try:
        async with factory() as session:
            cameras = (
                await session.execute(
                    select(
                        Cameras.id, Cameras.device_ip, Cameras.login,
                        Cameras.password, Cameras.direction,
                    ).where(Cameras.device_ip != "0.0.0.0")
                )
            ).all()

            # (time, camera_id, direction, employeeNo, name), replayed in order:
            # apply_enter/apply_exit pair segments by sequence, so chronology matters
            # more than which device an event came from.
            events: list[tuple[datetime, int, str, str, str]] = []
            for cam_id, ip, login, password, direction in cameras:
                try:
                    rows = await read_events(ip, login, password, start, end)
                    report.append(f"  {ip:<16} {direction.value:<6} events: {len(rows)}")
                    for when, code, name in rows:
                        events.append((when, cam_id, direction.value, code, name))
                except Exception as exc:  # noqa: BLE001
                    report.append(f"  {ip:<16} unreachable: {type(exc).__name__}")
            events.sort(key=lambda e: e[0])
            report.append(f"  total identifications: {len(events)}")
            if not events:
                raise _Rollback

            by_code = {
                c: i
                for i, c in (
                    await session.execute(
                        select(Employee.id, Employee.camera_code).where(
                            Employee.camera_code.is_not(None)
                        )
                    )
                ).all()
            }
            by_jshir = {
                j: i
                for i, j in (
                    await session.execute(select(Employee.id, Employee.jshir))
                ).all()
            }
            seen = {
                (e, c, t)
                for e, c, t in (
                    await session.execute(
                        select(
                            Attendance.employee_id,
                            Attendance.camera_id,
                            Attendance.enter_time,
                        )
                    )
                ).all()
            } | {
                (e, c, t)
                for e, c, t in (
                    await session.execute(
                        select(
                            Attendance.employee_id,
                            Attendance.camera_id,
                            Attendance.exit_time,
                        )
                    )
                ).all()
            }

            imported = skipped_known = unmatched = duplicate = 0
            cache: dict[int, Employee] = {}

            for when, cam_id, direction, code, name in events:
                emp_id = by_code.get(code) or by_jshir.get(name) or by_jshir.get(code)
                if emp_id is None:
                    unmatched += 1
                    continue
                if (emp_id, cam_id, when) in seen:
                    duplicate += 1
                    continue

                employee = cache.get(emp_id)
                if employee is None:
                    employee = await session.get(Employee, emp_id)
                    cache[emp_id] = employee

                if direction == "enter":
                    await apply_enter(session, employee, cam_id, when, None)
                else:
                    await apply_exit(session, employee, cam_id, when, None)
                seen.add((emp_id, cam_id, when))
                imported += 1

                if imported % 2000 == 0:
                    await session.flush()
                    report.append(f"    …{imported} replayed")

            await session.flush()
            report.append("")
            report.append(f"  imported : {imported}")
            report.append(f"  duplicate: {duplicate}")
            report.append(f"  unmatched: {unmatched}")
            report.append(f"  ignored  : {skipped_known}")

            if args.apply:
                await session.commit()
            else:
                await session.rollback()
    except _Rollback:
        pass
    finally:
        await engine.dispose()

    print("\n".join(report))
    print()
    print("APPLIED" if args.apply else "DRY RUN - rolled back, nothing written")


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD")
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
