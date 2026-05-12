export type User = {
  id: number
  username: string
  is_active: boolean
  is_superuser: boolean
}

export type UserCreateInput = {
  username: string
  password: string
  is_active?: boolean
  is_superuser?: boolean
}

export type UserListParams = {
  page?: number
  limit?: number
  search?: string
  is_active?: boolean
  is_superuser?: boolean
}

export type UserListResponse = {
  total: number
  page: number
  limit: number
  users: User[]
}
