from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.positions.model import Position
from app.modules.position.schemas import (
    PositionCreateRequest,
    PositionUpdateRequest,
    PositionListRequest,
    PositionListResponse,
    PositionResponse,
)


class PositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_position(self, position: PositionCreateRequest) -> Position:
        db_position = Position(**position.model_dump())
        self.session.add(db_position)
        await self.session.commit()
        await self.session.refresh(db_position)
        return db_position

    async def find_by_name(self, name: str) -> Position | None:
        result = await self.session.execute(
            select(Position).where(Position.name == name)
        )
        return result.scalar_one_or_none()

    async def list_positions(self, request: PositionListRequest) -> PositionListResponse:
        query = select(Position)

        if request.search:
            search_term = f"%{request.search}%"
            query = query.where(Position.name.ilike(search_term))

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.order_by(Position.name).offset(request.offset).limit(request.limit)
        result = await self.session.execute(query)
        position_list = result.scalars().all()

        return PositionListResponse(
            positions=[PositionResponse.model_validate(p) for p in position_list],
            total=total_count,
            page=request.page,
            limit=request.limit,
        )

    async def get_position(self, position_id: int) -> Position | None:
        result = await self.session.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()

    async def update_position(
        self, position_id: int, position: PositionUpdateRequest
    ) -> Position | None:
        db_position = await self.get_position(position_id)
        if not db_position:
            return None

        update_data = position.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_position, key, value)

        await self.session.commit()
        await self.session.refresh(db_position)
        return db_position

    async def delete_position(self, position_id: int) -> Position | None:
        db_position = await self.get_position(position_id)
        if not db_position:
            return None
        await self.session.delete(db_position)
        await self.session.commit()
        return db_position
