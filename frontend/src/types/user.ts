export type User = {
  id: number
  username: string
  is_active: boolean
  role_id: number | null
  role: { id: number; name: string } | null
}

export type UserCreateInput = {
  username: string
  password?: string
  is_active?: boolean
  role_id?: number | null
}

export type UserListParams = {
  page?: number
  limit?: number
  search?: string
  is_active?: boolean
  role_id?: number
}

export type UserListResponse = {
  total: number
  page: number
  limit: number
  users: User[]
}
