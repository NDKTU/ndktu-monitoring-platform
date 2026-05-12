from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.attendance.repository import AttendanceRepository
from app.modules.attendance.service import AttendanceService
from app.modules.attendance.schemas import (
    AttendanceListRequest,
    AttendanceListResponse,
    AttendanceResponse,
)

router = APIRouter(
    tags=["Attendance"],
    prefix="/attendance",
)


def get_attendance_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> AttendanceService:
    repository = AttendanceRepository(session)
    return AttendanceService(repository)


@router.get("/list", response_model=AttendanceListResponse)
async def list_events(
    request: AttendanceListRequest = Depends(),
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.list_events(request)


@router.get("/{event_id}", response_model=AttendanceResponse)
async def get_event(
    event_id: int,
    service: AttendanceService = Depends(get_attendance_service),
):
    return await service.get_event(event_id)
