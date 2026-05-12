import { api } from '@/lib/api'
import type {
  WorkSchedule,
  WorkScheduleCreateInput,
  WorkScheduleListParams,
  WorkScheduleListResponse,
  WorkScheduleUpdateInput,
} from '@/types/workSchedule'

export const workSchedulesService = {
  list: async (params?: WorkScheduleListParams) => {
    const { data } = await api.get<WorkScheduleListResponse>(
      '/work-schedules/list',
      { params },
    )
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<WorkSchedule>(`/work-schedules/${id}`)
    return data
  },
  create: async (input: WorkScheduleCreateInput) => {
    const { data } = await api.post<WorkSchedule>('/work-schedules/', input)
    return data
  },
  update: async (id: number, input: WorkScheduleUpdateInput) => {
    const { data } = await api.put<WorkSchedule>(
      `/work-schedules/${id}`,
      input,
    )
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/work-schedules/${id}`)
  },
}
