import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import CamerasPage from '@/pages/Cameras'
import DailyAttendancePage from '@/pages/DailyAttendance'
import DashboardPage from '@/pages/Dashboard'
import EmployeeDetailPage from '@/pages/EmployeeDetail'
import EmployeesPage from '@/pages/Employees'
import UsersPage from '@/pages/Users'
import WorkSchedulesPage from '@/pages/WorkSchedules'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="cameras" element={<CamerasPage />} />
        <Route path="employees" element={<EmployeesPage />} />
        <Route path="employees/:id" element={<EmployeeDetailPage />} />
        <Route path="daily-attendance" element={<DailyAttendancePage />} />
        <Route path="work-schedules" element={<WorkSchedulesPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
