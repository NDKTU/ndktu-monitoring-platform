import { api } from '@/lib/api'
import type {
  WorkSchedule,
  WorkScheduleCreateInput,
  WorkScheduleEmployeesInput,
  WorkScheduleEmployeesParams,
  WorkScheduleEmployeesResponse,
  WorkScheduleEmployeesResult,
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
  listEmployees: async (
    id: number,
    params?: WorkScheduleEmployeesParams,
  ) => {
    const { data } = await api.get<WorkScheduleEmployeesResponse>(
      `/work-schedules/${id}/employees`,
      { params },
    )
    return data
  },
  assignEmployees: async (id: number, input: WorkScheduleEmployeesInput) => {
    const { data } = await api.post<WorkScheduleEmployeesResult>(
      `/work-schedules/${id}/employees`,
      input,
    )
    return data
  },
  unassignEmployees: async (id: number, input: WorkScheduleEmployeesInput) => {
    const { data } = await api.delete<WorkScheduleEmployeesResult>(
      `/work-schedules/${id}/employees`,
      { data: input },
    )
    return data
  },
}
