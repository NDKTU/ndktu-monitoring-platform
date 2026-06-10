import { ArrowLeft, Clock, Pencil, Trash2, UserPlus } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { EmployeeMultiSelect } from '@/components/shared/EmployeeMultiSelect'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { Pagination } from '@/components/shared/Pagination'
import { ScrollableTable } from '@/components/shared/ScrollableTable'
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
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
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
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { TimeInput24 } from '@/components/ui/time-input-24'
import { formatTimeOnly, parseTimeInput } from '@/lib/time'
import { employeesService } from '@/services/employees'
import { workSchedulesService } from '@/services/workSchedules'
import type { Employee } from '@/types/employee'
import type {
  WorkSchedule,
  WorkScheduleEmployee,
} from '@/types/workSchedule'

const DEFAULT_LIMIT = 10

export default function WorkScheduleDetailPage() {
  const navigate = useNavigate()
  const { id: idParam } = useParams<{ id: string }>()
  const scheduleId = Number(idParam)

  const [schedule, setSchedule] = useState<WorkSchedule | null>(null)
  const [scheduleLoading, setScheduleLoading] = useState(true)
  const [scheduleError, setScheduleError] = useState<Error | null>(null)

  const [employees, setEmployees] = useState<WorkScheduleEmployee[]>([])
  const [employeesTotal, setEmployeesTotal] = useState(0)
  const [employeesPage, setEmployeesPage] = useState(1)
  const [employeesLimit, setEmployeesLimit] = useState(DEFAULT_LIMIT)
  const [employeesLoading, setEmployeesLoading] = useState(true)
  const [employeesError, setEmployeesError] = useState<Error | null>(null)

  const fetchSchedule = useCallback(async () => {
    if (!Number.isFinite(scheduleId)) return
    try {
      setScheduleLoading(true)
      setScheduleError(null)
      const data = await workSchedulesService.get(scheduleId)
      setSchedule(data)
    } catch (err) {
      setScheduleError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setScheduleLoading(false)
    }
  }, [scheduleId])

  const fetchEmployees = useCallback(async () => {
    if (!Number.isFinite(scheduleId)) return
    try {
      setEmployeesLoading(true)
      setEmployeesError(null)
      const res = await workSchedulesService.listEmployees(scheduleId, {
        page: employeesPage,
        limit: employeesLimit,
      })
      setEmployees(res.employees)
      setEmployeesTotal(res.total)
    } catch (err) {
      setEmployeesError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setEmployeesLoading(false)
    }
  }, [scheduleId, employeesPage, employeesLimit])

  useEffect(() => {
    fetchSchedule()
  }, [fetchSchedule])

  useEffect(() => {
    fetchEmployees()
  }, [fetchEmployees])

  const refreshAll = useCallback(async () => {
    await Promise.all([fetchSchedule(), fetchEmployees()])
  }, [fetchSchedule, fetchEmployees])

  const [editOpen, setEditOpen] = useState(false)
  const [editForm, setEditForm] = useState({
    start_time: '09:00',
    end_time: '18:00',
    grace_minutes: 0,
  })
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)

  const openEdit = () => {
    if (!schedule) return
    setEditForm({
      start_time: schedule.start_time.slice(0, 5),
      end_time: schedule.end_time.slice(0, 5),
      grace_minutes: schedule.grace_minutes,
    })
    setEditError(null)
    setEditOpen(true)
  }

  const submitEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!schedule) return
    try {
      setEditSubmitting(true)
      setEditError(null)
      await workSchedulesService.update(schedule.id, {
        start_time: parseTimeInput(editForm.start_time),
        end_time: parseTimeInput(editForm.end_time),
        grace_minutes: editForm.grace_minutes,
      })
      setEditOpen(false)
      await fetchSchedule()
    } catch {
      setEditError(
        "Vaqtni yangilab bo'lmadi. Bunday vaqtdagi jadval allaqachon mavjud bo'lishi mumkin.",
      )
    } finally {
      setEditSubmitting(false)
    }
  }

  const [assignOpen, setAssignOpen] = useState(false)
  const [allEmployees, setAllEmployees] = useState<Employee[]>([])
  const [allEmployeesLoaded, setAllEmployeesLoaded] = useState(false)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [assignSubmitting, setAssignSubmitting] = useState(false)
  const [assignError, setAssignError] = useState<string | null>(null)

  const openAssign = async () => {
    setSelectedIds([])
    setAssignError(null)
    setAssignOpen(true)
    if (!allEmployeesLoaded) {
      try {
        const res = await employeesService.list({ limit: 500 })
        setAllEmployees(res.employees)
        setAllEmployeesLoaded(true)
      } catch {
        setAssignError("Xodimlar ro'yxatini yuklab bo'lmadi.")
      }
    }
  }

  const submitAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!schedule || selectedIds.length === 0) {
      setAssignError('Kamida bitta xodimni tanlang.')
      return
    }
    try {
      setAssignSubmitting(true)
      setAssignError(null)
      await workSchedulesService.assignEmployees(schedule.id, {
        employee_ids: selectedIds,
      })
      setAssignOpen(false)
      await refreshAll()
    } catch {
      setAssignError("Xodimlarni qo'shib bo'lmadi.")
    } finally {
      setAssignSubmitting(false)
    }
  }

  const [toUnassign, setToUnassign] = useState<WorkScheduleEmployee | null>(null)
  const handleUnassign = async () => {
    if (!schedule || !toUnassign) return
    try {
      await workSchedulesService.unassignEmployees(schedule.id, {
        employee_ids: [toUnassign.id],
      })
      setToUnassign(null)
      await refreshAll()
    } catch (err) {
      console.error('Failed to unassign', err)
    }
  }

  const [confirmDeleteSchedule, setConfirmDeleteSchedule] = useState(false)
  const deleteSchedule = async () => {
    if (!schedule) return
    try {
      await workSchedulesService.remove(schedule.id)
      navigate('/work-schedules')
    } catch (err) {
      console.error('Failed to delete schedule', err)
    }
  }

  const candidates = allEmployees.filter(
    (e) => !e.department?.work_schedule_id || e.department.work_schedule_id !== scheduleId,
  )

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/work-schedules')}
        >
          <ArrowLeft className="size-4" aria-hidden />
          Ortga
        </Button>
      </div>

      {scheduleError ? (
        <Card>
          <div className="p-6">
            <ErrorState onRetry={fetchSchedule} />
          </div>
        </Card>
      ) : scheduleLoading || !schedule ? (
        <Card>
          <div className="space-y-3 p-6">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-5 w-40" />
          </div>
        </Card>
      ) : (
        <Card>
          <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-2xl font-semibold tracking-tight tabular-nums">
                <Clock className="size-6 text-muted-foreground" aria-hidden />
                {formatTimeOnly(schedule.start_time)} – {formatTimeOnly(schedule.end_time)}
              </div>
              <p className="text-sm text-muted-foreground">
                Kechikish imkoniyati: {schedule.grace_minutes} daq. ·{' '}
                {schedule.employee_count} xodim biriktirilgan
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={openEdit}>
                <Pencil className="size-4" aria-hidden />
                Vaqtni o'zgartirish
              </Button>
              <Button onClick={openAssign}>
                <UserPlus className="size-4" aria-hidden />
                Xodim qo'shish
              </Button>
              <Button
                variant="outline"
                className="text-destructive hover:text-destructive"
                onClick={() => setConfirmDeleteSchedule(true)}
              >
                <Trash2 className="size-4" aria-hidden />
                Jadvalni o'chirish
              </Button>
            </div>
          </div>
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        {employeesError ? (
          <div className="p-6">
            <ErrorState onRetry={fetchEmployees} />
          </div>
        ) : employeesLoading ? (
          <div className="space-y-2 p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : employees.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={UserPlus}
              title="Xodimlar yo'q"
              description={`Ushbu jadvalga hali hech kim biriktirilmagan. "Xodim qo'shish" tugmasini bosing.`}
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>F.I.Sh.</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.map((emp) => (
                    <TableRow key={emp.id}>
                      <TableCell className="font-medium">{emp.full_name}</TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            aria-label="Ajratish"
                            onClick={() => setToUnassign(emp)}
                          >
                            <Trash2 className="size-4" aria-hidden />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollableTable>
            <Pagination
              page={employeesPage}
              limit={employeesLimit}
              total={employeesTotal}
              onPageChange={setEmployeesPage}
              onLimitChange={(l) => {
                setEmployeesLimit(l)
                setEmployeesPage(1)
              }}
            />
          </>
        )}
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Vaqtni o'zgartirish</DialogTitle>
            <DialogDescription>
              O'zgarish ushbu jadvalga biriktirilgan barcha xodimlarga taalluqli
              bo'ladi.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={submitEdit}>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="edit-start">Boshlanish</Label>
                <TimeInput24
                  id="edit-start"
                  required
                  value={editForm.start_time}
                  onChange={(v) => setEditForm({ ...editForm, start_time: v })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-end">Tugash</Label>
                <TimeInput24
                  id="edit-end"
                  required
                  value={editForm.end_time}
                  onChange={(v) => setEditForm({ ...editForm, end_time: v })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-grace">Kechikish imkoniyati (daqiqa)</Label>
              <Input
                id="edit-grace"
                type="number"
                min={0}
                max={120}
                value={editForm.grace_minutes}
                onChange={(e) =>
                  setEditForm({
                    ...editForm,
                    grace_minutes: Math.max(0, Number(e.target.value) || 0),
                  })
                }
              />
            </div>

            {editError ? (
              <p role="alert" className="text-sm font-medium text-destructive">
                {editError}
              </p>
            ) : null}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditOpen(false)}>
                Bekor qilish
              </Button>
              <Button type="submit" disabled={editSubmitting}>
                {editSubmitting ? 'Saqlanmoqda…' : 'Saqlash'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xodim qo'shish</DialogTitle>
            <DialogDescription>
              Tanlangan xodimlar ushbu jadvalga biriktiriladi. Agar xodimda
              boshqa jadval bo'lsa, u qayta yoziladi.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={submitAssign}>
            <EmployeeMultiSelect
              employees={candidates}
              value={selectedIds}
              onChange={setSelectedIds}
            />

            {assignError ? (
              <p role="alert" className="text-sm font-medium text-destructive">
                {assignError}
              </p>
            ) : null}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAssignOpen(false)}>
                Bekor qilish
              </Button>
              <Button type="submit" disabled={assignSubmitting || selectedIds.length === 0}>
                {assignSubmitting ? 'Saqlanmoqda…' : 'Biriktirish'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={!!toUnassign}
        onOpenChange={(next) => !next && setToUnassign(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xodim ajratilsinmi?</AlertDialogTitle>
            <AlertDialogDescription>
              {toUnassign ? `${toUnassign.full_name} ushbu jadvaldan ajratiladi.` : null}
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

      <AlertDialog
        open={confirmDeleteSchedule}
        onOpenChange={setConfirmDeleteSchedule}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Jadvalni o'chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {schedule && schedule.employee_count > 0
                ? `Jadval o'chiriladi. ${schedule.employee_count} xodim jadvalsiz qoladi.`
                : "Jadval o'chiriladi. Davom etamizmi?"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteSchedule}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              O'chirish
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

    </>
  )
}
