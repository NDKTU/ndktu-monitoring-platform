import { api } from '@/lib/api'
import type {
  DailyAttendance,
  DailyAttendanceListParams,
  DailyAttendanceListResponse,
} from '@/types/dailyAttendance'

export const dailyAttendanceService = {
  list: async (params?: DailyAttendanceListParams) => {
    const { data } = await api.get<DailyAttendanceListResponse>(
      '/daily-attendance/list',
      { params },
    )
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<DailyAttendance>(
      `/daily-attendance/${id}`,
    )
    return data
  },
}
