import { api } from '@/lib/api'
import type {
  Attendance,
  AttendanceListParams,
  AttendanceListResponse,
} from '@/types/attendance'

export const attendanceService = {
  list: async (params?: AttendanceListParams) => {
    const { data } = await api.get<AttendanceListResponse>(
      '/attendance/list',
      { params },
    )
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Attendance>(`/attendance/${id}`)
    return data
  },
}
