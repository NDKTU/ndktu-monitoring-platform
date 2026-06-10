from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.department.repository import DepartmentRepository
from app.modules.department.service import DepartmentService
from app.modules.department.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentListRequest,
    DepartmentListResponse,
    DepartmentResponse,
)

router = APIRouter(
    tags=["Departments"],
    prefix="/departments",
)


def get_department_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> DepartmentService:
    repository = DepartmentRepository(session)
    return DepartmentService(repository)


@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department: DepartmentCreateRequest,
    service: DepartmentService = Depends(get_department_service),
):
    return await service.create_department(department)


@router.get("/list", response_model=DepartmentListResponse)
async def list_departments(
    request: DepartmentListRequest = Depends(),
    service: DepartmentService = Depends(get_department_service),
):
    return await service.list_departments(request)


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    service: DepartmentService = Depends(get_department_service),
):
    return await service.get_department(department_id)


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department: DepartmentUpdateRequest,
    service: DepartmentService = Depends(get_department_service),
):
    return await service.update_department(department_id, department)


@router.delete("/{department_id}", response_model=DepartmentResponse)
async def delete_department(
    department_id: int,
    service: DepartmentService = Depends(get_department_service),
):
    return await service.delete_department(department_id)
