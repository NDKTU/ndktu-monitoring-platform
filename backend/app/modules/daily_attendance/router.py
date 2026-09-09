from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.daily_attendance.repository import DailyAttendanceRepository
from app.modules.daily_attendance.service import DailyAttendanceService
from app.modules.daily_attendance.schemas import (
    DailyAttendanceListRequest,
    DailyAttendanceListResponse,
    DailyAttendanceResponse,
)
from app.modules.auth.dependencies import PermissionChecker

router = APIRouter(
    tags=["Daily Attendance"],
    prefix="/daily-attendance",
)


def get_daily_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> DailyAttendanceService:
    repository = DailyAttendanceRepository(session)
    return DailyAttendanceService(repository)


@router.get("/list", response_model=DailyAttendanceListResponse, dependencies=[Depends(PermissionChecker("daily_attendance:list"))])
async def list_items(
    request: DailyAttendanceListRequest = Depends(),
    service: DailyAttendanceService = Depends(get_daily_service),
):
    return await service.list_items(request)


@router.get("/{item_id}", response_model=DailyAttendanceResponse, dependencies=[Depends(PermissionChecker("daily_attendance:get"))])
async def get_item(
    item_id: int,
    service: DailyAttendanceService = Depends(get_daily_service),
):
    return await service.get_item(item_id)
