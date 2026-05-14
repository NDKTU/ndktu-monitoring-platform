import { api } from '@/lib/api'
import type {
  TabelEntryDeleteInput,
  TabelEntryUpsertInput,
  TabelMonthParams,
  TabelMonthResponse,
} from '@/types/tabel'

export const tabelService = {
  getMonth: async (params: TabelMonthParams) => {
    const { data } = await api.get<TabelMonthResponse>('/tabel/month', {
      params,
    })
    return data
  },
  upsertEntry: async (input: TabelEntryUpsertInput) => {
    const { data } = await api.put<{ ok: boolean }>('/tabel/entry', input)
    return data
  },
  deleteEntry: async (input: TabelEntryDeleteInput) => {
    const { data } = await api.delete<{ ok: boolean }>('/tabel/entry', {
      data: input,
    })
    return data
  },
}
