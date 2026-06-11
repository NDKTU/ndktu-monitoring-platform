from fastapi import HTTPException, status, UploadFile
from app.modules.employee.hikvision_service import HikiUserService
from app.modules.camera.repository import CameraRepository
from app.core.config import settings
import logging

from app.models.employees.model import Employee
from app.modules.employee.repository import EmployeeRepository
from app.modules.employee.schemas import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeListRequest,
    EmployeeListResponse,
    EmployeeUploadResponse,
)

class EmployeeService:
    def __init__(self, repository: EmployeeRepository) -> None:
        self.repository = repository

    async def _sync_with_hikvision(self, action: str, **kwargs):
        if not settings.hikvision.enabled:
            return
            
        camera_repo = CameraRepository(self.repository.session)
        cameras = await camera_repo.get_all_active_cameras()
        
        async def sync_single_camera(camera):
            hiki_service = HikiUserService(
                ip_address=camera.device_ip,
                username=camera.login,
                password=camera.password,
                enabled=True
            )
            
            # Check if camera is actually reachable before attempting
            is_reachable = await hiki_service.check_connection()
            if not is_reachable:
                logging.warning(f"Camera {camera.device_ip} is unreachable. Skipping {action}.")
                # Optionally, here we could update camera.is_active = False in DB
                return
                
            try:
                if action == "create":
                    await hiki_service.create_user(user_id=kwargs['user_id'], user_name=kwargs['user_name'])
                elif action == "modify":
                    await hiki_service.modify_user(user_id=kwargs['user_id'], new_name=kwargs['user_name'])
                elif action == "delete":
                    await hiki_service.delete_user(user_id=kwargs['user_id'])
                elif action == "upload_face":
                    success = await hiki_service.upload_face_image(user_id=kwargs['user_id'], image_path=kwargs['image_path'])
                    if not success:
                         logging.error(f"Failed to upload face on camera {camera.device_ip}")
            except Exception as e:
                logging.error(f"Failed to {action} on camera {camera.device_ip}: {e}")

        import asyncio
        # Run syncs concurrently for all active cameras
        tasks = [sync_single_camera(camera) for camera in cameras]
        if tasks:
            await asyncio.gather(*tasks)

    async def create_employee(self, employee: EmployeeCreateRequest) -> Employee:
        new_employee = await self.repository.create_employee(employee)
        # Sync with Hikvision
        user_name = f"{new_employee.first_name} {new_employee.last_name}"
        await self._sync_with_hikvision("create", user_id=new_employee.jshir, user_name=user_name)
        return new_employee

    async def list_employees(self, request: EmployeeListRequest) -> EmployeeListResponse:
        return await self.repository.list_employees(request)

    async def get_employee(self, employee_id: int) -> Employee:
        employee = await self.repository.get_employee(employee_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        return employee

    async def update_employee(
        self, employee_id: int, employee: EmployeeUpdateRequest
    ) -> Employee:
        updated = await self.repository.update_employee(employee_id, employee)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        
        # Sync with Hikvision
        user_name = f"{updated.first_name} {updated.last_name}"
        await self._sync_with_hikvision("modify", user_id=updated.jshir, user_name=user_name)
        
        return updated

    async def delete_employee(self, employee_id: int) -> Employee:
        deleted = await self.repository.delete_employee(employee_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
            )
        
        # Sync with Hikvision
        await self._sync_with_hikvision("delete", user_id=deleted.jshir)
        
        return deleted

    async def upload_excel(self, file: UploadFile) -> EmployeeUploadResponse:
        import io
        import pandas as pd
        from sqlalchemy import select

        from app.modules.position.repository import PositionRepository
        from app.modules.position.schemas import PositionCreateRequest
        from app.modules.department.repository import DepartmentRepository
        from app.modules.department.schemas import DepartmentCreateRequest
        from app.models.employees.model import Employee

        try:
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content), dtype=str)
        except Exception as e:
            return EmployeeUploadResponse(
                success=False,
                imported_count=0,
                errors=[f"Excel faylni o'qishda xatolik yuz berdi: {str(e)}"]
            )

        columns = [str(col).strip() for col in df.columns]

        normalized_mapping = {
            "lastname": "last_name", "familiya": "last_name", "фамилия": "last_name",
            "firstname": "first_name", "ism": "first_name", "имя": "first_name",
            "thirdname": "third_name", "sharif": "third_name", "patronymic": "third_name",
            "middlename": "third_name", "otchestvo": "third_name", "отчество": "third_name",
            "passportseries": "passport_series", "passport": "passport_series", "pasport": "passport_series", "паспорт": "passport_series",
            "jshir": "jshir", "pinfl": "jshir", "жшир": "jshir", "пинфл": "jshir",
            "inwork": "in_work", "ishdami": "in_work", "ishlamoqdami": "in_work", "работает": "in_work", "active": "in_work",
            "workrate": "work_rate", "stavka": "work_rate", "ставка": "work_rate",
            "position": "position", "lavozim": "position", "должность": "position",
            "department": "department", "bolim": "department", "bo'lim": "department", "отдел": "department",
        }

        field_mapping = {}
        for col in columns:
            normalized_col = "".join(c for c in col.lower() if c.isalnum())
            if normalized_col in normalized_mapping:
                field_mapping[normalized_mapping[normalized_col]] = col
            elif normalized_col in ("firstname", "first_name"):
                field_mapping["first_name"] = col
            elif normalized_col in ("lastname", "last_name"):
                field_mapping["last_name"] = col
            elif normalized_col in ("thirdname", "third_name"):
                field_mapping["third_name"] = col
            elif normalized_col in ("passportseries", "passport_series"):
                field_mapping["passport_series"] = col
            elif normalized_col in ("jshir",):
                field_mapping["jshir"] = col
            elif normalized_col in ("inwork", "in_work"):
                field_mapping["in_work"] = col
            elif normalized_col in ("workrate", "work_rate"):
                field_mapping["work_rate"] = col
            elif normalized_col in ("position",):
                field_mapping["position"] = col
            elif normalized_col in ("department",):
                field_mapping["department"] = col

        required_fields = ["first_name", "last_name", "jshir"]
        missing_fields = [f for f in required_fields if f not in field_mapping]
        if missing_fields:
            return EmployeeUploadResponse(
                success=False,
                imported_count=0,
                errors=[f"Excel faylda majburiy ustunlar topilmadi. Muqobil ustun nomlari: Ism, Familiya, JShShIR (PINFL). Missing mappings for: {', '.join(missing_fields)}"]
            )

        position_repo = PositionRepository(self.repository.session)
        department_repo = DepartmentRepository(self.repository.session)

        position_cache = {}
        department_cache = {}

        async def get_or_create_position(pos_name: str) -> int | None:
            if not pos_name:
                return None
            pos_name_clean = pos_name.strip()
            pos_name_lower = pos_name_clean.lower()
            if pos_name_lower in position_cache:
                return position_cache[pos_name_lower]

            db_pos = await position_repo.find_by_name(pos_name_clean)
            if not db_pos:
                db_pos = await position_repo.create_position(PositionCreateRequest(name=pos_name_clean))
            position_cache[pos_name_lower] = db_pos.id
            return db_pos.id

        async def get_or_create_department(dept_name: str) -> int | None:
            if not dept_name:
                return None
            dept_name_clean = dept_name.strip()
            dept_name_lower = dept_name_clean.lower()
            if dept_name_lower in department_cache:
                return department_cache[dept_name_lower]

            db_dept = await department_repo.find_by_name(dept_name_clean)
            if not db_dept:
                db_dept = await department_repo.create_department(DepartmentCreateRequest(name=dept_name_clean))
            department_cache[dept_name_lower] = db_dept.id
            return db_dept.id

        imported_count = 0
        errors = []

        def clean_val(val):
            if pd.isna(val):
                return None
            val_str = str(val).strip()
            if val_str == "" or val_str.lower() in ("none", "nan", "null"):
                return None
            return val_str

        def parse_bool(val):
            if val is None:
                return True
            val_str = str(val).lower().strip()
            if val_str in ("1", "true", "yes", "y", "ha", "да", "д", "active", "aktiv"):
                return True
            if val_str in ("0", "false", "no", "n", "yo'q", "yoq", "нет", "н", "inactive", "faol_emas"):
                return False
            return True

        for idx, row in df.iterrows():
            row_num = idx + 2

            try:
                first_name = clean_val(row[field_mapping["first_name"]])
                last_name = clean_val(row[field_mapping["last_name"]])
                jshir = clean_val(row[field_mapping["jshir"]])

                if not first_name or not last_name or not jshir:
                    errors.append(f"{row_num}-qatorda xatolik: Ism, Familiya va JShShIR to'ldirilishi shart.")
                    continue

                jshir = jshir.replace(" ", "").replace("-", "")
                if not jshir.isdigit() or len(jshir) != 14:
                    errors.append(f"{row_num}-qatorda xatolik: JShShIR 14 ta raqamdan iborat bo'lishi kerak. Topildi: '{jshir}'")
                    continue

                third_name = None
                if "third_name" in field_mapping:
                    third_name = clean_val(row[field_mapping["third_name"]])

                passport_series = None
                if "passport_series" in field_mapping:
                    passport_series = clean_val(row[field_mapping["passport_series"]])
                    if passport_series:
                        passport_series = passport_series.replace(" ", "").upper()

                in_work_val = None
                if "in_work" in field_mapping:
                    in_work_val = clean_val(row[field_mapping["in_work"]])
                in_work = parse_bool(in_work_val)

                work_rate = 1.0
                if "work_rate" in field_mapping:
                    wr_val = clean_val(row[field_mapping["work_rate"]])
                    if wr_val:
                        try:
                            work_rate = float(wr_val.replace(",", "."))
                        except ValueError:
                            errors.append(f"{row_num}-qatorda ogohlantirish: Stavka format xato, '1.0' deb olindi.")

                position_id = None
                if "position" in field_mapping:
                    pos_name = clean_val(row[field_mapping["position"]])
                    if pos_name:
                        position_id = await get_or_create_position(pos_name)

                department_id = None
                if "department" in field_mapping:
                    dept_name = clean_val(row[field_mapping["department"]])
                    if dept_name:
                        department_id = await get_or_create_department(dept_name)

                if passport_series:
                    passport_check = await self.repository.session.execute(
                        select(Employee).where(
                            Employee.passport_series == passport_series,
                            Employee.jshir != jshir
                        )
                    )
                    if passport_check.scalar_one_or_none():
                        errors.append(f"{row_num}-qatorda xatolik: '{passport_series}' pasport seriyasi boshqa xodimda mavjud.")
                        continue

                existing = await self.repository.get_employee_by_jshir(jshir)

                if existing:
                    existing.first_name = first_name
                    existing.last_name = last_name
                    existing.third_name = third_name
                    existing.passport_series = passport_series
                    existing.in_work = in_work
                    existing.work_rate = work_rate
                    if position_id is not None:
                        existing.position_id = position_id
                    if department_id is not None:
                        existing.department_id = department_id
                else:
                    new_employee = Employee(
                        first_name=first_name,
                        last_name=last_name,
                        third_name=third_name,
                        passport_series=passport_series,
                        jshir=jshir,
                        in_work=in_work,
                        work_rate=work_rate,
                        position_id=position_id,
                        department_id=department_id,
                    )
                    self.repository.session.add(new_employee)

                await self.repository.session.commit()
                imported_count += 1

                # Sync with Hikvision (non-blocking errors)
                try:
                    user_name = f"{first_name} {last_name}"
                    await self._sync_with_hikvision("create", user_id=jshir, user_name=user_name)
                except Exception as hik_err:
                    import logging
                    logging.error(f"Hikvision sync error for {jshir}: {hik_err}")

            except Exception as row_err:
                await self.repository.session.rollback()
                errors.append(f"{row_num}-qatorda xatolik: {str(row_err)}")

        return EmployeeUploadResponse(
            success=True,
            imported_count=imported_count,
            errors=errors
        )

    async def upload_face(self, employee_id: int, file: UploadFile) -> dict:
        import os
        import uuid
        
        employee = await self.get_employee(employee_id)
        
        # Save file locally first
        upload_dir = "uploads/faces"
        os.makedirs(upload_dir, exist_ok=True)
        
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        file_name = f"{employee.jshir}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Sync with Hikvision
        await self._sync_with_hikvision("upload_face", user_id=employee.jshir, image_path=file_path)
            
        return {"success": True, "message": "Face uploaded successfully", "path": file_path}

