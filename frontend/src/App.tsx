import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import LoginPage from '@/pages/Login'
import CamerasPage from '@/pages/Cameras'
import DailyAttendancePage from '@/pages/DailyAttendance'
import DashboardPage from '@/pages/Dashboard'
import EmployeeDetailPage from '@/pages/EmployeeDetail'
import EmployeesPage from '@/pages/Employees'
import PositionsPage from '@/pages/Positions'
import DepartmentsPage from '@/pages/Departments'
import UsersPage from '@/pages/Users'
import WorkSchedulesPage from '@/pages/WorkSchedules'
import WorkScheduleDetailPage from '@/pages/WorkScheduleDetail'
import TabelPage from '@/pages/Tabel'
import RolesPage from '@/pages/Roles'
import PermissionsPage from '@/pages/Permissions'

export default function App() {
  return (
    <>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="cameras" element={<CamerasPage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="employees/:id" element={<EmployeeDetailPage />} />
            <Route path="positions" element={<PositionsPage />} />
            <Route path="departments" element={<DepartmentsPage />} />
            <Route path="daily-attendance" element={<DailyAttendancePage />} />
            <Route path="work-schedules" element={<WorkSchedulesPage />} />
            <Route path="work-schedules/:id" element={<WorkScheduleDetailPage />} />
            <Route path="tabel" element={<TabelPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="roles" element={<RolesPage />} />
            <Route path="permissions" element={<PermissionsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </>
  )
}
