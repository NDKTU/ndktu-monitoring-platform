from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance.model import Attendance
from app.modules.attendance.schemas import (
    AttendanceListRequest,
    AttendanceListResponse,
    AttendanceResponse,
)


class AttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_events(self, request: AttendanceListRequest) -> AttendanceListResponse:
        query = select(Attendance).options(selectinload(Attendance.employee))

        if request.employee_id:
            query = query.where(Attendance.employee_id == request.employee_id)
        if request.camera_id:
            query = query.where(Attendance.camera_id == request.camera_id)
        if request.enter_time:
            query = query.where(Attendance.enter_time >= request.enter_time)
        if request.exit_time:
            query = query.where(Attendance.exit_time <= request.exit_time)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(request.offset).limit(request.limit)
        events_result = await self.session.execute(query)
        event_list = events_result.scalars().all()

        return AttendanceListResponse(
            events=[AttendanceResponse.model_validate(e) for e in event_list],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_event(self, event_id: int) -> Attendance | None:
        result = await self.session.execute(
            select(Attendance)
            .options(selectinload(Attendance.employee))
            .where(Attendance.id == event_id)
        )
        return result.scalar()
