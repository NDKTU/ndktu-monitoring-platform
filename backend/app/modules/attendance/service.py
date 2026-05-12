from fastapi import HTTPException, status

from app.models.attendance.model import Attendance
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.schemas import (
    AttendanceListRequest,
    AttendanceListResponse,
)


class AttendanceService:
    def __init__(self, repository: AttendanceRepository) -> None:
        self.repository = repository

    async def list_events(self, request: AttendanceListRequest) -> AttendanceListResponse:
        return await self.repository.list_events(request)

    async def get_event(self, event_id: int) -> Attendance:
        event = await self.repository.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attendance event not found"
            )
        return event
