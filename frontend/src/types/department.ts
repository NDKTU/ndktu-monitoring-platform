import type { WorkSchedule } from './workSchedule'

export type Department = {
  id: number
  name: string
  work_schedule_id?: number | null
  work_schedule?: WorkSchedule | null
  created_at?: string
  updated_at?: string
}

export type DepartmentCreateInput = {
  name: string
  work_schedule_id?: number | null
}

export type DepartmentUpdateInput = {
  name: string
  work_schedule_id?: number | null
}

export type DepartmentListParams = {
  page?: number
  limit?: number
  search?: string
}

export type DepartmentListResponse = {
  total: number
  page: number
  limit: number
  departments: Department[]
}
