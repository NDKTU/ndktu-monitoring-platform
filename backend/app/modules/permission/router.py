from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.permission.repository import PermissionRepository
from app.modules.permission.service import PermissionService
from app.modules.permission.schemas import PermissionResponse, PermissionListRequest
from app.modules.auth.dependencies import PermissionChecker

router = APIRouter(
    tags=["Permissions"],
    prefix="/permissions",
)

def get_permission_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> PermissionService:
    repository = PermissionRepository(session)
    return PermissionService(repository)

@router.get("/list", response_model=list[PermissionResponse], dependencies=[Depends(PermissionChecker("permissions:list"))])
async def list_permissions(
    request: PermissionListRequest = Depends(),
    service: PermissionService = Depends(get_permission_service)
):
    return await service.list_permissions(request)
