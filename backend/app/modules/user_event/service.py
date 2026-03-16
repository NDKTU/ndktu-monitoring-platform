from fastapi import HTTPException, status
from app.models.user_events.model import UserEvents
from app.modules.user_event.repository import UserEventRepository
from app.modules.user_event.schemas import (
    UserEventListRequest,
    UserEventListResponse
)


class UserEventService:
    def __init__(self, repository: UserEventRepository) -> None:
        self.repository = repository

    async def list_events(self, request: UserEventListRequest) -> UserEventListResponse:
        return await self.repository.list_events(request)

    async def get_event(self, event_id: int) -> UserEvents:
        event = await self.repository.get_event(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User event not found")
        return event
