import { api } from '@/lib/api'
import type {
  User,
  UserCreateInput,
  UserListParams,
  UserListResponse,
} from '@/types/user'

export const usersService = {
  list: async (params?: UserListParams) => {
    const { data } = await api.get<UserListResponse>('/users/list', { params })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<User>(`/users/${id}`)
    return data
  },
  create: async (input: UserCreateInput) => {
    const { data } = await api.post<User>('/users/', input)
    return data
  },
  update: async (id: number, input: Partial<UserCreateInput>) => {
    const { data } = await api.put<User>(`/users/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/users/${id}`)
  },
}
