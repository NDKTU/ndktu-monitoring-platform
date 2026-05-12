from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.service import EmployeeService
from app.modules.employee.schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeListRequest,
    EmployeeListResponse,
    EmployeeResponse,
)

router = APIRouter(
    tags=["Employees"],
    prefix="/employees",
)


def get_employee_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> EmployeeService:
    repository = EmployeeRepository(session)
    return EmployeeService(repository)


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreateRequest,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.create_employee(employee)


@router.get("/list", response_model=EmployeeListResponse)
async def list_employees(
    request: EmployeeListRequest = Depends(),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.list_employees(request)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.get_employee(employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee: EmployeeUpdateRequest,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.update_employee(employee_id, employee)


@router.delete("/{employee_id}", response_model=EmployeeResponse)
async def delete_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.delete_employee(employee_id)
