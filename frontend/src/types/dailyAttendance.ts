import type { EmployeeShortResponse } from '@/types/employee'
import type { TabelCode } from '@/types/tabel'

export type AttendanceStatus =
  | 'ON_TIME'
  | 'LATE_ARRIVAL'
  | 'EARLY_LEAVE'
  | 'LATE_AND_EARLY'
  | 'NO_ENTER'
  | 'NO_EXIT'

// Days with no record of their own. The backend computes them while reading and
// never stores them, so they are not filterable — keep them out of
// ATTENDANCE_STATUSES, which feeds the filter dropdown.
export type SyntheticDayStatus = 'ABSENT' | 'DAY_OFF'

export type DayStatus = AttendanceStatus | SyntheticDayStatus

export const ATTENDANCE_STATUSES: AttendanceStatus[] = [
  'ON_TIME',
  'LATE_ARRIVAL',
  'EARLY_LEAVE',
  'LATE_AND_EARLY',
  'NO_ENTER',
  'NO_EXIT',
]

export type DailyAttendance = {
  // null for a synthesised absent/day-off day.
  id: number | null
  employee_id: number
  date: string
  status: DayStatus | null
  total_working_hours: number
  first_enter_time: string | null
  last_exit_time: string | null
  has_no_enter: boolean
  has_no_exit: boolean
  // A tabel mark set by hand for this day; only filled in fill_absent mode.
  tabel_code?: TabelCode | null
  tabel_comment?: string | null
  employee?: EmployeeShortResponse | null
}

export type DailyAttendanceListParams = {
  page?: number
  limit?: number
  employee_id?: number
  date_from?: string
  date_to?: string
  status?: AttendanceStatus
  // Walk the calendar and fill the days with no record; needs employee_id.
  fill_absent?: boolean
}

export type DailyAttendanceListResponse = {
  total: number
  page: number
  limit: number
  items: DailyAttendance[]
}
