from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.service import EmployeeService
from app.modules.employee.schemas import (
    EmployeeCreateRequest,
    EmployeeCreateResponse,
    EmployeeUpdateRequest,
    EmployeeListRequest,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUploadResponse,
    FaceUploadResponse,
)
from app.modules.auth.dependencies import PermissionChecker


router = APIRouter(
    tags=["Employees"],
    prefix="/employees",
)


def get_employee_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> EmployeeService:
    repository = EmployeeRepository(session)
    return EmployeeService(repository)


@router.post("/", response_model=EmployeeCreateResponse, dependencies=[Depends(PermissionChecker("employees:create"))])
async def create_employee(
    # Multipart rather than JSON: the face shot travels with the employee, and
    # a person the terminals cannot recognise is not worth creating.
    jshir: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    third_name: Annotated[str | None, Form()] = None,
    passport_series: Annotated[str | None, Form()] = None,
    in_work: Annotated[bool, Form()] = False,
    position_id: Annotated[int | None, Form()] = None,
    department_id: Annotated[int | None, Form()] = None,
    work_rate: Annotated[float, Form()] = 1.0,
    service: EmployeeService = Depends(get_employee_service),
):
    employee = EmployeeCreateRequest(
        jshir=jshir,
        first_name=first_name,
        last_name=last_name,
        third_name=third_name,
        passport_series=passport_series,
        in_work=in_work,
        position_id=position_id,
        department_id=department_id,
        work_rate=work_rate,
    )
    return await service.create_employee(employee, file)


@router.get("/list", response_model=EmployeeListResponse, dependencies=[Depends(PermissionChecker("employees:list"))])
async def list_employees(
    request: EmployeeListRequest = Depends(),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.list_employees(request)


@router.get("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(PermissionChecker("employees:get"))])
async def get_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.get_employee(employee_id)


@router.put("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(PermissionChecker("employees:update"))])
async def update_employee(
    employee_id: int,
    employee: EmployeeUpdateRequest,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.update_employee(employee_id, employee)


@router.delete("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(PermissionChecker("employees:delete"))])
async def delete_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.delete_employee(employee_id)


@router.post("/upload-excel", response_model=EmployeeUploadResponse, dependencies=[Depends(PermissionChecker("employees:upload_excel"))])
async def upload_employees_excel(
    file: UploadFile,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.upload_excel(file)


@router.post("/{employee_id}/face", response_model=FaceUploadResponse, dependencies=[Depends(PermissionChecker("employees:face"))])
async def upload_employee_face(
    employee_id: int,
    file: UploadFile,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.upload_face(employee_id, file)
