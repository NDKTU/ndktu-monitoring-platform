import type { WorkSchedule } from './workSchedule'

export type PositionShort = {
  id: number
  name: string
}

export type DepartmentShort = {
  id: number
  name: string
  work_schedule_id?: number | null
  work_schedule?: WorkSchedule | null
}

export type Employee = {
  id: number
  first_name: string
  last_name: string
  third_name?: string | null
  passport_series?: string | null
  jshir: string
  in_work: boolean
  image_path?: string | null
  position_id?: number | null
  department_id?: number | null
  position?: PositionShort | null
  department?: DepartmentShort | null
  full_name: string
  work_rate: number
}

export type EmployeeShortResponse = {
  id: number
  first_name: string
  last_name: string
  third_name?: string | null
  jshir: string
  full_name: string
}

export type EmployeeCreateInput = {
  first_name: string
  last_name: string
  third_name?: string | null
  passport_series?: string | null
  jshir: string
  in_work?: boolean
  image_path?: string | null
  position_id?: number | null
  department_id?: number | null
  work_rate?: number
}

export type EmployeeUpdateInput = Partial<EmployeeCreateInput>

export type EmployeeListParams = {
  page?: number
  limit?: number
  search?: string
  in_work?: boolean
  jshir?: string
}

export type EmployeeListResponse = {
  total: number
  page: number
  limit: number
  employees: Employee[]
}
