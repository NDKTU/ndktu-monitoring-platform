import { api } from '@/lib/api'
import type {
  Position,
  PositionCreateInput,
  PositionListResponse,
  PositionUpdateInput,
  PositionListParams,
} from '@/types/position'

export const positionsService = {
  list: async (params?: PositionListParams) => {
    const { data } = await api.get<PositionListResponse>('/positions/list', {
      params,
    })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Position>(`/positions/${id}`)
    return data
  },
  create: async (input: PositionCreateInput) => {
    const { data } = await api.post<Position>('/positions/', input)
    return data
  },
  update: async (id: number, input: PositionUpdateInput) => {
    const { data } = await api.put<Position>(`/positions/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/positions/${id}`)
  },
}
