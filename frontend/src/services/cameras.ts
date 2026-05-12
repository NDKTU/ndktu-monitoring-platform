import { api } from '@/lib/api'
import type {
  Camera,
  CameraCreateInput,
  CameraListParams,
  CameraListResponse,
} from '@/types/camera'

export const camerasService = {
  list: async (params?: CameraListParams) => {
    const { data } = await api.get<CameraListResponse>('/cameras/list', {
      params,
    })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<Camera>(`/cameras/${id}`)
    return data
  },
  create: async (input: CameraCreateInput) => {
    const { data } = await api.post<Camera>('/cameras/', input)
    return data
  },
  update: async (id: number, input: Partial<CameraCreateInput>) => {
    const { data } = await api.put<Camera>(`/cameras/${id}`, input)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/cameras/${id}`)
  },
  connect: async (id: number) => {
    await api.post(`/cameras/${id}/connect`)
  },
  disconnect: async (id: number) => {
    await api.post(`/cameras/${id}/disconnect`)
  },
  restart: async (id: number) => {
    await api.post(`/cameras/${id}/restart`)
  },
}
