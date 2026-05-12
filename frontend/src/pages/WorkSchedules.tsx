import { Clock, Pencil, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { PageHeader } from '@/components/shared/PageHeader'
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
import { TimeInput24 } from '@/components/ui/time-input-24'
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
import { formatTimeOnly, parseTimeInput } from '@/lib/time'
import { employeesService } from '@/services/employees'
import { workSchedulesService } from '@/services/workSchedules'
import type { Employee } from '@/types/employee'
import type {
  WorkSchedule,
  WorkScheduleCreateInput,
  WorkScheduleListParams,
} from '@/types/workSchedule'

type FormState = {
  employee_id: number | null
  start_time: string
  end_time: string
  grace_minutes: number
}

const EMPTY_FORM: FormState = {
  employee_id: null,
  start_time: '09:00',
  end_time: '18:00',
  grace_minutes: 0,
}

export default function WorkSchedulesPage() {
  const {
    items: schedules,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<WorkSchedule, WorkScheduleListParams>({
    fetcher: workSchedulesService.list,
    itemsKey: 'schedules',
    initialParams: { page: 1, limit: 10 },
  })

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

  const employeeById = (id: number) =>
    employees.find((e) => e.id === id)

  const [filterEmployee, setFilterEmployee] = useState<string>('all')

  const onFilterChange = (value: string) => {
    setFilterEmployee(value)
    setParams((prev) => ({
      ...prev,
      employee_id: value === 'all' ? undefined : Number(value),
    }))
  }

  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<WorkSchedule | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [toDelete, setToDelete] = useState<WorkSchedule | null>(null)

  const openCreate = () => {
    setForm(EMPTY_FORM)
    setFormError(null)
    setEditing(null)
    setCreateOpen(true)
  }

  const openEdit = (schedule: WorkSchedule) => {
    setForm({
      employee_id: schedule.employee_id,
      start_time: schedule.start_time.slice(0, 5),
      end_time: schedule.end_time.slice(0, 5),
      grace_minutes: schedule.grace_minutes,
    })
    setFormError(null)
    setEditing(schedule)
    setCreateOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.employee_id) {
      setFormError('Xodimni tanlang.')
      return
    }
    try {
      setSubmitting(true)
      setFormError(null)
      const payload = {
        start_time: parseTimeInput(form.start_time),
        end_time: parseTimeInput(form.end_time),
        grace_minutes: form.grace_minutes,
      }
      if (editing) {
        await workSchedulesService.update(editing.id, payload)
      } else {
        const create: WorkScheduleCreateInput = {
          employee_id: form.employee_id,
          ...payload,
        }
        await workSchedulesService.create(create)
      }
      setCreateOpen(false)
      setEditing(null)
      await refetch()
    } catch {
      setFormError(
        editing
          ? "Jadvalni yangilab bo'lmadi."
          : "Jadval yaratilmadi. Ehtimol, bu xodim uchun jadval allaqachon mavjud.",
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await workSchedulesService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete schedule', err)
    }
  }

  return (
    <>
      <PageHeader
        title="Ish jadvallari"
        description="Xodimlarning ish soatlari va kechikish toleranti"
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Yangi jadval
          </Button>
        }
      />

      <Card>
        <Label htmlFor="schedule-employee-filter" className="sr-only">
          Xodim bo‘yicha filtr
        </Label>
        <Select value={filterEmployee} onValueChange={onFilterChange}>
          <SelectTrigger
            id="schedule-employee-filter"
            className="w-full sm:w-72"
            aria-label="Xodim filtri"
          >
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
      </Card>

      <Card className="overflow-hidden p-0">
        {error ? (
          <div className="p-6">
            <ErrorState onRetry={refetch} />
          </div>
        ) : loading ? (
          <div className="space-y-2 p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : schedules.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Clock}
              title="Jadvallar topilmadi"
              description="Yangi xodim uchun ish jadvali yarating."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Xodim</TableHead>
                    <TableHead>Boshlanish</TableHead>
                    <TableHead>Tugash</TableHead>
                    <TableHead>Imkoniyat</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedules.map((schedule) => {
                    const employee = employeeById(schedule.employee_id)
                    return (
                      <TableRow key={schedule.id}>
                        <TableCell>
                          {employee ? (
                            <span className="font-medium">
                              {employee.full_name}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">
                              #{schedule.employee_id}
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="tabular-nums">
                          {formatTimeOnly(schedule.start_time)}
                        </TableCell>
                        <TableCell className="tabular-nums">
                          {formatTimeOnly(schedule.end_time)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {schedule.grace_minutes} daq.
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="Tahrirlash"
                              onClick={() => openEdit(schedule)}
                            >
                              <Pencil className="size-4" aria-hidden />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive hover:text-destructive"
                              aria-label="O‘chirish"
                              onClick={() => setToDelete(schedule)}
                            >
                              <Trash2 className="size-4" aria-hidden />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
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

      <Dialog
        open={createOpen}
        onOpenChange={(next) => {
          setCreateOpen(next)
          if (!next) setEditing(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editing ? 'Jadvalni tahrirlash' : 'Yangi ish jadvali'}
            </DialogTitle>
            <DialogDescription>
              Ish boshlanish va tugash vaqtini hamda kechikishga ruxsat
              beriladigan daqiqalarni kiriting.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="schedule-employee">Xodim</Label>
              <Select
                value={form.employee_id ? String(form.employee_id) : ''}
                onValueChange={(v) =>
                  setForm({ ...form, employee_id: Number(v) })
                }
                disabled={!!editing}
              >
                <SelectTrigger id="schedule-employee">
                  <SelectValue placeholder="Xodimni tanlang" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((e) => (
                    <SelectItem key={e.id} value={String(e.id)}>
                      {e.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="start_time">Boshlanish</Label>
                <TimeInput24
                  id="start_time"
                  required
                  value={form.start_time}
                  onChange={(v) => setForm({ ...form, start_time: v })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_time">Tugash</Label>
                <TimeInput24
                  id="end_time"
                  required
                  value={form.end_time}
                  onChange={(v) => setForm({ ...form, end_time: v })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="grace_minutes">Kechikish imkoniyati (daqiqa)</Label>
              <Input
                id="grace_minutes"
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
              <p
                role="alert"
                className="text-sm font-medium text-destructive"
              >
                {formError}
              </p>
            ) : null}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                Bekor qilish
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting
                  ? 'Saqlanmoqda…'
                  : editing
                    ? 'Saqlash'
                    : 'Yaratish'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={!!toDelete}
        onOpenChange={(next) => !next && setToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Jadvalni o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              Ish jadvali o‘chirilsa, kunlik davomat statuslari hisoblanmaydi.
              Davom etamizmi?
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
