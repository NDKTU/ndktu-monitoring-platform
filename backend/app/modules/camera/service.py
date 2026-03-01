

class CameraService:
    def __init__(self, repository: CameraRepository) -> None:
        self.repository = repository

    async def create_camera(self, camera: CameraCreate) -> Camera:
        return await self.repository.create_camera(camera)

    async def list_cameras(self, camera_list_request: CameraListRequest) -> CameraListResponse:
        return await self.repository.list_cameras(camera_list_request)

    async def get_camera(self, camera_id: int) -> Camera | None:
        return await self.repository.get_camera(camera_id)

    async def update_camera(self, camera_id: int, camera: CameraUpdate) -> Camera | None:
        return await self.repository.update_camera(camera_id, camera)

    async def delete_camera(self, camera_id: int) -> Camera | None:
        return await self.repository.delete_camera(camera_id)

    async def connect_camera(self, camera_id: int) -> Camera | None:
        return await self.repository.connect_camera(camera_id)

    async def disconnect_camera(self, camera_id: int) -> Camera | None:
        return await self.repository.disconnect_camera(camera_id)

    async def restart_camera(self, camera_id: int) -> Camera | None:
        return await self.repository.restart_camera(camera_id)