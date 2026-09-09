from fastapi import HTTPException, status
from app.modules.role.repository import RoleRepository, ADMIN_ROLE_NAME
from app.modules.role.schemas import RoleCreateRequest, RoleUpdateRequest, RoleListRequest, RolePermissionsRequest
from app.models.rbac.model import Role

class RoleService:
    def __init__(self, repository: RoleRepository) -> None:
        self.repository = repository

    async def _reject_admin(self, role_id: int) -> None:
        """The admin role is already filtered out of list_roles; addressing it by id
        must behave the same way. Deleting it would strip the only account that can
        administer the system (users.role_id is ON DELETE SET NULL) until the next
        restart, and editing its permissions would silently lock features away."""
        role = await self.repository.get_role(role_id)
        if role is not None and role.name == ADMIN_ROLE_NAME:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

    async def list_roles(self, request: RoleListRequest) -> list[Role]:
        return await self.repository.list_roles(request)

    async def get_role(self, role_id: int) -> Role:
        await self._reject_admin(role_id)
        role = await self.repository.get_role(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def create_role(self, request: RoleCreateRequest) -> Role:
        return await self.repository.create_role(request)

    async def update_role(self, role_id: int, request: RoleUpdateRequest) -> Role:
        await self._reject_admin(role_id)
        role = await self.repository.update_role(role_id, request)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def delete_role(self, role_id: int) -> Role:
        await self._reject_admin(role_id)
        role = await self.repository.delete_role(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role

    async def assign_permissions(self, role_id: int, request: RolePermissionsRequest) -> Role:
        await self._reject_admin(role_id)
        role = await self.repository.assign_permissions(role_id, request)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return role
