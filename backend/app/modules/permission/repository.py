from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac.model import Permission
from app.modules.permission.schemas import PermissionListRequest

class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_permissions(self, request: PermissionListRequest) -> list[Permission]:
        query = select(Permission)
        if request.search:
            query = query.where(Permission.name.ilike(f"%{request.search}%"))
        result = await self.session.execute(query)
        return result.scalars().all()
