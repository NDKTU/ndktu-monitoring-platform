import os
import json
import traceback
import asyncio
import httpx
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, or_
from app.core.db_helper import db_helper
from app.models.employees.model import Employee
from app.modules.attendance.status_service import apply_enter, apply_exit

logger = logging.getLogger(__name__)

# The terminals timestamp events with an offset (…+05:00) while every datetime
# column here is timestamp-without-time-zone, so an aware value cannot be compared
# with what is already stored. Normalise to local wall-clock time on the way in.
LOCAL_TZ = timezone(timedelta(hours=5))


def _to_local_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(LOCAL_TZ).replace(tzinfo=None)



# A terminal that has nothing to report still keeps its notification stream
# alive, so silence this long means the stream is dead even though the socket
# is not: the read times out, and the loop below reconnects. Generous enough to
# sit through a quiet night without churning.
STREAM_READ_TIMEOUT = 300.0
RECONNECT_DELAY = 5.0
MAX_RECONNECT_DELAY = 60.0
# Only say a camera is down once reconnecting has failed repeatedly; a single
# blip should not light up the UI.
FAILURES_BEFORE_INACTIVE = 3


async def _set_camera_active(camera_id: int, active: bool) -> None:
    """Persist whether a camera's stream is currently delivering."""
    from app.models.cameras.model import Cameras

    async for session in db_helper.session_getter():
        camera = await session.get(Cameras, camera_id)
        if camera and camera.is_active != active:
            camera.is_active = active
            await session.commit()
            logger.info(
                "Camera %s marked %s.", camera_id, "active" if active else "inactive"
            )
        break


async def probe_hikvision(
    device_ip: str, login: str, password: str, timeout: float = 3.0
) -> str | None:
    """Quick reachability/auth check against the Hikvision device.

    Uses /ISAPI/System/deviceInfo (a plain request) instead of the alertStream
    endpoint: DS-705 devices allow only ONE alertStream session, so probing it
    held the single slot and made the real stream connection fail with 404.
    deviceInfo does not consume the event-stream slot.

    Returns None on success or a user-facing error message (Uzbek) on failure.
    """
    url = f"http://{device_ip}/ISAPI/System/deviceInfo"
    auth = httpx.DigestAuth(login, password)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", url, auth=auth) as response:
                if response.status_code == 401:
                    return "Login yoki parol noto‘g‘ri"
                if response.status_code != 200:
                    return f"Qurilma HTTP {response.status_code} qaytardi"
        return None
    except httpx.ConnectError:
        return f"{device_ip} ga ulanib bo‘lmadi (tarmoqda mavjud emas)"
    except httpx.ReadError:
        return f"{device_ip} bilan aloqa uzildi"
    except (httpx.TimeoutException, asyncio.TimeoutError):
        return f"{device_ip} javob bermayapti (timeout)"
    except Exception as e:
        logger.error(f"Unexpected probe error for {device_ip}: {e}")
        return f"Kutilmagan xatolik: {e}"


class HikiVisionConnection:
    def __init__(self, camera_id: int, device_ip: str, login: str, password: str, direction: str):
        self.camera_id = camera_id
        self.device_ip = device_ip
        self.login = login
        self.password = password
        self.direction = direction
        self.url = f"http://{self.device_ip}/ISAPI/Event/notification/alertStream?format=json"
        self.boundary = b"--MIME_boundary"
        self.current_image_path: str | None = None

    async def connection_stream(self):
        """Connect to Hikvision device and yield each multipart 'part' as bytes."""
        auth = httpx.DigestAuth(self.login, self.password)

        # No total deadline — the stream is meant to stay open — but a read
        # deadline, so a terminal that goes quiet is noticed instead of leaving
        # the reader blocked on a socket that will never speak again.
        timeout = httpx.Timeout(None, connect=10.0, read=STREAM_READ_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", self.url, auth=auth) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to connect to {self.device_ip}: {response.status_code}")
                    raise httpx.ConnectError(
                        f"Camera {self.device_ip} returned HTTP {response.status_code}"
                    )

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

    async def publish_event(
        self,
        employee_no: str,
        dt_str: str,
        image_path: str | None = None,
        person_name: str = "",
    ):
        try:
            try:
                event_time = _to_local_naive(datetime.fromisoformat(dt_str))
            except Exception:
                event_time = datetime.now()

            keys = [k for k in (employee_no, person_name) if k]
            if not keys:
                return

            async for session in db_helper.session_getter():
                # An event identifies a person by the code they were enrolled under
                # (employeeNoString) or by their JSHIR (name); accept either.
                employee_stmt = select(Employee).where(
                    or_(
                        Employee.camera_code.in_(keys),
                        Employee.jshir.in_(keys),
                    )
                )
                employee_result = await session.execute(employee_stmt)
                employee = employee_result.scalars().first()

                if not employee:
                    logger.warning(
                        f"No employee matches camera_code/jshir in {keys!r}."
                    )
                    return

                if self.direction == "enter":
                    await apply_enter(session, employee, self.camera_id, event_time, image_path)
                    logger.info(
                        f"ENTER recorded: Employee {employee.jshir} at camera "
                        f"{self.camera_id} at {event_time}"
                    )
                elif self.direction == "exit":
                    await apply_exit(session, employee, self.camera_id, event_time, image_path)
                    logger.info(
                        f"EXIT recorded: Employee {employee.jshir} at camera "
                        f"{self.camera_id} at {event_time}"
                    )

                await session.commit()
                return
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
                    employee_no = (data.get("employeeNoString") or "").strip()
                    # The terminals put the JSHIR in `name`, usually padded with
                    # spaces. Either field identifies the person; both are passed on.
                    person_name = (data.get("name") or "").strip()

                    if employee_no or person_name:
                        logger.info(
                            f"Received Access Event: employeeNo={employee_no!r} "
                            f"name={person_name!r} at {dt}"
                        )
                        await self.publish_event(
                            employee_no, dt,
                            image_path=self.current_image_path,
                            person_name=person_name,
                        )
                        self.current_image_path = None
                    else:
                        # Door open/close records (minor 21/22) carry no identity at
                        # all — they are not attendance and are expected here.
                        logger.debug(f"Access event without identity: {json_data}")
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
        """Stay connected to the terminal for as long as the task lives.

        A dropped connection used to end the stream for good, and a connection
        that stayed open while the terminal went silent was never noticed at
        all — both left the platform quietly blind, with the turnstiles still
        recording everything the platform never saw. So every way out of the
        read loop other than cancellation leads back into it.
        """
        delay = RECONNECT_DELAY
        failures = 0
        try:
            while True:
                try:
                    logger.info("Attempting to connect to %s...", self.device_ip)
                    async for part in self.connection_stream():
                        if failures:
                            # Data is flowing again: clear the outage.
                            await _set_camera_active(self.camera_id, True)
                        failures = 0
                        delay = RECONNECT_DELAY
                        await self.process_part(part)
                    logger.warning(
                        "%s closed the notification stream. Reconnecting in %.0fs.",
                        self.device_ip,
                        delay,
                    )
                except asyncio.CancelledError:
                    raise
                except httpx.ReadTimeout:
                    logger.warning(
                        "No data from %s for %.0fs — treating the stream as dead. "
                        "Reconnecting in %.0fs.",
                        self.device_ip,
                        STREAM_READ_TIMEOUT,
                        delay,
                    )
                except (httpx.ConnectError, httpx.ReadError, httpx.HTTPError) as e:
                    logger.warning(
                        "Connection to %s failed: %s. Reconnecting in %.0fs.",
                        self.device_ip,
                        e,
                        delay,
                    )
                except Exception as e:
                    logger.error(
                        "Unhandled streaming error from %s: %s. Reconnecting in %.0fs.",
                        self.device_ip,
                        e,
                        delay,
                    )
                    logger.error(traceback.format_exc())

                failures += 1
                if failures == FAILURES_BEFORE_INACTIVE:
                    await _set_camera_active(self.camera_id, False)

                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RECONNECT_DELAY)
        except asyncio.CancelledError:
            logger.info("Stream task cancelled for %s. Disconnecting...", self.device_ip)
            raise
        finally:
            # Only ever retract this task's own registration: a restart cancels
            # the old task after the new one is already registered, and popping
            # blindly would leave the live stream untracked.
            if camera_manager.active_streams.get(self.camera_id) is asyncio.current_task():
                camera_manager.active_streams.pop(self.camera_id, None)


class CameraStreamManager:
    def __init__(self):
        self.active_streams: dict[int, asyncio.Task] = {}

    def start_stream(self, camera_id: int, device_ip: str, login: str, password: str, direction: str):
        if camera_id in self.active_streams:
            logger.info(f"Stream for camera {camera_id} is already running.")
            return

        connection = HikiVisionConnection(camera_id, device_ip, login, password, direction)
        task = asyncio.create_task(connection.stream_events())
        self.active_streams[camera_id] = task
        logger.info(f"Started background stream for camera {camera_id}")

    def stop_stream(self, camera_id: int):
        task = self.active_streams.pop(camera_id, None)
        if task:
            task.cancel()
            logger.info(f"Stopped background stream for camera {camera_id}")

    def restart_stream(self, camera_id: int, device_ip: str, login: str, password: str, direction: str):
        logger.info(f"Restarting stream for camera {camera_id}...")
        self.stop_stream(camera_id)
        self.start_stream(camera_id, device_ip, login, password, direction)

    async def start_active_cameras(self):
        """Fetch all active cameras from DB and start their streams."""
        from app.models.cameras.model import Cameras

        async for session in db_helper.session_getter():
            stmt = select(Cameras).where(Cameras.is_active == True)
            result = await session.execute(stmt)
            cameras = result.scalars().all()

            for camera in cameras:
                self.start_stream(
                    camera_id=camera.id,
                    device_ip=camera.device_ip,
                    login=camera.login,
                    password=camera.password,
                    direction=camera.direction.value,
                )
            break


camera_manager = CameraStreamManager()
