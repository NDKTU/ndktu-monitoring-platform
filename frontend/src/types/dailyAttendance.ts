import type { EmployeeShortResponse } from '@/types/employee'

export type AttendanceStatus =
  | 'ON_TIME'
  | 'LATE_ARRIVAL'
  | 'EARLY_LEAVE'
  | 'LATE_AND_EARLY'
  | 'NO_ENTER'
  | 'NO_EXIT'

export const ATTENDANCE_STATUSES: AttendanceStatus[] = [
  'ON_TIME',
  'LATE_ARRIVAL',
  'EARLY_LEAVE',
  'LATE_AND_EARLY',
  'NO_ENTER',
  'NO_EXIT',
]

export type DailyAttendance = {
  id: number
  employee_id: number
  date: string
  status: AttendanceStatus | null
  total_working_hours: number
  first_enter_time: string | null
  last_exit_time: string | null
  has_no_enter: boolean
  has_no_exit: boolean
  employee?: EmployeeShortResponse | null
}

export type DailyAttendanceListParams = {
  page?: number
  limit?: number
  employee_id?: number
  date_from?: string
  date_to?: string
  status?: AttendanceStatus
}

export type DailyAttendanceListResponse = {
  total: number
  page: number
  limit: number
  items: DailyAttendance[]
}
