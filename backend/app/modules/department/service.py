from fastapi import HTTPException, status

from app.models.departments.model import Department
from app.modules.department.repository import DepartmentRepository
from app.modules.department.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentListRequest,
    DepartmentListResponse,
)


class DepartmentService:
    def __init__(self, repository: DepartmentRepository) -> None:
        self.repository = repository

    async def create_department(self, department: DepartmentCreateRequest) -> Department:
        existing = await self.repository.find_by_name(department.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bo'lim allaqachon mavjud",
            )
        return await self.repository.create_department(department)

    async def list_departments(self, request: DepartmentListRequest) -> DepartmentListResponse:
        return await self.repository.list_departments(request)

    async def get_department(self, department_id: int) -> Department:
        department = await self.repository.get_department(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bo'lim topilmadi",
            )
        return department

    async def update_department(
        self, department_id: int, department: DepartmentUpdateRequest
    ) -> Department:
        if department.name is not None:
            existing = await self.repository.find_by_name(department.name)
            if existing and existing.id != department_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Bo'lim allaqachon mavjud",
                )
        updated = await self.repository.update_department(department_id, department)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bo'lim topilmadi",
            )
        return updated

    async def delete_department(self, department_id: int) -> Department:
        deleted = await self.repository.delete_department(department_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bo'lim topilmadi",
            )
        return deleted
