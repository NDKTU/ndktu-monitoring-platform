from pydantic import BaseModel

class PermissionResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class PermissionListRequest(BaseModel):
    search: str | None = None
