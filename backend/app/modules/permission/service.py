from app.modules.permission.repository import PermissionRepository
from app.modules.permission.schemas import PermissionListRequest
from app.models.rbac.model import Permission

class PermissionService:
    def __init__(self, repository: PermissionRepository) -> None:
        self.repository = repository

    async def list_permissions(self, request: PermissionListRequest) -> list[Permission]:
        return await self.repository.list_permissions(request)
