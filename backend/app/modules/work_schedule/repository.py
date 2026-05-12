from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_schedules.model import WorkSchedule
from app.modules.work_schedule.schemas import (
    WorkScheduleCreateRequest,
    WorkScheduleUpdateRequest,
    WorkScheduleListRequest,
    WorkScheduleListResponse,
    WorkScheduleResponse,
)


class WorkScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_schedule(self, schedule: WorkScheduleCreateRequest) -> WorkSchedule:
        db_schedule = WorkSchedule(**schedule.model_dump())
        self.session.add(db_schedule)
        await self.session.commit()
        await self.session.refresh(db_schedule)
        return db_schedule

    async def list_schedules(self, request: WorkScheduleListRequest) -> WorkScheduleListResponse:
        query = select(WorkSchedule)
        if request.employee_id:
            query = query.where(WorkSchedule.employee_id == request.employee_id)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(request.offset).limit(request.limit)
        result = await self.session.execute(query)
        schedules = result.scalars().all()

        return WorkScheduleListResponse(
            schedules=[WorkScheduleResponse.model_validate(s) for s in schedules],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_schedule(self, schedule_id: int) -> WorkSchedule | None:
        result = await self.session.execute(
            select(WorkSchedule).where(WorkSchedule.id == schedule_id)
        )
        return result.scalar()

    async def get_by_employee(self, employee_id: int) -> WorkSchedule | None:
        result = await self.session.execute(
            select(WorkSchedule).where(WorkSchedule.employee_id == employee_id)
        )
        return result.scalar()

    async def update_schedule(
        self, schedule_id: int, schedule: WorkScheduleUpdateRequest
    ) -> WorkSchedule | None:
        db_schedule = await self.get_schedule(schedule_id)
        if not db_schedule:
            return None

        update_data = schedule.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_schedule, key, value)

        await self.session.commit()
        await self.session.refresh(db_schedule)
        return db_schedule

    async def delete_schedule(self, schedule_id: int) -> WorkSchedule | None:
        db_schedule = await self.get_schedule(schedule_id)
        if not db_schedule:
            return None
        await self.session.delete(db_schedule)
        await self.session.commit()
        return db_schedule
