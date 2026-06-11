import httpx
import json
import os
import logging

logger = logging.getLogger(__name__)


class HikiUserService:
    def __init__(self, ip_address: str, username: str, password: str, enabled: bool = True):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.enabled = enabled

        # Base URLs
        self.user_record_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Record?format=json"
        self.user_modify_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Modify?format=json"
        self.user_delete_url = f"http://{self.ip_address}/ISAPI/AccessControl/UserInfo/Delete?format=json"
        self.face_data_url = f"http://{self.ip_address}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
        self.card_search_url = f"http://{self.ip_address}/ISAPI/AccessControl/CardInfo/Search?format=json"

        # Always use digest auth
        self.auth = httpx.DigestAuth(self.username, self.password)

    async def check_connection(self) -> bool:
        """Ping device to check if it's active and reachable."""
        if not self.enabled:
            return False
            
        url = f"http://{self.ip_address}/ISAPI/System/deviceInfo?format=json"
        async with httpx.AsyncClient(auth=self.auth, timeout=5.0) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"❌ Camera {self.ip_address} connection check failed: {e}")
                return False

    async def create_user(self, user_id: str, user_name: str, device_ids: list[int] = None) -> bool:
        if not self.enabled:
            logger.info(f"[Hikvision] Disabled. Skipping create_user for {user_name}")
            return True
            
        if device_ids is None:
            device_ids = [1]
            
        payload = {
            "UserInfo": {
                "employeeNo": str(user_id),
                "name": user_name,
                "userType": "normal",
                "gender": "unknown",
                "enable": True,
                "Valid": {
                    "enable": True,
                    "beginTime": "2020-01-01T00:00:00",
                    "endTime": "2037-12-31T23:59:59"
                }
            },
            "AccessRight": {
                "deviceIDs": device_ids
            }
        }

        logger.info(f"Attempting to create user record for '{user_name}' on Hikvision...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.post(
                    self.user_record_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                logger.info("✅ User record created successfully on Hikvision.")
                return True
            except httpx.HTTPStatusError as err:
                logger.error(f"❌ Failed to create user record on Hikvision. {err}")
                logger.error(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                logger.error(f"❌ Request error to Hikvision: {err}")
        return False

    async def upload_face_image(self, user_id: str, image_path: str) -> bool:
        """Upload face image for a user."""
        if not self.enabled:
            logger.info(f"[Hikvision] Disabled. Skipping upload_face_image for {user_id}")
            return True
            
        if not os.path.exists(image_path):
            logger.error(f"❌ Error: Image not found at '{image_path}'")
            return False

        logger.info(f"Attempting to upload face image for user ID '{user_id}' to Hikvision...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                with open(image_path, "rb") as f:
                    files = {
                        "FaceDataRecord": (
                            None,
                            json.dumps({
                                "faceLibType": "blackFD",  # or "whiteFD"
                                "FDID": "1",
                                "FPID": str(user_id)
                            }),
                            "application/json"
                        ),
                        "FaceImage": (os.path.basename(image_path), f, "image/jpeg")
                    }

                    response = await client.post(self.face_data_url, files=files, timeout=20)
                    response.raise_for_status()
                    logger.info("✅ Face image uploaded successfully to Hikvision.")
                    return True
            except httpx.HTTPStatusError as err:
                logger.error(f"❌ Failed to upload face image to Hikvision. {err}")
                logger.error(f"Response: {err.response.text}")
            except Exception as e:
                logger.error(f"❌ Unexpected error while uploading to Hikvision: {e}")
        return False

    async def register_with_face(self, user_id: str, user_name: str, image_path: str, device_ids: list[int] = None) -> bool:
        if not self.enabled:
            return True
        user_created = await self.create_user(user_id, user_name, device_ids)
        if user_created:
            return await self.upload_face_image(user_id, image_path)
        return False

    async def search_card_info(self, employee_no: str, max_results: int = 20):
        """
        Async search for card information by employee number (user ID).
        """
        if not self.enabled:
            return {"error": "Service disabled"}
            
        payload = {
            "CardInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": max_results,
                "EmployeeNoString": str(employee_no)
            }
        }

        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
            try:
                response = await client.post(
                    self.card_search_url,
                    headers={"Content-Type": "application/json"},
                    content=json.dumps(payload)
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

            except httpx.RequestError as e:
                return {"error": "Request failed", "details": str(e)}

    async def modify_user(self, user_id: str, new_name: str = None,
                          new_gender: str = None, new_validity: dict = None) -> bool:
        """Modify existing user information."""
        if not self.enabled:
            logger.info(f"[Hikvision] Disabled. Skipping modify_user for {user_id}")
            return True
            
        payload = {"UserInfo": {"employeeNo": str(user_id)}}

        if new_name:
            payload["UserInfo"]["name"] = new_name
        if new_gender:
            payload["UserInfo"]["gender"] = new_gender
        if new_validity:
            payload["UserInfo"]["Valid"] = {
                "enable": True,
                "beginTime": new_validity.get("beginTime", "2020-01-01T00:00:00"),
                "endTime": new_validity.get("endTime", "2037-12-31T23:59:59")
            }

        logger.info(f"Attempting to modify user ID '{user_id}' on Hikvision...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.put(
                    self.user_modify_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                logger.info("✅ User modified successfully on Hikvision.")
                return True
            except httpx.HTTPStatusError as err:
                logger.error(f"❌ Failed to modify user on Hikvision. {err}")
                logger.error(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                logger.error(f"❌ Request error to Hikvision: {err}")
        return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by employeeNo."""
        if not self.enabled:
            logger.info(f"[Hikvision] Disabled. Skipping delete_user for {user_id}")
            return True
            
        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [{"employeeNo": str(user_id)}]
            }
        }
        logger.info(f"Attempting to delete user ID '{user_id}' on Hikvision...")
        async with httpx.AsyncClient(auth=self.auth) as client:
            try:
                response = await client.put(
                    self.user_delete_url,
                    headers={'Content-Type': 'application/json'},
                    content=json.dumps(payload),
                    timeout=10,
                )
                response.raise_for_status()
                logger.info("✅ User deleted successfully on Hikvision.")
                return True
            except httpx.HTTPStatusError as err:
                logger.error(f"❌ Failed to delete user on Hikvision. {err}")
                logger.error(f"Response: {err.response.text}")
            except httpx.RequestError as err:
                logger.error(f"❌ Request error to Hikvision: {err}")
        return False
