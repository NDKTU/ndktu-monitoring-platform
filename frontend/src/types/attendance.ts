import type { EmployeeShortResponse } from '@/types/employee'

export type Attendance = {
  id: number
  employee_id: number
  camera_id: number
  enter_time: string
  exit_time?: string | null
  enter_image_path?: string | null
  exit_image_path?: string | null
  working_hours?: number | null
  employee?: EmployeeShortResponse | null
}

export type AttendanceListParams = {
  page?: number
  limit?: number
  employee_id?: number
  camera_id?: number
  enter_time?: string
  exit_time?: string
}

export type AttendanceListResponse = {
  total: number
  page: number
  limit: number
  events: Attendance[]
}
