import { api } from '@/lib/api'
import type {
  Department,
  DepartmentCreateInput,
  DepartmentListResponse,
  DepartmentUpdateInput,
  DepartmentListParams,
} from '@/types/department'

export const departmentsService = {
  list: async (params?: DepartmentListParams) => {
    const { data } = await api.get<DepartmentListResponse>('/departments/list', {
      params,
    })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Department>(`/departments/${id}`)
    return data
  },
  create: async (input: DepartmentCreateInput) => {
    const { data } = await api.post<Department>('/departments/', input)
    return data
  },
  update: async (id: number, input: DepartmentUpdateInput) => {
    const { data } = await api.put<Department>(`/departments/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/departments/${id}`)
  },
}
