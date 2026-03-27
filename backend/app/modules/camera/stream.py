import os
import json
import traceback
import asyncio
import httpx
import logging
from datetime import datetime

from sqlalchemy import select
from app.core.db_helper import db_helper
from app.models.users.model import User
from app.models.user_events.model import UserEvents

logger = logging.getLogger(__name__)

class HikiVisionConnection:
    def __init__(self, camera_id: int, device_ip: str, username: str, password: str, direction: str):
        self.camera_id = camera_id
        self.device_ip = device_ip
        self.username = username
        self.password = password
        self.direction = direction
        self.url = f"http://{self.device_ip}/ISAPI/Event/notification/alertStream?format=json"
        self.boundary = b"--MIME_boundary"
        self.current_image_path: str | None = None

    async def connection_stream(self):
        """Connect to Hikvision device and yield each multipart 'part' as bytes."""
        auth = httpx.DigestAuth(self.username, self.password)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", self.url, auth=auth) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to connect to {self.device_ip}: {response.status_code}")
                    return

                logger.info(f"Connected to {self.device_ip}. Waiting for events...")

                buffer = b""
                async for chunk in response.aiter_bytes():
                    buffer += chunk
                    while True:
                        boundary_index = buffer.find(self.boundary)
                        if boundary_index == -1:
                            break

                        part = buffer[:boundary_index]
                        buffer = buffer[boundary_index + len(self.boundary):]
                        part = part.lstrip(b"\r\n")

                        if part.strip():
                            yield part

    async def publish_event(self, employee_no: str, dt_str: str, image_path: str | None = None):
        try:
            # Parse datetime or fallback
            try:
                # Hikvision format might need tweaking depending on exact output
                event_time = datetime.fromisoformat(dt_str)
            except Exception:
                event_time = datetime.utcnow()

            async for session in db_helper.session_getter():
                user_stmt = select(User).where(User.username == employee_no)
                user_result = await session.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.warning(f"User with username '{employee_no}' not found in DB.")
                    return
                
                if self.direction == "enter":
                    user.in_work = True
                    new_event = UserEvents(
                        user_id=user.id,
                        camera_id=self.camera_id,
                        enter_time=event_time,
                        enter_image_path=image_path
                    )
                    session.add(new_event)
                    logger.info(f"Saved ENTER Event: User {user.username} at camera {self.camera_id} at {event_time} with image {image_path}")

                elif self.direction == "exit":
                    user.in_work = False
                    
                    # Find the most recent open event for this user
                    event_stmt = (
                        select(UserEvents)
                        .where(UserEvents.user_id == user.id, UserEvents.exit_time.is_(None))
                        .order_by(UserEvents.enter_time.desc())
                        .limit(1)
                    )
                    event_result = await session.execute(event_stmt)
                    open_event = event_result.scalar_one_or_none()
                    
                    if open_event:
                        open_event.exit_time = event_time
                        open_event.exit_image_path = image_path
                        logger.info(f"Updated EXIT Event: User {user.username} at camera {self.camera_id} at {event_time} with image {image_path}")
                    else:
                        # Fallback if there was no enter event found
                        new_event = UserEvents(
                            user_id=user.id,
                            camera_id=self.camera_id,
                            enter_time=event_time,  # Fallback
                            exit_time=event_time,
                            exit_image_path=image_path
                        )
                        session.add(new_event)
                        logger.warning(f"Saved EXIT Event (No prior enter): User {user.username} at {event_time} with image {image_path}")

                await session.commit()
                return # We only need one session execution
        except Exception as e:
            logger.error(f"Failed to save event to DB: {e}")
            logger.error(traceback.format_exc())

    def save_image(self, image_bytes: bytes, direction: str) -> str:
        """Save image to uploads/{direction} directory with timestamp."""
        directory = f"uploads/{direction}"
        os.makedirs(directory, exist_ok=True)
        filename = f"{directory}/{datetime.now():%Y%m%d_%H%M%S_%f}.jpg"
        
        with open(filename, "wb") as f:
            f.write(image_bytes)

        logger.info(f"[📷] Image saved to {direction}: {filename}")
        return filename

    async def process_part(self, part: bytes):
        """Process one part of the multipart stream."""
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            return

        headers_raw = part[:header_end].decode(errors="ignore")
        content = part[header_end + 4:]

        if "application/json" in headers_raw:
            try:
                json_data = json.loads(content.decode(errors="ignore"))
                event_type = json_data.get("eventType")
                dt = json_data.get("dateTime")

                if event_type == "AccessControllerEvent":
                    data = json_data.get("AccessControllerEvent", {})
                    employee_no = data.get("employeeNoString")
                    
                    if employee_no:
                        logger.info(f"Received Access Event: Employee {employee_no} at {dt}")
                        await self.publish_event(employee_no, dt, image_path=self.current_image_path)
                        # Reset image path after associating it with the event
                        self.current_image_path = None
                    else:
                        logger.warning(f"Access event received but missing employeeNoString: {json_data}")
                else:
                    logger.debug(f"Received non-access event type '{event_type}': {json_data}")

            except Exception as e:
                logger.error(f"Failed to parse JSON stream: {e}")
                logger.info(f"Raw content that failed to parse: {content}")
        elif "image/jpeg" in headers_raw:
            self.current_image_path = self.save_image(content, self.direction)
        else:
            logger.warning("Unknown content type in part")


    async def stream_events(self):
        """Main loop: read parts from the stream and process them. Stops if connection fails."""
        try:
            logger.info(f"Attempting to connect to {self.device_ip}...")
            async for part in self.connection_stream():
                await self.process_part(part)
        except asyncio.CancelledError:
            logger.info(f"Stream task cancelled for {self.device_ip}. Disconnecting...")
        except (httpx.ConnectError, httpx.ReadError) as e:
            logger.error(f"Connection to {self.device_ip} failed: {e}. Stopping stream.")
        except Exception as e:
            logger.error(f"Unhandled streaming error from {self.device_ip}: {e}. Stopping stream.")
            logger.error(traceback.format_exc())


class CameraStreamManager:
    def __init__(self):
        self.active_streams: dict[int, asyncio.Task] = {}

    def start_stream(self, camera_id: int, device_ip: str, username: str, password: str, direction: str):
        if camera_id in self.active_streams:
            logger.info(f"Stream for camera {camera_id} is already running.")
            return

        connection = HikiVisionConnection(camera_id, device_ip, username, password, direction)
        task = asyncio.create_task(connection.stream_events())
        self.active_streams[camera_id] = task
        logger.info(f"Started background stream for camera {camera_id}")

    def stop_stream(self, camera_id: int):
        task = self.active_streams.pop(camera_id, None)
        if task:
            task.cancel()
            logger.info(f"Stopped background stream for camera {camera_id}")

    def restart_stream(self, camera_id: int, device_ip: str, username: str, password: str, direction: str):
        logger.info(f"Restarting stream for camera {camera_id}...")
        self.stop_stream(camera_id)
        self.start_stream(camera_id, device_ip, username, password, direction)

    async def start_active_cameras(self):
        """Fetch all active cameras from DB and start their streams."""
        from app.modules.camera.repository import CameraRepository
        from app.models.cameras.model import Cameras
        
        async for session in db_helper.session_getter():
            repo = CameraRepository(session)
            stmt = select(Cameras).where(Cameras.is_active == True)
            result = await session.execute(stmt)
            cameras = result.scalars().all()
            
            for camera in cameras:
                self.start_stream(
                    camera_id=camera.id,
                    device_ip=camera.device_ip,
                    username=camera.username,
                    password=camera.password,
                    direction=camera.direction.value
                )
            break

camera_manager = CameraStreamManager()
