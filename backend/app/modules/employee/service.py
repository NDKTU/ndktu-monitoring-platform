from fastapi import HTTPException, status

from app.models.employees.model import Employee
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeListRequest,
    EmployeeListResponse,
)


class EmployeeService:
    def __init__(self, repository: EmployeeRepository) -> None:
        self.repository = repository

    async def create_employee(self, employee: EmployeeCreateRequest) -> Employee:
        return await self.repository.create_employee(employee)

    async def list_employees(self, request: EmployeeListRequest) -> EmployeeListResponse:
        return await self.repository.list_employees(request)

    async def get_employee(self, employee_id: int) -> Employee:
        employee = await self.repository.get_employee(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        return employee

    async def update_employee(
        self, employee_id: int, employee: EmployeeUpdateRequest
    ) -> Employee:
        updated = await self.repository.update_employee(employee_id, employee)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        return updated

    async def delete_employee(self, employee_id: int) -> Employee:
        deleted = await self.repository.delete_employee(employee_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        return deleted
