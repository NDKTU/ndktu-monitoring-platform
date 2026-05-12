from fastapi import HTTPException, status

from app.models.work_schedules.model import WorkSchedule
from app.modules.work_schedule.repository import WorkScheduleRepository
from app.modules.work_schedule.schemas import (
    WorkScheduleCreateRequest,
    WorkScheduleUpdateRequest,
    WorkScheduleListRequest,
    WorkScheduleListResponse,
)


class WorkScheduleService:
    def __init__(self, repository: WorkScheduleRepository) -> None:
        self.repository = repository

    async def create_schedule(self, schedule: WorkScheduleCreateRequest) -> WorkSchedule:
        existing = await self.repository.get_by_employee(schedule.employee_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Schedule already exists for employee {schedule.employee_id}",
            )
        return await self.repository.create_schedule(schedule)

    async def list_schedules(self, request: WorkScheduleListRequest) -> WorkScheduleListResponse:
        return await self.repository.list_schedules(request)

    async def get_schedule(self, schedule_id: int) -> WorkSchedule:
        schedule = await self.repository.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Work schedule not found"
            )
        return schedule

    async def update_schedule(
        self, schedule_id: int, schedule: WorkScheduleUpdateRequest
    ) -> WorkSchedule:
        updated = await self.repository.update_schedule(schedule_id, schedule)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Work schedule not found"
            )
        return updated

    async def delete_schedule(self, schedule_id: int) -> WorkSchedule:
        deleted = await self.repository.delete_schedule(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Work schedule not found"
            )
        return deleted
