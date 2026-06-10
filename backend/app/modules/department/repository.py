from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.departments.model import Department
from app.modules.department.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentListRequest,
    DepartmentListResponse,
    DepartmentResponse,
)


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_department(self, department: DepartmentCreateRequest) -> Department:
        db_department = Department(**department.model_dump())
        self.session.add(db_department)
        await self.session.commit()
        
        # Reload with joined work_schedule relationship
        stmt = (
            select(Department)
            .options(joinedload(Department.work_schedule))
            .where(Department.id == db_department.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_by_name(self, name: str) -> Department | None:
        result = await self.session.execute(
            select(Department)
            .options(joinedload(Department.work_schedule))
            .where(Department.name == name)
        )
        return result.scalar_one_or_none()

    async def list_departments(self, request: DepartmentListRequest) -> DepartmentListResponse:
        query = select(Department).options(joinedload(Department.work_schedule))

        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(Department.name.ilike(search_term))

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.order_by(Department.name).offset(request.offset).limit(request.limit)
        result = await self.session.execute(query)
        department_list = result.scalars().all()

        return DepartmentListResponse(
            departments=[DepartmentResponse.model_validate(d) for d in department_list],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_department(self, department_id: int) -> Department | None:
        result = await self.session.execute(
            select(Department)
            .options(joinedload(Department.work_schedule))
            .where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def update_department(
        self, department_id: int, department: DepartmentUpdateRequest
    ) -> Department | None:
        db_department = await self.get_department(department_id)
        if not db_department:
            return None

        update_data = department.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_department, key, value)

        await self.session.commit()
        
        # Reload to ensure relationships are up to date
        return await self.get_department(department_id)

    async def delete_department(self, department_id: int) -> Department | None:
        db_department = await self.get_department(department_id)
        if not db_department:
            return None
        await self.session.delete(db_department)
        await self.session.commit()
        return db_department
