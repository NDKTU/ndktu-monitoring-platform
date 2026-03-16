from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.user_event.repository import UserEventRepository
from app.modules.user_event.service import UserEventService
from app.modules.user_event.schemas import (
    UserEventListRequest,
    UserEventListResponse,
    UserEventResponse
)

router = APIRouter(
    tags=["User Events"],
    prefix="/user-events",
)

def get_user_event_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> UserEventService:
    repository = UserEventRepository(session)
    return UserEventService(repository)


@router.post("/list", response_model=UserEventListResponse)
async def list_events(
    request: UserEventListRequest,
    service: UserEventService = Depends(get_user_event_service)
):
    return await service.list_events(request)


@router.get("/{event_id}", response_model=UserEventResponse)
async def get_event(
    event_id: int,
    service: UserEventService = Depends(get_user_event_service)
):
    return await service.get_event(event_id)
