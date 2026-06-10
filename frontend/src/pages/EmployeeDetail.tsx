import {
  ArrowLeft,
  Camera as CameraIcon,
  ChevronDown,
  ChevronRight,
  ContactRound,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Pagination } from '@/components/shared/Pagination'
import { ScrollableTable } from '@/components/shared/ScrollableTable'
import { StatusBadge } from '@/components/shared/StatusBadge'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatTimeOnly } from '@/lib/time'
import { attendanceService } from '@/services/attendance'
import { dailyAttendanceService } from '@/services/dailyAttendance'
import { employeesService } from '@/services/employees'
import { workSchedulesService } from '@/services/workSchedules'
import type { Attendance } from '@/types/attendance'
import type { DailyAttendance } from '@/types/dailyAttendance'
import type { Employee } from '@/types/employee'
import type { WorkSchedule } from '@/types/workSchedule'

const LOCALE = 'uz-Latn-UZ'

function buildImageUrl(path?: string | null) {
  if (!path) return null
  const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  return `${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

function formatShortDate(value: string) {
  return new Date(value).toLocaleDateString(LOCALE, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

function getInitials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const employeeId = id ? Number.parseInt(id, 10) : Number.NaN

  const [employee, setEmployee] = useState<Employee | null>(null)
  const [employeeLoading, setEmployeeLoading] = useState(true)
  const [employeeError, setEmployeeError] = useState<Error | null>(null)

  useEffect(() => {
    if (!Number.isFinite(employeeId)) return
    let cancelled = false
    setEmployeeLoading(true)
    employeesService
      .get(employeeId)
      .then((data) => {
        if (!cancelled) setEmployee(data)
      })
      .catch((err: Error) => {
        if (!cancelled) setEmployeeError(err)
      })
      .finally(() => {
        if (!cancelled) setEmployeeLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [employeeId])

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="w-fit"
        onClick={() => navigate('/employees')}
      >
        <ArrowLeft className="size-4" aria-hidden />
        Orqaga
      </Button>

      {employeeError ? (
        <ErrorState onRetry={() => navigate(0)} />
      ) : employeeLoading ? (
        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <Skeleton className="h-80 w-full" />
          <div className="space-y-3">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      ) : !employee ? (
        <EmptyState
          icon={ContactRound}
          title="Xodim topilmadi"
          description="Yozuv o‘chirilgan bo‘lishi mumkin."
        />
      ) : (
        <>
          <PageHeader
            title={employee.full_name}
            description={`Xodim tafsiloti — JSHIR ${employee.jshir}`}
          />
          <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <Card>
            <CardHeader className="items-center text-center">
              {(() => {
                const avatar = buildImageUrl(employee.image_path)
                return (
                  <div className="grid size-24 place-items-center overflow-hidden rounded-full bg-muted text-2xl font-semibold text-muted-foreground">
                    {avatar ? (
                      <img
                        src={avatar}
                        alt=""
                        className="size-full object-cover"
                      />
                    ) : (
                      getInitials(employee.full_name)
                    )}
                  </div>
                )
              })()}
              <CardTitle className="text-lg">{employee.full_name}</CardTitle>
              {employee.in_work ? (
                <Badge
                  variant="secondary"
                  className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                >
                  Ishda
                </Badge>
              ) : (
                <Badge variant="outline">Yo‘q</Badge>
              )}
            </CardHeader>
            <Separator />
            <CardContent className="space-y-3 pt-4 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">ID</span>
                <span className="font-medium tabular-nums">#{employee.id}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">JSHIR</span>
                <span className="font-mono text-sm font-medium tabular-nums">
                  {employee.jshir}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Pasport</span>
                <span className="font-medium">
                  {employee.passport_series || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Lavozim</span>
                <span className="font-medium">
                  {employee.position?.name || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Bo'lim</span>
                <span className="font-medium">
                  {employee.department?.name || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Ish stavkasi</span>
                <span className="font-medium">
                  {employee.work_rate ?? 1.0} stavka
                </span>
              </div>
            </CardContent>
            <Separator />
            <CardContent className="pt-4">
              <ScheduleSection employeeId={employee.id} />
            </CardContent>
          </Card>

          <AttendanceSection employeeId={employee.id} />
          </div>
        </>
      )}
    </>
  )
}

function ScheduleSection({ employeeId }: { employeeId: number }) {
  const navigate = useNavigate()
  const [schedule, setSchedule] = useState<WorkSchedule | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const [assignOpen, setAssignOpen] = useState(false)
  const [confirmUnassign, setConfirmUnassign] = useState(false)
  const [availableSchedules, setAvailableSchedules] = useState<WorkSchedule[]>([])
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const fetchSchedule = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const emp = await employeesService.get(employeeId)
      if (emp.department?.work_schedule) {
        setSchedule(emp.department.work_schedule)
      } else {
        setSchedule(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setLoading(false)
    }
  }, [employeeId])

  useEffect(() => {
    fetchSchedule()
  }, [fetchSchedule])

  const openAssign = async () => {
    setSelectedScheduleId(null)
    setFormError(null)
    try {
      const res = await workSchedulesService.list({ limit: 100 })
      setAvailableSchedules(res.schedules)
      setAssignOpen(true)
    } catch {
      setFormError("Jadvallar ro'yxatini yuklab bo'lmadi.")
    }
  }

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedScheduleId) {
      setFormError('Jadvalni tanlang.')
      return
    }
    try {
      setSubmitting(true)
      setFormError(null)
      await workSchedulesService.assignEmployees(selectedScheduleId, {
        employee_ids: [employeeId],
      })
      setAssignOpen(false)
      await fetchSchedule()
    } catch {
      setFormError("Jadvalni tayinlab bo'lmadi.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleUnassign = async () => {
    if (!schedule) return
    try {
      await workSchedulesService.unassignEmployees(schedule.id, {
        employee_ids: [employeeId],
      })
      setConfirmUnassign(false)
      await fetchSchedule()
    } catch (err) {
      console.error('Failed to unassign schedule', err)
    }
  }

  return (
    <>
      <div className="space-y-3 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Ish jadvali
          </span>
          {schedule ? (
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="size-7"
                aria-label="Jadvalga o'tish"
                onClick={() => navigate(`/work-schedules/${schedule.id}`)}
              >
                <Pencil className="size-3.5" aria-hidden />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-7 text-destructive hover:text-destructive"
                aria-label="Ajratish"
                onClick={() => setConfirmUnassign(true)}
              >
                <Trash2 className="size-3.5" aria-hidden />
              </Button>
            </div>
          ) : null}
        </div>

        {loading ? (
          <Skeleton className="h-16 w-full" />
        ) : error ? (
          <p className="text-sm text-destructive">
            Jadvalni yuklab bo'lmadi
          </p>
        ) : schedule ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Boshlanish</span>
              <span className="font-medium tabular-nums">
                {formatTimeOnly(schedule.start_time)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Tugash</span>
              <span className="font-medium tabular-nums">
                {formatTimeOnly(schedule.end_time)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Imkoniyat</span>
              <span className="font-medium tabular-nums">
                {schedule.grace_minutes} daq.
              </span>
            </div>
          </div>
        ) : (
          <Button variant="outline" size="sm" className="w-full" onClick={openAssign}>
            <Plus className="size-4" aria-hidden />
            Jadval tayinlash
          </Button>
        )}
      </div>

      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Jadval tayinlash</DialogTitle>
            <DialogDescription>
              Mavjud jadvallardan birini tanlang. Yangi jadval yaratish uchun
              "Ish jadvallari" sahifasiga o'ting.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleAssign}>
            <div className="max-h-64 space-y-1 overflow-y-auto rounded-md border p-2">
              {availableSchedules.length === 0 ? (
                <p className="py-3 text-center text-sm text-muted-foreground">
                  Hozircha jadvallar yo'q. Avval "Ish jadvallari" sahifasida
                  yarating.
                </p>
              ) : (
                availableSchedules.map((s) => (
                  <Label
                    key={s.id}
                    className="flex cursor-pointer items-center justify-between gap-2 rounded px-2 py-2 hover:bg-accent"
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="schedule"
                        checked={selectedScheduleId === s.id}
                        onChange={() => setSelectedScheduleId(s.id)}
                      />
                      <span className="font-medium tabular-nums">
                        {formatTimeOnly(s.start_time)} – {formatTimeOnly(s.end_time)}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {s.grace_minutes} daq. · {s.employee_count} xodim
                    </span>
                  </Label>
                ))
              )}
            </div>

            {formError ? (
              <p role="alert" className="text-sm font-medium text-destructive">
                {formError}
              </p>
            ) : null}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAssignOpen(false)}>
                Bekor qilish
              </Button>
              <Button type="submit" disabled={submitting || !selectedScheduleId}>
                {submitting ? 'Saqlanmoqda…' : 'Tayinlash'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={confirmUnassign} onOpenChange={setConfirmUnassign}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Jadvaldan ajratilsinmi?</AlertDialogTitle>
            <AlertDialogDescription>
              Xodim ushbu ish jadvalidan ajratiladi. Jadval shabloni o'chmaydi.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleUnassign}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Ajratish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

const DAILY_LIMIT = 20

function localDateKey(value: string) {
  const d = new Date(value)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function AttendanceSection({ employeeId }: { employeeId: number }) {
  const [days, setDays] = useState<DailyAttendance[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [daysLoading, setDaysLoading] = useState(true)
  const [daysError, setDaysError] = useState<Error | null>(null)

  const [events, setEvents] = useState<Attendance[]>([])
  const [eventsLoading, setEventsLoading] = useState(true)

  const [expandedDate, setExpandedDate] = useState<string | null>(null)

  const loadDays = useCallback(async () => {
    try {
      setDaysLoading(true)
      setDaysError(null)
      const res = await dailyAttendanceService.list({
        employee_id: employeeId,
        limit: DAILY_LIMIT,
        page,
      })
      setDays(res.items)
      setTotal(res.total)
    } catch (err) {
      setDaysError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setDaysLoading(false)
    }
  }, [employeeId, page])

  const loadEvents = useCallback(async () => {
    try {
      setEventsLoading(true)
      const res = await attendanceService.list({
        employee_id: employeeId,
        limit: 200,
      })
      setEvents(res.events)
    } catch {
      // tolerate — segments are secondary info
      setEvents([])
    } finally {
      setEventsLoading(false)
    }
  }, [employeeId])

  useEffect(() => {
    loadDays()
  }, [loadDays])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const eventsByDate = events.reduce<Record<string, Attendance[]>>((acc, ev) => {
    const key = localDateKey(ev.enter_time ?? ev.exit_time ?? '')
    if (!key) return acc
    if (!acc[key]) acc[key] = []
    acc[key].push(ev)
    return acc
  }, {})

  for (const key of Object.keys(eventsByDate)) {
    eventsByDate[key].sort(
      (a, b) =>
        new Date(a.enter_time ?? a.exit_time ?? 0).getTime() -
        new Date(b.enter_time ?? b.exit_time ?? 0).getTime(),
    )
  }

  const toggleExpand = (date: string) => {
    setExpandedDate((prev) => (prev === date ? null : date))
  }

  if (daysError) {
    return <ErrorState onRetry={loadDays} />
  }

  if (daysLoading && days.length === 0) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (days.length === 0) {
    return (
      <EmptyState
        title="Davomat yo'q"
        description="Hozircha bu xodim uchun yozuvlar mavjud emas."
      />
    )
  }

  return (
    <div className="space-y-3">
      <Card className="overflow-hidden p-0">
        <ScrollableTable>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10"></TableHead>
                <TableHead>Sana</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Kelish</TableHead>
                <TableHead>Ketish</TableHead>
                <TableHead className="text-right">Soat</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {days.map((item) => {
                const isOpen = expandedDate === item.date
                const dayEvents = eventsByDate[item.date] ?? []
                return (
                  <DayRows
                    key={item.id}
                    item={item}
                    isOpen={isOpen}
                    dayEvents={dayEvents}
                    eventsLoading={eventsLoading}
                    onToggle={() => toggleExpand(item.date)}
                  />
                )
              })}
            </TableBody>
          </Table>
        </ScrollableTable>
        <Pagination
          page={page}
          limit={DAILY_LIMIT}
          total={total}
          onPageChange={setPage}
        />
      </Card>
    </div>
  )
}

function DayRows({
  item,
  isOpen,
  dayEvents,
  eventsLoading,
  onToggle,
}: {
  item: DailyAttendance
  isOpen: boolean
  dayEvents: Attendance[]
  eventsLoading: boolean
  onToggle: () => void
}) {
  const hasAnyImage = dayEvents.some(
    (e) => e.enter_image_path || e.exit_image_path,
  )

  return (
    <>
      <TableRow className="cursor-pointer" onClick={onToggle}>
        <TableCell>
          {isOpen ? (
            <ChevronDown className="size-4 text-muted-foreground" aria-hidden />
          ) : (
            <ChevronRight className="size-4 text-muted-foreground" aria-hidden />
          )}
        </TableCell>
        <TableCell className="tabular-nums">
          {formatShortDate(item.date)}
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
      {isOpen ? (
        <TableRow className="bg-muted/30 hover:bg-muted/30">
          <TableCell colSpan={6} className="p-0">
            <div className="px-4 py-3">
              {eventsLoading ? (
                <Skeleton className="h-16 w-full" />
              ) : dayEvents.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Ushbu kun uchun batafsil yozuvlar mavjud emas.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="h-9">Kirish</TableHead>
                      <TableHead className="h-9">Chiqish</TableHead>
                      <TableHead className="h-9">Kamera</TableHead>
                      <TableHead className="h-9 text-right">Soat</TableHead>
                      {hasAnyImage ? (
                        <TableHead className="h-9 text-right">Foto</TableHead>
                      ) : null}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dayEvents.map((ev) => {
                      const enterUrl = buildImageUrl(ev.enter_image_path)
                      const exitUrl = buildImageUrl(ev.exit_image_path)
                      return (
                        <TableRow key={ev.id}>
                          <TableCell className="tabular-nums">
                            {formatTimeOnly(ev.enter_time)}
                          </TableCell>
                          <TableCell className="tabular-nums">
                            {formatTimeOnly(ev.exit_time ?? null)}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            <span className="inline-flex items-center gap-1.5">
                              <CameraIcon className="size-3.5" aria-hidden />
                              #{ev.camera_id}
                            </span>
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {ev.working_hours != null
                              ? ev.working_hours.toFixed(2)
                              : '—'}
                          </TableCell>
                          {hasAnyImage ? (
                            <TableCell className="text-right">
                              <div className="inline-flex items-center justify-end gap-1.5">
                                {enterUrl ? (
                                  <img
                                    src={enterUrl}
                                    alt=""
                                    className="size-9 rounded-md object-cover"
                                  />
                                ) : null}
                                {exitUrl ? (
                                  <img
                                    src={exitUrl}
                                    alt=""
                                    className="size-9 rounded-md object-cover"
                                  />
                                ) : null}
                              </div>
                            </TableCell>
                          ) : null}
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              )}
            </div>
          </TableCell>
        </TableRow>
      ) : null}
    </>
  )
}
