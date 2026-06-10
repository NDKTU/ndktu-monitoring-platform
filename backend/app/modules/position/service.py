from fastapi import HTTPException, status

from app.models.positions.model import Position
from app.modules.position.repository import PositionRepository
from app.modules.position.schemas import (
    PositionCreateRequest,
    PositionUpdateRequest,
    PositionListRequest,
    PositionListResponse,
)


class PositionService:
    def __init__(self, repository: PositionRepository) -> None:
        self.repository = repository

    async def create_position(self, position: PositionCreateRequest) -> Position:
        existing = await self.repository.find_by_name(position.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lavozim allaqachon mavjud",
            )
        return await self.repository.create_position(position)

    async def list_positions(self, request: PositionListRequest) -> PositionListResponse:
        return await self.repository.list_positions(request)

    async def get_position(self, position_id: int) -> Position:
        position = await self.repository.get_position(position_id)
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lavozim topilmadi",
            )
        return position

    async def update_position(
        self, position_id: int, position: PositionUpdateRequest
    ) -> Position:
        existing = await self.repository.find_by_name(position.name)
        if existing and existing.id != position_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lavozim allaqachon mavjud",
            )
        updated = await self.repository.update_position(position_id, position)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lavozim topilmadi",
            )
        return updated

    async def delete_position(self, position_id: int) -> Position:
        deleted = await self.repository.delete_position(position_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lavozim topilmadi",
            )
        return deleted
