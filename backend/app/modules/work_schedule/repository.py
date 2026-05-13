from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employees.model import Employee
from app.models.work_schedules.model import WorkSchedule
from app.modules.work_schedule.schemas import (
    WorkScheduleCreateRequest,
    WorkScheduleUpdateRequest,
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

    async def find_by_times(
        self, start_time, end_time, grace_minutes: int
    ) -> WorkSchedule | None:
        result = await self.session.execute(
            select(WorkSchedule).where(
                WorkSchedule.start_time == start_time,
                WorkSchedule.end_time == end_time,
                WorkSchedule.grace_minutes == grace_minutes,
            )
        )
        return result.scalar_one_or_none()

    async def list_schedules(
        self, offset: int, limit: int
    ) -> tuple[int, list[tuple[WorkSchedule, int]]]:
        employee_count = func.count(Employee.id)
        rows_stmt = (
            select(WorkSchedule, employee_count.label("employee_count"))
            .outerjoin(Employee, Employee.work_schedule_id == WorkSchedule.id)
            .group_by(WorkSchedule.id)
            .order_by(WorkSchedule.start_time, WorkSchedule.end_time)
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(rows_stmt)).all()

        total_stmt = select(func.count()).select_from(WorkSchedule)
        total = (await self.session.execute(total_stmt)).scalar() or 0

        return total, [(row[0], int(row[1] or 0)) for row in rows]

    async def get_schedule(self, schedule_id: int) -> WorkSchedule | None:
        result = await self.session.execute(
            select(WorkSchedule).where(WorkSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_employee_count(self, schedule_id: int) -> int:
        stmt = select(func.count(Employee.id)).where(
            Employee.work_schedule_id == schedule_id
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def update_schedule(
        self, schedule_id: int, schedule: WorkScheduleUpdateRequest
    ) -> WorkSchedule | None:
        db_schedule = await self.get_schedule(schedule_id)
        if not db_schedule:
            return None

        for key, value in schedule.model_dump().items():
            setattr(db_schedule, key, value)

        await self.session.commit()
        await self.session.refresh(db_schedule)
        return db_schedule

    async def delete_schedule(self, schedule_id: int) -> WorkSchedule | None:
        db_schedule = await self.get_schedule(schedule_id)
        if not db_schedule:
            return None
        await self.session.execute(
            update(Employee)
            .where(Employee.work_schedule_id == schedule_id)
            .values(work_schedule_id=None)
        )
        await self.session.delete(db_schedule)
        await self.session.commit()
        return db_schedule

    async def list_employees(
        self, schedule_id: int, offset: int, limit: int
    ) -> tuple[int, list[Employee]]:
        base = select(Employee).where(Employee.work_schedule_id == schedule_id)

        total_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(total_stmt)).scalar() or 0

        rows_stmt = base.order_by(Employee.last_name, Employee.first_name).offset(offset).limit(limit)
        employees = (await self.session.execute(rows_stmt)).scalars().all()
        return int(total), list(employees)

    async def assign_employees(
        self, schedule_id: int, employee_ids: list[int]
    ) -> int:
        if not employee_ids:
            return 0
        result = await self.session.execute(
            update(Employee)
            .where(Employee.id.in_(employee_ids))
            .values(work_schedule_id=schedule_id)
        )
        await self.session.commit()
        return int(result.rowcount or 0)

    async def unassign_employees(
        self, schedule_id: int, employee_ids: list[int]
    ) -> int:
        if not employee_ids:
            return 0
        result = await self.session.execute(
            update(Employee)
            .where(
                Employee.id.in_(employee_ids),
                Employee.work_schedule_id == schedule_id,
            )
            .values(work_schedule_id=None)
        )
        await self.session.commit()
        return int(result.rowcount or 0)
