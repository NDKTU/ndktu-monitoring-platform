from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cameras.model import Cameras
from app.modules.camera.schemas import (
    CameraCreateRequest,
    CameraUpdateRequest,
    CameraListRequest,
    CameraListResponse,
    CameraResponse
)
from app.modules.camera.stream import camera_manager


class CameraRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_camera(self, camera: CameraCreateRequest) -> Cameras:
        db_camera = Cameras(**camera.model_dump())
        self.session.add(db_camera)
        await self.session.commit()
        await self.session.refresh(db_camera)
        return db_camera

    async def list_cameras(self, camera_list_request: CameraListRequest) -> CameraListResponse:
        query = select(Cameras)

        if camera_list_request.search:
            search_term = f"%{camera_list_request.search}%"
            query = query.where(
                or_(
                    Cameras.device_ip.ilike(search_term),
                    Cameras.username.ilike(search_term)
                )
            )

        if camera_list_request.device_ip:
            query = query.where(Cameras.device_ip == camera_list_request.device_ip)
        if camera_list_request.username:
            query = query.where(Cameras.username == camera_list_request.username)
        if camera_list_request.direction:
            query = query.where(Cameras.direction == camera_list_request.direction)
        if camera_list_request.is_active is not None:
            query = query.where(Cameras.is_active == camera_list_request.is_active)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_stmt)
        total_count = total.scalar() or 0

        query = query.offset(camera_list_request.offset).limit(camera_list_request.limit)
        cameras_result = await self.session.execute(query)
        camera_list = cameras_result.scalars().all()

        return CameraListResponse(
            cameras=[CameraResponse.model_validate(c) for c in camera_list],
            total=total_count,
            page=camera_list_request.page,
            limit=camera_list_request.limit
        )

    async def get_camera(self, camera_id: int) -> Cameras | None:
        return await self.session.execute(select(Cameras).where(Cameras.id == camera_id)).scalar()

    async def update_camera(self, camera_id: int, camera: CameraUpdateRequest) -> Cameras | None:
        db_camera = await self.get_camera(camera_id)
        if not db_camera:
            return None
        
        update_data = camera.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_camera, key, value)
            
        await self.session.commit()
        await self.session.refresh(db_camera)
        return db_camera

    async def delete_camera(self, camera_id: int) -> Cameras | None:
        db_camera = await self.get_camera(camera_id)
        if not db_camera:
            return None
        await self.session.delete(db_camera)
        await self.session.commit()
        return db_camera

    async def connect_camera(self, camera_id: int) -> Cameras | None:
        db_camera = await self.get_camera(camera_id)
        if not db_camera:
            return None
        db_camera.is_active = True
        await self.session.commit()
        await self.session.refresh(db_camera)
        
        # Start the background stream
        camera_manager.start_stream(
            camera_id=db_camera.id,
            device_ip=db_camera.device_ip,
            username=db_camera.username,
            password=db_camera.password,
            direction=db_camera.direction.value
        )
        
        return db_camera

    async def disconnect_camera(self, camera_id: int) -> Cameras | None:
        db_camera = await self.get_camera(camera_id)
        if not db_camera:
            return None
        db_camera.is_active = False
        await self.session.commit()
        await self.session.refresh(db_camera)
        
        # Stop background stream
        camera_manager.stop_stream(camera_id=db_camera.id)
        
        return db_camera

    async def restart_camera(self, camera_id: int) -> Cameras | None:
        db_camera = await self.get_camera(camera_id)
        if not db_camera:
            return None
            
        # Ensure it's marked as active if restarted
        if not db_camera.is_active:
            db_camera.is_active = True
            await self.session.commit()
            await self.session.refresh(db_camera)
        
        # Restart background stream
        camera_manager.restart_stream(
            camera_id=db_camera.id,
            device_ip=db_camera.device_ip,
            username=db_camera.username,
            password=db_camera.password,
            direction=db_camera.direction.value
        )
        
        return db_camera