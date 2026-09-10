from datetime import date as date_type, timedelta

from fastapi import HTTPException, status

from app.models.daily_attendance.model import DailyAttendance
from app.models.tabel_entries.model import TabelCode, TabelEntry
from app.modules.daily_attendance.repository import DailyAttendanceRepository
from app.modules.daily_attendance.schemas import (
    DailyAttendanceListRequest,
    DailyAttendanceListResponse,
    DailyAttendanceResponse,
    SyntheticDayStatus,
)


class DailyAttendanceService:
    def __init__(self, repository: DailyAttendanceRepository) -> None:
        self.repository = repository

    async def list_items(
        self, request: DailyAttendanceListRequest
    ) -> DailyAttendanceListResponse:
        if request.fill_absent and request.employee_id:
            return await self._list_calendar(request)
        return await self.repository.list_items(request)

    async def _list_calendar(
        self, request: DailyAttendanceListRequest
    ) -> DailyAttendanceListResponse:
        """List one employee's days as a continuous calendar, newest first.

        Pagination walks calendar days rather than stored rows, so a day with no
        row is still a row in the answer — that is the whole point: the days the
        person did not turn up are exactly the ones that have nothing stored.
        """
        employee_id = request.employee_id
        assert employee_id is not None

        today = date_type.today()
        # Never invent days that have not happened yet.
        end = min(request.date_to or today, today)
        start = request.date_from or await self.repository.get_tracking_start(
            employee_id
        )

        if start is None or start > end:
            return DailyAttendanceListResponse(
                items=[], total=0, page=request.page, limit=request.limit
            )

        total = (end - start).days + 1

        page_end = end - timedelta(days=request.offset)
        if page_end < start:
            return DailyAttendanceListResponse(
                items=[], total=total, page=request.page, limit=request.limit
            )
        page_start = max(start, page_end - timedelta(days=request.limit - 1))

        rows = await self.repository.get_range(employee_id, page_start, page_end)
        by_date = {row.date: row for row in rows}

        overrides = await self.repository.get_tabel_overrides(
            employee_id, page_start, page_end
        )
        override_by_date = {entry.date: entry for entry in overrides}

        items: list[DailyAttendanceResponse] = []
        day = page_end
        while day >= page_start:
            row = by_date.get(day)
            override = override_by_date.get(day)
            if row is not None:
                item = DailyAttendanceResponse.model_validate(row)
                if override is not None:
                    item.tabel_code = override.code
                    item.tabel_comment = override.comment
                items.append(item)
            else:
                items.append(self._absent_day(employee_id, day, override))
            day -= timedelta(days=1)

        return DailyAttendanceListResponse(
            items=items, total=total, page=request.page, limit=request.limit
        )

    @staticmethod
    def _absent_day(
        employee_id: int, day: date_type, override: TabelEntry | None = None
    ) -> DailyAttendanceResponse:
        if override is not None:
            # An administrator has already accounted for this day by hand. Only
            # code F actually claims truancy; for leave, sick days or a holiday we
            # make no claim of our own and let the mark speak.
            status = (
                SyntheticDayStatus.ABSENT if override.code == TabelCode.F else None
            )
        elif day.weekday() >= 5:
            # Saturday and Sunday are the institution's days off — flagging them as
            # absences would bury the real ones under weekend noise. The tabel makes
            # the same assumption (weekend -> code A).
            status = SyntheticDayStatus.DAY_OFF
        else:
            status = SyntheticDayStatus.ABSENT

        return DailyAttendanceResponse(
            id=None,
            employee_id=employee_id,
            date=day,
            status=status,
            total_working_hours=0.0,
            first_enter_time=None,
            last_exit_time=None,
            has_no_enter=False,
            has_no_exit=False,
            tabel_code=override.code if override else None,
            tabel_comment=override.comment if override else None,
            employee=None,
        )

    async def get_item(self, item_id: int) -> DailyAttendance:
        item = await self.repository.get_item(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily attendance not found",
            )
        return item
