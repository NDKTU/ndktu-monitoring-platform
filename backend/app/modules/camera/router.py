from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.camera.repository import CameraRepository
from app.modules.camera.service import CameraService
from app.modules.camera.schemas import (
    CameraCreateRequest,
    CameraUpdateRequest,
    CameraListRequest,
    CameraListResponse,
    CameraResponse
)


router = APIRouter(
    tags=["Cameras"],
    prefix="/cameras",
)

def get_camera_service(
    session: AsyncSession = Depends(db_helper.session_getter)
) -> CameraService:
    repository = CameraRepository(session)
    return CameraService(repository)


@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera: CameraCreateRequest,
    service: CameraService = Depends(get_camera_service)
):
    return await service.create_camera(camera)


@router.post("/list", response_model=CameraListResponse)
async def list_cameras(
    request: CameraListRequest,
    service: CameraService = Depends(get_camera_service)
):
    return await service.list_cameras(request)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service)
):
    camera = await service.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera: CameraUpdateRequest,
    service: CameraService = Depends(get_camera_service)
):
    updated = await service.update_camera(camera_id, camera)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return updated


@router.delete("/{camera_id}", response_model=CameraResponse)
async def delete_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service)
):
    deleted = await service.delete_camera(camera_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return deleted


@router.post("/{camera_id}/connect", response_model=CameraResponse)
async def connect_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service)
):
    connected = await service.connect_camera(camera_id)
    if not connected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return connected


@router.post("/{camera_id}/disconnect", response_model=CameraResponse)
async def disconnect_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service)
):
    disconnected = await service.disconnect_camera(camera_id)
    if not disconnected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return disconnected


@router.post("/{camera_id}/restart", response_model=CameraResponse)
async def restart_camera(
    camera_id: int,
    service: CameraService = Depends(get_camera_service)
):
    restarted = await service.restart_camera(camera_id)
    if not restarted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return restarted