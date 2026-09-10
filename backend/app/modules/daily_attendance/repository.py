from datetime import date as date_type

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_attendance.model import DailyAttendance
from app.models.employees.model import Employee
from app.models.tabel_entries.model import TabelEntry
from app.modules.daily_attendance.schemas import (
    DailyAttendanceListRequest,
    DailyAttendanceListResponse,
    DailyAttendanceResponse,
)


class DailyAttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_items(
        self, request: DailyAttendanceListRequest
    ) -> DailyAttendanceListResponse:
        query = select(DailyAttendance).options(selectinload(DailyAttendance.employee))

        if request.employee_id:
            query = query.where(DailyAttendance.employee_id == request.employee_id)
        if request.date_from:
            query = query.where(DailyAttendance.date >= request.date_from)
        if request.date_to:
            query = query.where(DailyAttendance.date <= request.date_to)
        if request.status:
            query = query.where(DailyAttendance.status == request.status)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.order_by(DailyAttendance.date.desc()).offset(request.offset).limit(request.limit)
        result = await self.session.execute(query)
        items = result.scalars().all()

        return DailyAttendanceListResponse(
            items=[DailyAttendanceResponse.model_validate(i) for i in items],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_item(self, item_id: int) -> DailyAttendance | None:
        result = await self.session.execute(
            select(DailyAttendance)
            .options(selectinload(DailyAttendance.employee))
            .where(DailyAttendance.id == item_id)
        )
        return result.scalar()

    async def get_range(
        self, employee_id: int, date_from: date_type, date_to: date_type
    ) -> list[DailyAttendance]:
        """Every stored row for one employee inside a closed date range."""
        result = await self.session.execute(
            select(DailyAttendance)
            .options(selectinload(DailyAttendance.employee))
            .where(
                DailyAttendance.employee_id == employee_id,
                DailyAttendance.date >= date_from,
                DailyAttendance.date <= date_to,
            )
        )
        return list(result.scalars().all())

    async def get_tracking_start(self, employee_id: int) -> date_type | None:
        """First day we could honestly call this person absent.

        Absence is only meaningful once the terminals were recording *and* the
        person was registered, so it is the later of those two. A row older than
        that (the event-log backfill reaches further back than either) wins over
        both — we plainly do have data for that day.
        """
        system_start = await self.session.scalar(select(func.min(DailyAttendance.date)))
        employee_first = await self.session.scalar(
            select(func.min(DailyAttendance.date)).where(
                DailyAttendance.employee_id == employee_id
            )
        )
        created_at = await self.session.scalar(
            select(Employee.created_at).where(Employee.id == employee_id)
        )
        created_day = created_at.date() if created_at else None

        candidates = [d for d in (system_start, created_day) if d is not None]
        start = max(candidates) if candidates else None

        if employee_first is not None and (start is None or employee_first < start):
            return employee_first
        return start

    async def get_tabel_overrides(
        self, employee_id: int, date_from: date_type, date_to: date_type
    ) -> list[TabelEntry]:
        """Hand-set tabel marks for one employee inside a closed date range."""
        result = await self.session.execute(
            select(TabelEntry).where(
                TabelEntry.employee_id == employee_id,
                TabelEntry.date >= date_from,
                TabelEntry.date <= date_to,
            )
        )
        return list(result.scalars().all())
