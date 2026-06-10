export type Position = {
  id: number
  name: string
  created_at?: string
  updated_at?: string
}

export type PositionCreateInput = {
  name: string
}

export type PositionUpdateInput = {
  name: string
}

export type PositionListParams = {
  page?: number
  limit?: number
  search?: string
}

export type PositionListResponse = {
  total: number
  page: number
  limit: number
  positions: Position[]
}
