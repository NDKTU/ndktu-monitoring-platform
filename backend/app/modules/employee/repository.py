from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.employees.model import Employee
from app.models.departments.model import Department
from app.modules.employee.schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeListRequest,
    EmployeeListResponse,
    EmployeeResponse,
)


class EmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_employee(self, employee: EmployeeCreateRequest) -> Employee:
        db_employee = Employee(**employee.model_dump())
        self.session.add(db_employee)
        await self.session.commit()
        
        # Load relationships and return
        return await self.get_employee(db_employee.id)

    async def list_employees(self, request: EmployeeListRequest) -> EmployeeListResponse:
        query = select(Employee).options(
            joinedload(Employee.position),
            joinedload(Employee.department).joinedload(Department.work_schedule),
        )

        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.third_name.ilike(search_term),
                    Employee.jshir.ilike(search_term),
                )
            )

        if request.in_work is not None:
            query = query.where(Employee.in_work == request.in_work)
        if request.jshir:
            query = query.where(Employee.jshir == request.jshir)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(request.offset).limit(request.limit)
        result = await self.session.execute(query)
        employee_list = result.scalars().all()

        return EmployeeListResponse(
            employees=[EmployeeResponse.model_validate(e) for e in employee_list],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_employee(self, employee_id: int) -> Employee | None:
        result = await self.session.execute(
            select(Employee)
            .options(
                joinedload(Employee.position),
                joinedload(Employee.department).joinedload(Department.work_schedule),
            )
            .where(Employee.id == employee_id)
        )
        return result.scalar()

    async def update_employee(
        self, employee_id: int, employee: EmployeeUpdateRequest
    ) -> Employee | None:
        db_employee = await self.get_employee(employee_id)
        if not db_employee:
            return None

        update_data = employee.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_employee, key, value)

        await self.session.commit()
        await self.session.refresh(db_employee)
        return await self.get_employee(employee_id)

    async def delete_employee(self, employee_id: int) -> Employee | None:
        db_employee = await self.get_employee(employee_id)
        if not db_employee:
            return None
        await self.session.delete(db_employee)
        await self.session.commit()
        return db_employee

    async def get_employee_by_jshir(self, jshir: str) -> Employee | None:
        result = await self.session.execute(
            select(Employee)
            .options(
                joinedload(Employee.position),
                joinedload(Employee.department).joinedload(Department.work_schedule),
            )
            .where(Employee.jshir == jshir)
        )
        return result.scalar_one_or_none()

    async def get_all_active_employees(self) -> list[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.in_work == True)
        )
        return list(result.scalars().all())

