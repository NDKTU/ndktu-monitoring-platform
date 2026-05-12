import { CalendarCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Pagination } from '@/components/shared/Pagination'
import { ScrollableTable } from '@/components/shared/ScrollableTable'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { usePagedList } from '@/hooks/usePagedList'
import { formatTimeOnly } from '@/lib/time'
import { dailyAttendanceService } from '@/services/dailyAttendance'
import { employeesService } from '@/services/employees'
import type {
  AttendanceStatus,
  DailyAttendance,
  DailyAttendanceListParams,
} from '@/types/dailyAttendance'
import { ATTENDANCE_STATUSES } from '@/types/dailyAttendance'
import type { Employee } from '@/types/employee'

const STATUS_LABELS: Record<AttendanceStatus, string> = {
  ON_TIME: 'Vaqtida',
  LATE_ARRIVAL: 'Kech kelgan',
  EARLY_LEAVE: 'Erta ketgan',
  LATE_AND_EARLY: 'Kech va erta',
  NO_ENTER: 'Kirish yo‘q',
  NO_EXIT: 'Chiqish yo‘q',
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('uz-Latn-UZ', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

export default function DailyAttendancePage() {
  const {
    items,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<DailyAttendance, DailyAttendanceListParams>({
    fetcher: dailyAttendanceService.list,
    itemsKey: 'items',
    initialParams: { page: 1, limit: 10 },
  })

  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [status, setStatus] = useState<'all' | AttendanceStatus>('all')
  const [employeeId, setEmployeeId] = useState<string>('all')

  const [employees, setEmployees] = useState<Employee[]>([])

  useEffect(() => {
    let cancelled = false
    employeesService
      .list({ limit: 200 })
      .then((res) => {
        if (!cancelled) setEmployees(res.employees)
      })
      .catch((err) => console.error('Failed to load employees', err))
    return () => {
      cancelled = true
    }
  }, [])

  const apply = (
    next: Partial<{
      date_from: string
      date_to: string
      status: 'all' | AttendanceStatus
      employee_id: string
    }>,
  ) => {
    if (next.date_from !== undefined) setDateFrom(next.date_from)
    if (next.date_to !== undefined) setDateTo(next.date_to)
    if (next.status !== undefined) setStatus(next.status)
    if (next.employee_id !== undefined) setEmployeeId(next.employee_id)

    setParams((prev) => {
      const df = next.date_from ?? dateFrom
      const dt = next.date_to ?? dateTo
      const st = next.status ?? status
      const ei = next.employee_id ?? employeeId
      return {
        ...prev,
        date_from: df || undefined,
        date_to: dt || undefined,
        status: st === 'all' ? undefined : st,
        employee_id: ei === 'all' ? undefined : Number(ei),
      }
    })
  }

  return (
    <>
      <PageHeader
        title="Kunlik davomat"
        description="Xodimlarning kunlik kelish-ketish holati va ish soatlari"
      />

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-full space-y-2 sm:w-44">
            <Label htmlFor="daily-date-from">Sanadan</Label>
            <Input
              id="daily-date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => apply({ date_from: e.target.value })}
            />
          </div>
          <div className="w-full space-y-2 sm:w-44">
            <Label htmlFor="daily-date-to">Sanagacha</Label>
            <Input
              id="daily-date-to"
              type="date"
              value={dateTo}
              onChange={(e) => apply({ date_to: e.target.value })}
            />
          </div>
          <div className="w-full space-y-2 sm:w-48">
            <Label htmlFor="daily-status">Status</Label>
            <Select
              value={status}
              onValueChange={(v) =>
                apply({ status: v as 'all' | AttendanceStatus })
              }
            >
              <SelectTrigger id="daily-status" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha statuslar</SelectItem>
                {ATTENDANCE_STATUSES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {STATUS_LABELS[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-full space-y-2 sm:w-56">
            <Label htmlFor="daily-employee">Xodim</Label>
            <Select
              value={employeeId}
              onValueChange={(v) => apply({ employee_id: v })}
            >
              <SelectTrigger id="daily-employee" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha xodimlar</SelectItem>
                {employees.map((e) => (
                  <SelectItem key={e.id} value={String(e.id)}>
                    {e.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        {error ? (
          <div className="p-6">
            <ErrorState onRetry={refetch} />
          </div>
        ) : loading ? (
          <div className="space-y-2 p-6">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={CalendarCheck}
              title="Yozuvlar topilmadi"
              description="Filtrlarni o‘zgartiring."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Sana</TableHead>
                    <TableHead>Xodim</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Kelish</TableHead>
                    <TableHead>Ketish</TableHead>
                    <TableHead className="text-right">Soat</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="tabular-nums">
                        {formatDate(item.date)}
                      </TableCell>
                      <TableCell>
                        {item.employee?.full_name ?? `#${item.employee_id}`}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={item.status} />
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {formatTimeOnly(item.first_enter_time)}
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {formatTimeOnly(item.last_exit_time)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {item.total_working_hours.toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollableTable>
            <Pagination
              page={page}
              limit={limit}
              total={total}
              onPageChange={setPage}
              onLimitChange={setLimit}
            />
          </>
        )}
      </Card>
    </>
  )
}
