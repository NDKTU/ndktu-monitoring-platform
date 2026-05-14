from datetime import date as date_type

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_attendance.model import DailyAttendance
from app.models.employees.model import Employee
from app.models.tabel_entries.model import TabelCode, TabelEntry


class TabelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_employees(
        self, department: str | None, search: str | None
    ) -> list[Employee]:
        query = select(Employee)
        if department:
            query = query.where(Employee.department.ilike(f"%{department}%"))
        if search:
            term = f"%{search}%"
            query = query.where(
                or_(
                    Employee.first_name.ilike(term),
                    Employee.last_name.ilike(term),
                    Employee.third_name.ilike(term),
                    Employee.jshir.ilike(term),
                )
            )
        query = query.order_by(Employee.last_name, Employee.first_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_daily_for_month(
        self, employee_ids: list[int], start: date_type, end: date_type
    ) -> list[DailyAttendance]:
        if not employee_ids:
            return []
        result = await self.session.execute(
            select(DailyAttendance).where(
                DailyAttendance.employee_id.in_(employee_ids),
                DailyAttendance.date >= start,
                DailyAttendance.date <= end,
            )
        )
        return list(result.scalars().all())

    async def get_overrides_for_month(
        self, employee_ids: list[int], start: date_type, end: date_type
    ) -> list[TabelEntry]:
        if not employee_ids:
            return []
        result = await self.session.execute(
            select(TabelEntry).where(
                TabelEntry.employee_id.in_(employee_ids),
                TabelEntry.date >= start,
                TabelEntry.date <= end,
            )
        )
        return list(result.scalars().all())

    async def get_entry(
        self, employee_id: int, date: date_type
    ) -> TabelEntry | None:
        result = await self.session.execute(
            select(TabelEntry).where(
                TabelEntry.employee_id == employee_id,
                TabelEntry.date == date,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_entry(
        self,
        employee_id: int,
        date: date_type,
        code: TabelCode,
        comment: str | None,
    ) -> TabelEntry:
        entry = await self.get_entry(employee_id, date)
        if entry is None:
            entry = TabelEntry(
                employee_id=employee_id,
                date=date,
                code=code,
                comment=comment,
            )
            self.session.add(entry)
        else:
            entry.code = code
            entry.comment = comment
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def delete_entry(self, employee_id: int, date: date_type) -> bool:
        entry = await self.get_entry(employee_id, date)
        if entry is None:
            return False
        await self.session.delete(entry)
        await self.session.commit()
        return True

    async def employee_exists(self, employee_id: int) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(Employee)
            .where(Employee.id == employee_id)
        )
        return (result.scalar() or 0) > 0
