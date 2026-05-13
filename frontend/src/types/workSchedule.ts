export type WorkSchedule = {
  id: number
  start_time: string
  end_time: string
  grace_minutes: number
  employee_count: number
}

export type WorkScheduleCreateInput = {
  start_time: string
  end_time: string
  grace_minutes: number
}

export type WorkScheduleUpdateInput = {
  start_time: string
  end_time: string
  grace_minutes: number
}

export type WorkScheduleListParams = {
  page?: number
  limit?: number
}

export type WorkScheduleListResponse = {
  total: number
  page: number
  limit: number
  schedules: WorkSchedule[]
}

export type WorkScheduleEmployee = {
  id: number
  first_name: string
  last_name: string
  third_name: string | null
  full_name: string
}

export type WorkScheduleEmployeesParams = {
  page?: number
  limit?: number
}

export type WorkScheduleEmployeesResponse = {
  total: number
  page: number
  limit: number
  employees: WorkScheduleEmployee[]
}

export type WorkScheduleEmployeesInput = {
  employee_ids: number[]
}

export type WorkScheduleEmployeesResult = {
  affected: number
}
