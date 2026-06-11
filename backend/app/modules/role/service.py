from fastapi import HTTPException, status
from app.modules.role.repository import RoleRepository
from app.modules.role.schemas import RoleCreateRequest, RoleUpdateRequest, RoleListRequest, RolePermissionsRequest
from app.models.rbac.model import Role

class RoleService:
    def __init__(self, repository: RoleRepository) -> None:
        self.repository = repository

    async def list_roles(self, request: RoleListRequest) -> list[Role]:
        return await self.repository.list_roles(request)

    async def get_role(self, role_id: int) -> Role:
        role = await self.repository.get_role(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def create_role(self, request: RoleCreateRequest) -> Role:
        return await self.repository.create_role(request)

    async def update_role(self, role_id: int, request: RoleUpdateRequest) -> Role:
        role = await self.repository.update_role(role_id, request)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def delete_role(self, role_id: int) -> Role:
        role = await self.repository.delete_role(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def assign_permissions(self, role_id: int, request: RolePermissionsRequest) -> Role:
        role = await self.repository.assign_permissions(role_id, request)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role
