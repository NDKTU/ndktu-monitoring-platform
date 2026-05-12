export type WorkSchedule = {
  id: number
  employee_id: number
  start_time: string
  end_time: string
  grace_minutes: number
}

export type WorkScheduleCreateInput = {
  employee_id: number
  start_time: string
  end_time: string
  grace_minutes?: number
}

export type WorkScheduleUpdateInput = {
  start_time?: string
  end_time?: string
  grace_minutes?: number
}

export type WorkScheduleListParams = {
  page?: number
  limit?: number
  employee_id?: number
}

export type WorkScheduleListResponse = {
  total: number
  page: number
  limit: number
  schedules: WorkSchedule[]
}
