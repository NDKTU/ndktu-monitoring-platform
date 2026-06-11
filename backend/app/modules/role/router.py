from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.role.repository import RoleRepository
from app.modules.role.service import RoleService
from app.modules.role.schemas import RoleResponse, RoleCreateRequest, RoleUpdateRequest, RoleListRequest, RolePermissionsRequest
from app.modules.auth.dependencies import PermissionChecker

router = APIRouter(
    tags=["Roles"],
    prefix="/roles",
)

def get_role_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> RoleService:
    repository = RoleRepository(session)
    return RoleService(repository)

@router.get("/list", response_model=list[RoleResponse], dependencies=[Depends(PermissionChecker("roles:list"))])
async def list_roles(
    request: RoleListRequest = Depends(),
    service: RoleService = Depends(get_role_service)
):
    return await service.list_roles(request)

@router.get("/{role_id}", response_model=RoleResponse, dependencies=[Depends(PermissionChecker("roles:get"))])
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    return await service.get_role(role_id)

@router.post("/", response_model=RoleResponse, dependencies=[Depends(PermissionChecker("roles:create"))])
async def create_role(
    request: RoleCreateRequest,
    service: RoleService = Depends(get_role_service)
):
    return await service.create_role(request)

@router.put("/{role_id}", response_model=RoleResponse, dependencies=[Depends(PermissionChecker("roles:update"))])
async def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    service: RoleService = Depends(get_role_service)
):
    return await service.update_role(role_id, request)

@router.delete("/{role_id}", response_model=RoleResponse, dependencies=[Depends(PermissionChecker("roles:delete"))])
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    return await service.delete_role(role_id)

@router.post("/{role_id}/permissions", response_model=RoleResponse, dependencies=[Depends(PermissionChecker("roles:assign_permissions"))])
async def assign_permissions(
    role_id: int,
    request: RolePermissionsRequest,
    service: RoleService = Depends(get_role_service)
):
    return await service.assign_permissions(role_id, request)
