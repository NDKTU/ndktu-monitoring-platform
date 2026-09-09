from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.work_schedule.repository import WorkScheduleRepository
from app.modules.work_schedule.service import WorkScheduleService
from app.modules.work_schedule.schemas import (
    WorkScheduleCreateRequest,
    WorkScheduleEmployeesListRequest,
    WorkScheduleEmployeesListResponse,
    WorkScheduleEmployeesRequest,
    WorkScheduleEmployeesResult,
    WorkScheduleListRequest,
    WorkScheduleListResponse,
    WorkScheduleResponse,
    WorkScheduleUpdateRequest,
)
from app.modules.auth.dependencies import PermissionChecker

router = APIRouter(
    tags=["Work Schedules"],
    prefix="/work-schedules",
)


def get_schedule_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> WorkScheduleService:
    repository = WorkScheduleRepository(session)
    return WorkScheduleService(repository)


@router.post("/", response_model=WorkScheduleResponse, dependencies=[Depends(PermissionChecker("work_schedules:create"))])
async def create_schedule(
    schedule: WorkScheduleCreateRequest,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.create_schedule(schedule)


@router.get("/list", response_model=WorkScheduleListResponse, dependencies=[Depends(PermissionChecker("work_schedules:list"))])
async def list_schedules(
    request: WorkScheduleListRequest = Depends(),
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.list_schedules(request)


@router.get("/{schedule_id}", response_model=WorkScheduleResponse, dependencies=[Depends(PermissionChecker("work_schedules:get"))])
async def get_schedule(
    schedule_id: int,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.get_schedule(schedule_id)


@router.put("/{schedule_id}", response_model=WorkScheduleResponse, dependencies=[Depends(PermissionChecker("work_schedules:update"))])
async def update_schedule(
    schedule_id: int,
    schedule: WorkScheduleUpdateRequest,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.update_schedule(schedule_id, schedule)


@router.delete("/{schedule_id}", response_model=WorkScheduleResponse, dependencies=[Depends(PermissionChecker("work_schedules:delete"))])
async def delete_schedule(
    schedule_id: int,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.delete_schedule(schedule_id)


@router.get(
    "/{schedule_id}/employees", response_model=WorkScheduleEmployeesListResponse
, dependencies=[Depends(PermissionChecker("work_schedules:list_employees"))])
async def list_schedule_employees(
    schedule_id: int,
    request: WorkScheduleEmployeesListRequest = Depends(),
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.list_employees(schedule_id, request)


@router.post(
    "/{schedule_id}/employees", response_model=WorkScheduleEmployeesResult
, dependencies=[Depends(PermissionChecker("work_schedules:assign_employees"))])
async def assign_employees(
    schedule_id: int,
    payload: WorkScheduleEmployeesRequest,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.assign_employees(schedule_id, payload)


@router.delete(
    "/{schedule_id}/employees", response_model=WorkScheduleEmployeesResult
, dependencies=[Depends(PermissionChecker("work_schedules:remove_employees"))])
async def unassign_employees(
    schedule_id: int,
    payload: WorkScheduleEmployeesRequest,
    service: WorkScheduleService = Depends(get_schedule_service),
):
    return await service.unassign_employees(schedule_id, payload)
