import calendar
from datetime import date as date_type

from fastapi import HTTPException, status

from app.models.tabel_entries.model import TabelCode
from app.modules.tabel.repository import TabelRepository
from app.modules.tabel.schemas import (
    TabelCell,
    TabelEntryDeleteRequest,
    TabelEntryResult,
    TabelEntryUpsertRequest,
    TabelMonthRequest,
    TabelMonthResponse,
    TabelRow,
)


class TabelService:
    def __init__(self, repository: TabelRepository) -> None:
        self.repository = repository

    async def get_month(self, request: TabelMonthRequest) -> TabelMonthResponse:
        days_in_month = calendar.monthrange(request.year, request.month)[1]
        start = date_type(request.year, request.month, 1)
        end = date_type(request.year, request.month, days_in_month)

        working_days = sum(
            1
            for d in range(1, days_in_month + 1)
            if date_type(request.year, request.month, d).weekday() < 5
        )

        employees = await self.repository.get_employees(
            request.department, request.search
        )
        employee_ids = [e.id for e in employees]

        daily_rows = await self.repository.get_daily_for_month(
            employee_ids, start, end
        )
        # (employee_id, day) -> True if there is a worked day
        worked: dict[tuple[int, int], bool] = {}
        for d in daily_rows:
            is_worked = d.status is not None or d.total_working_hours > 0
            if is_worked:
                worked[(d.employee_id, d.date.day)] = True

        overrides = await self.repository.get_overrides_for_month(
            employee_ids, start, end
        )
        override_map: dict[tuple[int, int], TabelCode] = {
            (o.employee_id, o.date.day): o.code for o in overrides
        }

        rows: list[TabelRow] = []
        for emp in employees:
            cells: list[TabelCell] = []
            worked_days = 0
            for day in range(1, days_in_month + 1):
                key = (emp.id, day)
                override = override_map.get(key)
                if override is not None:
                    cells.append(
                        TabelCell(day=day, code=override, source="manual")
                    )
                    if override in (TabelCode.B, TabelCode.O):
                        worked_days += 1
                    continue

                weekday = date_type(request.year, request.month, day).weekday()
                if worked.get(key):
                    cells.append(
                        TabelCell(day=day, code=TabelCode.B, source="auto")
                    )
                    worked_days += 1
                elif weekday >= 5:
                    cells.append(
                        TabelCell(day=day, code=TabelCode.A, source="auto")
                    )
                else:
                    cells.append(TabelCell(day=day, code=None, source="auto"))

            rows.append(
                TabelRow(
                    employee_id=emp.id,
                    full_name=emp.full_name,
                    position=emp.position,
                    department=emp.department,
                    cells=cells,
                    worked_days=worked_days,
                )
            )

        return TabelMonthResponse(
            year=request.year,
            month=request.month,
            days_in_month=days_in_month,
            working_days=working_days,
            rows=rows,
        )

    async def upsert_entry(
        self, request: TabelEntryUpsertRequest
    ) -> TabelEntryResult:
        if not await self.repository.employee_exists(request.employee_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Xodim topilmadi",
            )
        await self.repository.upsert_entry(
            employee_id=request.employee_id,
            date=request.date,
            code=request.code,
            comment=request.comment,
        )
        return TabelEntryResult(ok=True)

    async def delete_entry(
        self, request: TabelEntryDeleteRequest
    ) -> TabelEntryResult:
        deleted = await self.repository.delete_entry(
            request.employee_id, request.date
        )
        return TabelEntryResult(ok=deleted)
