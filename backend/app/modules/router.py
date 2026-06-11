from fastapi import APIRouter

from app.modules.camera.router import router as camera_router
from app.modules.user.router import router as user_router
from app.modules.employee.router import router as employee_router
from app.modules.attendance.router import router as attendance_router
from app.modules.work_schedule.router import router as work_schedule_router
from app.modules.daily_attendance.router import router as daily_attendance_router
from app.modules.tabel.router import router as tabel_router
from app.modules.position.router import router as position_router
from app.modules.department.router import router as department_router
from app.modules.auth.router import router as auth_router
from app.modules.role.router import router as role_router
from app.modules.permission.router import router as permission_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(role_router)
router.include_router(permission_router)
router.include_router(camera_router)
router.include_router(user_router)
router.include_router(employee_router)
router.include_router(attendance_router)
router.include_router(work_schedule_router)
router.include_router(daily_attendance_router)
router.include_router(tabel_router)
router.include_router(position_router)
router.include_router(department_router)
