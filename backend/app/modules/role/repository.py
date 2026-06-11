from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rbac.model import Role, Permission
from app.modules.role.schemas import RoleCreateRequest, RoleUpdateRequest, RoleListRequest, RolePermissionsRequest

class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_roles(self, request: RoleListRequest) -> list[Role]:
        query = select(Role).options(selectinload(Role.permissions)).where(Role.name != "admin")
        if request.search:
            query = query.where(Role.name.ilike(f"%{request.search}%"))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_role(self, role_id: int) -> Role | None:
        result = await self.session.execute(
            select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
        )
        return result.scalar()

    async def create_role(self, request: RoleCreateRequest) -> Role:
        role = Role(name=request.name)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def update_role(self, role_id: int, request: RoleUpdateRequest) -> Role | None:
        role = await self.get_role(role_id)
        if not role:
            return None
        role.name = request.name
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete_role(self, role_id: int) -> Role | None:
        role = await self.get_role(role_id)
        if not role:
            return None
        await self.session.delete(role)
        await self.session.commit()
        return role

    async def assign_permissions(self, role_id: int, request: RolePermissionsRequest) -> Role | None:
        role = await self.get_role(role_id)
        if not role:
            return None
        
        result = await self.session.execute(select(Permission).where(Permission.id.in_(request.permission_ids)))
        permissions = result.scalars().all()
        
        role.permissions = list(permissions)
        await self.session.commit()
        return role
