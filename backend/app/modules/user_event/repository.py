from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_events.model import UserEvents
from app.modules.user_event.schemas import (
    UserEventListRequest,
    UserEventListResponse,
    UserEventResponse
)


class UserEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_events(self, request: UserEventListRequest) -> UserEventListResponse:
        query = select(UserEvents)

        if request.user_id:
            query = query.where(UserEvents.user_id == request.user_id)
        if request.camera_id:
            query = query.where(UserEvents.camera_id == request.camera_id)
        if request.enter_time:
            query = query.where(UserEvents.enter_time >= request.enter_time)
        if request.exit_time:
            query = query.where(UserEvents.exit_time <= request.exit_time)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(request.offset).limit(request.limit)
        events_result = await self.session.execute(query)
        event_list = events_result.scalars().all()

        return UserEventListResponse(
            events=[UserEventResponse.model_validate(e) for e in event_list],
            total=total_count,
            page=request.page,
            limit=request.limit
        )

    async def get_event(self, event_id: int) -> UserEvents | None:
        return await self.session.get(UserEvents, event_id)
