from fastapi import HTTPException, status

from app.models.cameras.model import Cameras
from app.modules.camera.repository import CameraRepository
from app.modules.camera.schemas import (
    CameraCreateRequest,
    CameraUpdateRequest,
    CameraListRequest,
    CameraListResponse,
)
from app.modules.camera.stream import camera_manager, probe_hikvision


class CameraService:
    def __init__(self, repository: CameraRepository) -> None:
        self.repository = repository

    async def create_camera(self, camera: CameraCreateRequest) -> Cameras:
        return await self.repository.create_camera(camera)

    async def list_cameras(self, camera_list_request: CameraListRequest) -> CameraListResponse:
        return await self.repository.list_cameras(camera_list_request)

    async def get_camera(self, camera_id: int) -> Cameras:
        camera = await self.repository.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        return camera

    async def update_camera(self, camera_id: int, camera: CameraUpdateRequest) -> Cameras:
        updated = await self.repository.update_camera(camera_id, camera)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        return updated

    async def delete_camera(self, camera_id: int) -> Cameras:
        deleted = await self.repository.delete_camera(camera_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        return deleted

    async def connect_camera(self, camera_id: int) -> Cameras:
        db_camera = await self.repository.get_camera(camera_id)
        if not db_camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

        # Already streaming → don't probe again. The device allows only one
        # event session, so a fresh probe could collide with the live stream.
        if camera_id in camera_manager.active_streams:
            return db_camera

        error = await probe_hikvision(
            db_camera.device_ip, db_camera.login, db_camera.password
        )
        if error is not None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "device_unreachable",
                    "message": error,
                    "device_ip": db_camera.device_ip,
                },
            )

        db_camera = await self.repository.connect_camera(camera_id)
        camera_manager.start_stream(
            camera_id=db_camera.id,
            device_ip=db_camera.device_ip,
            login=db_camera.login,
            password=db_camera.password,
            direction=db_camera.direction.value,
        )
        return db_camera

    async def disconnect_camera(self, camera_id: int) -> Cameras:
        db_camera = await self.repository.disconnect_camera(camera_id)
        if not db_camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

        camera_manager.stop_stream(camera_id=db_camera.id)
        return db_camera

    async def restart_camera(self, camera_id: int) -> Cameras:
        db_camera = await self.repository.restart_camera(camera_id)
        if not db_camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

        camera_manager.restart_stream(
            camera_id=db_camera.id,
            device_ip=db_camera.device_ip,
            login=db_camera.login,
            password=db_camera.password,
            direction=db_camera.direction.value,
        )
        return db_camera

    async def sync_employees(self, camera_id: int) -> dict:
        import asyncio
        import os
        import logging
        from app.modules.employee.repository import EmployeeRepository
        from app.modules.employee.hikvision_service import HikiUserService
        from app.core.config import settings

        db_camera = await self.repository.get_camera(camera_id)
        if not db_camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

        if not settings.hikvision.enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hikvision integration is disabled")

        hiki_service = HikiUserService(
            ip_address=db_camera.device_ip,
            username=db_camera.login,
            password=db_camera.password,
            enabled=True
        )

        is_reachable = await hiki_service.check_connection()
        if not is_reachable:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Camera {db_camera.device_ip} is unreachable"
            )

        employee_repo = EmployeeRepository(self.repository.session)
        employees = await employee_repo.get_all_active_employees()

        success_count = 0
        error_count = 0

        async def upload_employee(emp):
            nonlocal success_count, error_count
            user_name = f"{emp.first_name} {emp.last_name}"
            created = await hiki_service.create_user(user_id=emp.jshir, user_name=user_name)
            if created:
                success_count += 1
                # If there's a face image, we could upload it here.
                # Assuming the face image is in uploads/faces/{emp.jshir}_*.jpg
                # We can search for the first matching file:
                faces_dir = "uploads/faces"
                if os.path.exists(faces_dir):
                    matching_files = [f for f in os.listdir(faces_dir) if f.startswith(f"{emp.jshir}_")]
                    if matching_files:
                        img_path = os.path.join(faces_dir, matching_files[0])
                        await hiki_service.upload_face_image(user_id=emp.jshir, image_path=img_path)
            else:
                error_count += 1

        # Process in batches or concurrently. Let's do batches to not overwhelm the camera
        batch_size = 5
        for i in range(0, len(employees), batch_size):
            batch = employees[i:i+batch_size]
            await asyncio.gather(*(upload_employee(emp) for emp in batch))

        return {
            "success": True,
            "message": f"Sync complete. Successful: {success_count}, Failed: {error_count}"
        }
