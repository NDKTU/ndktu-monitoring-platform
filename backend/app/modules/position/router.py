from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.position.repository import PositionRepository
from app.modules.position.service import PositionService
from app.modules.position.schemas import (
    PositionCreateRequest,
    PositionUpdateRequest,
    PositionListRequest,
    PositionListResponse,
    PositionResponse,
)

router = APIRouter(
    tags=["Positions"],
    prefix="/positions",
)


def get_position_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> PositionService:
    repository = PositionRepository(session)
    return PositionService(repository)


@router.post("/", response_model=PositionResponse)
async def create_position(
    position: PositionCreateRequest,
    service: PositionService = Depends(get_position_service),
):
    return await service.create_position(position)


@router.get("/list", response_model=PositionListResponse)
async def list_positions(
    request: PositionListRequest = Depends(),
    service: PositionService = Depends(get_position_service),
):
    return await service.list_positions(request)


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    service: PositionService = Depends(get_position_service),
):
    return await service.get_position(position_id)


@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: int,
    position: PositionUpdateRequest,
    service: PositionService = Depends(get_position_service),
):
    return await service.update_position(position_id, position)


@router.delete("/{position_id}", response_model=PositionResponse)
async def delete_position(
    position_id: int,
    service: PositionService = Depends(get_position_service),
):
    return await service.delete_position(position_id)
