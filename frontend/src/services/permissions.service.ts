import { api } from '@/lib/api'

export const permissionsService = {
  list: async (search?: string) => {
    const { data } = await api.get('/permissions/list', { params: { search } })
    return data
  }
}
