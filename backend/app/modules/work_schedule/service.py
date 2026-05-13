from fastapi import HTTPException, status

from app.modules.work_schedule.repository import WorkScheduleRepository
from app.modules.work_schedule.schemas import (
    WorkScheduleCreateRequest,
    WorkScheduleEmployeesListRequest,
    WorkScheduleEmployeesListResponse,
    WorkScheduleEmployeeItem,
    WorkScheduleEmployeesRequest,
    WorkScheduleEmployeesResult,
    WorkScheduleListRequest,
    WorkScheduleListResponse,
    WorkScheduleResponse,
    WorkScheduleUpdateRequest,
)


class WorkScheduleService:
    def __init__(self, repository: WorkScheduleRepository) -> None:
        self.repository = repository

    async def create_schedule(
        self, schedule: WorkScheduleCreateRequest
    ) -> WorkScheduleResponse:
        existing = await self.repository.find_by_times(
            schedule.start_time, schedule.end_time, schedule.grace_minutes
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bunday ish jadvali allaqachon mavjud",
            )
        created = await self.repository.create_schedule(schedule)
        return WorkScheduleResponse(
            id=created.id,
            start_time=created.start_time,
            end_time=created.end_time,
            grace_minutes=created.grace_minutes,
            employee_count=0,
        )

    async def list_schedules(
        self, request: WorkScheduleListRequest
    ) -> WorkScheduleListResponse:
        total, rows = await self.repository.list_schedules(
            offset=request.offset, limit=request.limit
        )
        return WorkScheduleListResponse(
            total=total,
            page=request.page,
            limit=request.limit,
            schedules=[
                WorkScheduleResponse(
                    id=schedule.id,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time,
                    grace_minutes=schedule.grace_minutes,
                    employee_count=count,
                )
                for schedule, count in rows
            ],
        )

    async def get_schedule(self, schedule_id: int) -> WorkScheduleResponse:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        count = await self.repository.get_employee_count(schedule_id)
        return WorkScheduleResponse(
            id=schedule.id,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            grace_minutes=schedule.grace_minutes,
            employee_count=count,
        )

    async def update_schedule(
        self, schedule_id: int, schedule: WorkScheduleUpdateRequest
    ) -> WorkScheduleResponse:
        clash = await self.repository.find_by_times(
            schedule.start_time, schedule.end_time, schedule.grace_minutes
        )
        if clash is not None and clash.id != schedule_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bunday vaqtdagi jadval allaqachon mavjud",
            )
        updated = await self.repository.update_schedule(schedule_id, schedule)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        count = await self.repository.get_employee_count(schedule_id)
        return WorkScheduleResponse(
            id=updated.id,
            start_time=updated.start_time,
            end_time=updated.end_time,
            grace_minutes=updated.grace_minutes,
            employee_count=count,
        )

    async def delete_schedule(self, schedule_id: int) -> WorkScheduleResponse:
        deleted = await self.repository.delete_schedule(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        return WorkScheduleResponse(
            id=deleted.id,
            start_time=deleted.start_time,
            end_time=deleted.end_time,
            grace_minutes=deleted.grace_minutes,
            employee_count=0,
        )

    async def list_employees(
        self, schedule_id: int, request: WorkScheduleEmployeesListRequest
    ) -> WorkScheduleEmployeesListResponse:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        total, employees = await self.repository.list_employees(
            schedule_id, offset=request.offset, limit=request.limit
        )
        return WorkScheduleEmployeesListResponse(
            total=total,
            page=request.page,
            limit=request.limit,
            employees=[WorkScheduleEmployeeItem.model_validate(e) for e in employees],
        )

    async def assign_employees(
        self, schedule_id: int, payload: WorkScheduleEmployeesRequest
    ) -> WorkScheduleEmployeesResult:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        affected = await self.repository.assign_employees(schedule_id, payload.employee_ids)
        return WorkScheduleEmployeesResult(affected=affected)

    async def unassign_employees(
        self, schedule_id: int, payload: WorkScheduleEmployeesRequest
    ) -> WorkScheduleEmployeesResult:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ish jadvali topilmadi"
            )
        affected = await self.repository.unassign_employees(schedule_id, payload.employee_ids)
        return WorkScheduleEmployeesResult(affected=affected)
