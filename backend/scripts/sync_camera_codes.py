"""Fill employees.camera_code from what the Hikvision terminals actually hold.

Access events identify a person by `employeeNoString` — the code they were enrolled
under, not their JSHIR — so without this mapping every event is discarded. The
terminals store both fields per enrolled person (`employeeNo` and `name`, the latter
being the JSHIR, usually space-padded), which makes them the authoritative source: it
reflects who is really enrolled right now, not who a database once thought was.

Usage (from backend/ dir, or inside the ndktu_backend container):

    # Dry run — reports what it would change, writes nothing:
    uv run python scripts/sync_camera_codes.py
    # Apply:
    uv run python scripts/sync_camera_codes.py --apply

Cameras are read over ISAPI with the credentials stored in the cameras table. Only
read requests are made; nothing on the devices is modified.

Re-runnable: matching is by JSHIR, so a second run rewrites the same values.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models.cameras.model import Cameras
from app.models.employees.model import Employee

PAGE = 30
JSHIR_MAX = 16


class _Rollback(Exception):
    """Raised to unwind the transaction after a dry run."""


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


async def read_enrolled(ip: str, login: str, password: str) -> dict[str, str]:
    """Return {jshir -> employeeNo} for everyone enrolled on one terminal."""
    found: dict[str, str] = {}
    url = f"http://{ip}/ISAPI/AccessControl/UserInfo/Search?format=json"
    auth = httpx.DigestAuth(login, password)
    position = 0
    async with httpx.AsyncClient(auth=auth, timeout=30) as client:
        while True:
            body = {
                "UserInfoSearchCond": {
                    "searchID": "sync",
                    "searchResultPosition": position,
                    "maxResults": PAGE,
                }
            }
            response = await client.post(url, json=body)
            response.raise_for_status()
            block = json.loads(response.text)["UserInfoSearch"]
            for row in block.get("UserInfo", []):
                code = (row.get("employeeNo") or "").strip()
                jshir = (row.get("name") or "").strip()
                if code and jshir:
                    found.setdefault(jshir, code)
            if block.get("responseStatusStrg") != "MORE":
                break
            position += PAGE
    return found


async def run(args) -> None:
    engine = create_async_engine(args.target, echo=False)
    report: list[str] = []

    try:
        async with engine.begin() as conn:
            cameras = (
                await conn.execute(
                    select(Cameras.device_ip, Cameras.login, Cameras.password).where(
                        Cameras.device_ip != "0.0.0.0"
                    )
                )
            ).all()

            enrolled: dict[str, str] = {}
            for ip, login, password in cameras:
                try:
                    rows = await read_enrolled(ip, login, password)
                    report.append(f"  {ip:<16} enrolled: {len(rows)}")
                    for jshir, code in rows.items():
                        enrolled.setdefault(jshir, code)
                except Exception as exc:  # noqa: BLE001
                    report.append(f"  {ip:<16} unreachable: {type(exc).__name__}")

            report.append(f"  distinct people across terminals: {len(enrolled)}")
            if not enrolled:
                raise _Rollback

            employees = (
                await conn.execute(select(Employee.id, Employee.jshir))
            ).all()
            by_jshir = {j: i for i, j in employees}
            # A JSHIR that did not fit the old 14-char column was replaced at import
            # by a synthetic "LGC<legacy id>" — and that legacy id is exactly the code
            # the terminals have the person enrolled under, so it reconnects them.
            by_legacy_code: dict[str, int] = {}
            for emp_id, jshir in employees:
                if jshir.startswith("LGC"):
                    by_legacy_code[_digits(jshir).lstrip("0")] = emp_id

            code_updates: list[tuple[int, str]] = []
            jshir_repairs: list[tuple[int, str]] = []
            unmatched: list[str] = []

            for jshir, code in enrolled.items():
                emp_id = by_jshir.get(jshir)
                if emp_id is None:
                    emp_id = by_legacy_code.get(code.lstrip("0"))
                    # Longer than the column even after widening? Keep the
                    # synthetic id — camera_code alone is enough to match events.
                    if emp_id is not None and len(jshir) <= JSHIR_MAX:
                        jshir_repairs.append((emp_id, jshir))
                if emp_id is None:
                    unmatched.append(f"{code} / {jshir}")
                    continue
                code_updates.append((emp_id, code))

            for emp_id, jshir in jshir_repairs:
                await conn.execute(
                    update(Employee).where(Employee.id == emp_id).values(jshir=jshir)
                )
            for emp_id, code in code_updates:
                await conn.execute(
                    update(Employee).where(Employee.id == emp_id).values(camera_code=code)
                )

            report.append("")
            report.append(f"  camera_code set     : {len(code_updates)}")
            report.append(f"  jshir restored      : {len(jshir_repairs)}")
            report.append(f"  enrolled but unknown: {len(unmatched)}")
            for row in unmatched[:20]:
                report.append(f"      {row}")

            if not args.apply:
                raise _Rollback
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
