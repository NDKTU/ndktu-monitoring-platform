import { api } from '@/lib/api'

export const rolesService = {
  list: async (search?: string) => {
    const { data } = await api.get('/roles/list', { params: { search } })
    return data
  },
  create: async (payload: { name: string }) => {
    const { data } = await api.post('/roles/', payload)
    return data
  },
  update: async (id: number, payload: { name: string }) => {
    const { data } = await api.put(`/roles/${id}`, payload)
    return data
  },
  delete: async (id: number) => {
    const { data } = await api.delete(`/roles/${id}`)
    return data
  },
  assignPermissions: async (id: number, permissionIds: number[]) => {
    const { data } = await api.post(`/roles/${id}/permissions`, { permission_ids: permissionIds })
    return data
  }
}
