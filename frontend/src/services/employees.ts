import { api } from '@/lib/api'
import type {
  Employee,
  EmployeeCreateInput,
  EmployeeCreateResponse,
  EmployeeListParams,
  EmployeeListResponse,
  EmployeeUpdateInput,
  FaceUploadResponse,
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
  /**
   * Creates the employee and enrols their face in one request. The face is
   * required: the backend rolls the employee back if no terminal accepts it.
   */
  create: async (input: EmployeeCreateInput, face: File) => {
    const body = new FormData()
    Object.entries(input).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        body.append(key, String(value))
      }
    })
    body.append('file', face)
    const { data } = await api.post<EmployeeCreateResponse>('/employees/', body)
    return data
  },
  update: async (id: number, input: EmployeeUpdateInput) => {
    const { data } = await api.put<Employee>(`/employees/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/employees/${id}`)
  },
  /** Enrols the face on every active terminal and keeps it as the avatar. */
  uploadFace: async (id: number, file: File) => {
    const body = new FormData()
    body.append('file', file)
    const { data } = await api.post<FaceUploadResponse>(
      `/employees/${id}/face`,
      body,
    )
    return data
  },
}
