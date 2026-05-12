from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_attendance.model import DailyAttendance
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
