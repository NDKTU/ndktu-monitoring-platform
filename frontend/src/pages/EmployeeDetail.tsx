import {
  ArrowLeft,
  Calendar,
  CalendarCheck,
  Camera as CameraIcon,
  Clock,
  ContactRound,
  ImageOff,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
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
import { Input } from '@/components/ui/input'
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
import { formatTimeOnly, parseTimeInput } from '@/lib/time'
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

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(LOCALE, {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

function formatShortDate(value: string) {
  return new Date(value).toLocaleDateString(LOCALE, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

function formatTime(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleTimeString(LOCALE, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
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

  const [events, setEvents] = useState<Attendance[]>([])
  const [eventsTotal, setEventsTotal] = useState(0)
  const [eventsLoading, setEventsLoading] = useState(true)
  const [eventsError, setEventsError] = useState<Error | null>(null)
  const [page, setPage] = useState(1)
  const limit = 20

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

  useEffect(() => {
    if (!Number.isFinite(employeeId)) return
    let cancelled = false
    setEventsLoading(true)
    attendanceService
      .list({ employee_id: employeeId, page, limit })
      .then((data) => {
        if (cancelled) return
        setEvents(data.events)
        setEventsTotal(data.total)
      })
      .catch((err: Error) => {
        if (!cancelled) setEventsError(err)
      })
      .finally(() => {
        if (!cancelled) setEventsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [employeeId, page])

  const groupedEvents = useMemo(() => {
    const groups = new Map<string, Attendance[]>()
    for (const event of events) {
      const key = new Date(event.enter_time).toISOString().slice(0, 10)
      const list = groups.get(key) ?? []
      list.push(event)
      groups.set(key, list)
    }
    return Array.from(groups.entries())
      .map(([date, list]) => ({
        date,
        events: list.sort(
          (a, b) =>
            new Date(b.enter_time).getTime() -
            new Date(a.enter_time).getTime(),
        ),
      }))
      .sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
      )
  }, [events])

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
                <span className="text-muted-foreground">Voqealar</span>
                <span className="font-medium tabular-nums">{eventsTotal}</span>
              </div>
            </CardContent>
            <Separator />
            <CardContent className="pt-4">
              <ScheduleSection employeeId={employee.id} />
            </CardContent>
          </Card>

          <div className="space-y-8">
            <section className="space-y-5">
              <div className="flex items-center gap-2">
                <Calendar
                  className="size-4 text-muted-foreground"
                  aria-hidden
                />
                <h2 className="text-lg font-semibold">Davomat tarixi</h2>
              </div>

              {eventsError ? (
                <ErrorState onRetry={() => setPage((p) => p)} />
              ) : eventsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-24 w-full" />
                  ))}
                </div>
              ) : groupedEvents.length === 0 ? (
                <EmptyState
                  title="Voqealar yo‘q"
                  description="Hozircha bu xodim uchun yozuvlar mavjud emas."
                />
              ) : (
                <>
                  <div className="space-y-5">
                    {groupedEvents.map(({ date, events: dayEvents }) => (
                      <section key={date} className="space-y-3">
                        <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          {formatDate(date)}
                        </h3>
                        <div className="space-y-2">
                          {dayEvents.map((event) => (
                            <Card key={event.id}>
                              <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_1fr_auto]">
                                <AttendanceSlot
                                  kind="enter"
                                  time={event.enter_time}
                                  imageUrl={buildImageUrl(event.enter_image_path)}
                                />
                                <AttendanceSlot
                                  kind="exit"
                                  time={event.exit_time}
                                  imageUrl={buildImageUrl(event.exit_image_path)}
                                />
                                <div className="flex flex-col gap-1 self-start text-sm text-muted-foreground sm:items-end sm:self-center">
                                  <div className="flex items-center gap-2">
                                    <CameraIcon className="size-4" aria-hidden />
                                    <span>Kamera #{event.camera_id}</span>
                                  </div>
                                  {event.working_hours != null ? (
                                    <span className="tabular-nums text-xs">
                                      {event.working_hours.toFixed(2)} soat
                                    </span>
                                  ) : null}
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </section>
                    ))}
                  </div>

                  <Pagination
                    page={page}
                    limit={limit}
                    total={eventsTotal}
                    onPageChange={setPage}
                  />
                </>
              )}
            </section>

            <section className="space-y-5">
              <div className="flex items-center gap-2">
                <CalendarCheck
                  className="size-4 text-muted-foreground"
                  aria-hidden
                />
                <h2 className="text-lg font-semibold">Kunlik davomat</h2>
              </div>
              <DailySection employeeId={employee.id} />
            </section>
          </div>
        </div>
        </>
      )}
    </>
  )
}

function AttendanceSlot({
  kind,
  time,
  imageUrl,
}: {
  kind: 'enter' | 'exit'
  time?: string | null
  imageUrl: string | null
}) {
  const label = kind === 'enter' ? 'Kirish' : 'Chiqish'
  const iconColor =
    kind === 'enter' ? 'text-emerald-500' : 'text-destructive'

  return (
    <div className="flex items-center gap-3">
      <div className="grid size-12 place-items-center overflow-hidden rounded-md bg-muted text-muted-foreground">
        {imageUrl ? (
          <img src={imageUrl} alt="" className="size-full object-cover" />
        ) : (
          <ImageOff className="size-5" aria-hidden />
        )}
      </div>
      <div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock className={`size-3 ${iconColor}`} aria-hidden />
          {label}
        </div>
        <div className="text-sm font-medium tabular-nums">
          {formatTime(time)}
        </div>
      </div>
    </div>
  )
}

type ScheduleFormState = {
  start_time: string
  end_time: string
  grace_minutes: number
}

const EMPTY_SCHEDULE_FORM: ScheduleFormState = {
  start_time: '09:00',
  end_time: '18:00',
  grace_minutes: 0,
}

function ScheduleSection({ employeeId }: { employeeId: number }) {
  const [schedule, setSchedule] = useState<WorkSchedule | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [form, setForm] = useState<ScheduleFormState>(EMPTY_SCHEDULE_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const fetchSchedule = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await workSchedulesService.list({ employee_id: employeeId, limit: 1 })
      setSchedule(res.schedules[0] ?? null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setLoading(false)
    }
  }, [employeeId])

  useEffect(() => {
    fetchSchedule()
  }, [fetchSchedule])

  const openCreate = () => {
    setForm(EMPTY_SCHEDULE_FORM)
    setFormError(null)
    setDialogOpen(true)
  }

  const openEdit = () => {
    if (!schedule) return
    setForm({
      start_time: schedule.start_time.slice(0, 5),
      end_time: schedule.end_time.slice(0, 5),
      grace_minutes: schedule.grace_minutes,
    })
    setFormError(null)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSubmitting(true)
      setFormError(null)
      const payload = {
        start_time: parseTimeInput(form.start_time),
        end_time: parseTimeInput(form.end_time),
        grace_minutes: form.grace_minutes,
      }
      if (schedule) {
        await workSchedulesService.update(schedule.id, payload)
      } else {
        await workSchedulesService.create({ employee_id: employeeId, ...payload })
      }
      setDialogOpen(false)
      await fetchSchedule()
    } catch {
      setFormError("Jadvalni saqlab bo'lmadi.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!schedule) return
    try {
      await workSchedulesService.remove(schedule.id)
      setConfirmDelete(false)
      await fetchSchedule()
    } catch (err) {
      console.error('Failed to delete schedule', err)
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
                aria-label="Tahrirlash"
                onClick={openEdit}
              >
                <Pencil className="size-3.5" aria-hidden />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-7 text-destructive hover:text-destructive"
                aria-label="O‘chirish"
                onClick={() => setConfirmDelete(true)}
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
            Jadvalni yuklab bo‘lmadi
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
          <Button variant="outline" size="sm" className="w-full" onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Jadval qo‘shish
          </Button>
        )}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {schedule ? 'Jadvalni tahrirlash' : 'Ish jadvali'}
            </DialogTitle>
            <DialogDescription>
              Boshlanish va tugash vaqtini hamda kechikishga ruxsat daqiqalarini kiriting.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="emp-start_time">Boshlanish</Label>
                <Input
                  id="emp-start_time"
                  type="time"
                  required
                  value={form.start_time}
                  onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="emp-end_time">Tugash</Label>
                <Input
                  id="emp-end_time"
                  type="time"
                  required
                  value={form.end_time}
                  onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="emp-grace">Kechikish imkoniyati (daqiqa)</Label>
              <Input
                id="emp-grace"
                type="number"
                min={0}
                max={120}
                value={form.grace_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    grace_minutes: Math.max(0, Number(e.target.value) || 0),
                  })
                }
              />
            </div>

            {formError ? (
              <p role="alert" className="text-sm font-medium text-destructive">
                {formError}
              </p>
            ) : null}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Bekor qilish
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Saqlanmoqda…' : 'Saqlash'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Jadvalni o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              Ish jadvali o‘chiriladi. Davom etamizmi?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              O‘chirish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

function DailySection({ employeeId }: { employeeId: number }) {
  const [items, setItems] = useState<DailyAttendance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    dailyAttendanceService
      .list({ employee_id: employeeId, limit: 30, page: 1 })
      .then((res) => {
        if (!cancelled) setItems(res.items)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [employeeId])

  if (error) {
    return <ErrorState />
  }
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }
  if (items.length === 0) {
    return (
      <EmptyState
        title="Kunlik yozuvlar yo‘q"
        description="Hozircha bu xodim uchun kunlik davomat hisoblanmagan."
      />
    )
  }

  return (
    <Card className="overflow-hidden p-0">
      <ScrollableTable>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Sana</TableHead>
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
            ))}
          </TableBody>
        </Table>
      </ScrollableTable>
    </Card>
  )
}
