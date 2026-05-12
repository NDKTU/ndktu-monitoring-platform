from fastapi import HTTPException, status

from app.models.daily_attendance.model import DailyAttendance
from app.modules.daily_attendance.repository import DailyAttendanceRepository
from app.modules.daily_attendance.schemas import (
    DailyAttendanceListRequest,
    DailyAttendanceListResponse,
)


class DailyAttendanceService:
    def __init__(self, repository: DailyAttendanceRepository) -> None:
        self.repository = repository

    async def list_items(
        self, request: DailyAttendanceListRequest
    ) -> DailyAttendanceListResponse:
        return await self.repository.list_items(request)

    async def get_item(self, item_id: int) -> DailyAttendance:
        item = await self.repository.get_item(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily attendance not found",
            )
        return item
