from pydantic import BaseModel
from app.modules.permission.schemas import PermissionResponse

class RoleCreateRequest(BaseModel):
    name: str

class RoleUpdateRequest(BaseModel):
    name: str

class RoleResponse(BaseModel):
    id: int
    name: str
    permissions: list[PermissionResponse] = []
    
    class Config:
        from_attributes = True

class RoleListRequest(BaseModel):
    search: str | None = None

class RolePermissionsRequest(BaseModel):
    permission_ids: list[int]
