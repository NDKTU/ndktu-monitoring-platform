import { api } from '@/lib/api'
import type {
  Employee,
  EmployeeCreateInput,
  EmployeeListParams,
  EmployeeListResponse,
  EmployeeUpdateInput,
} from '@/types/employee'

export const employeesService = {
  list: async (params?: EmployeeListParams) => {
    const { data } = await api.get<EmployeeListResponse>('/employees/list', {
      params,
    })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Employee>(`/employees/${id}`)
    return data
  },
  create: async (input: EmployeeCreateInput) => {
    const { data } = await api.post<Employee>('/employees/', input)
    return data
  },
  update: async (id: number, input: EmployeeUpdateInput) => {
    const { data } = await api.put<Employee>(`/employees/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/employees/${id}`)
  },
}
