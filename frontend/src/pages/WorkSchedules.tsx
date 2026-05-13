import { Clock, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { workSchedulesService } from '@/services/workSchedules'
import type {
  WorkSchedule,
  WorkScheduleListParams,
} from '@/types/workSchedule'

type FormState = {
  start_time: string
  end_time: string
  grace_minutes: number
}

const EMPTY_FORM: FormState = {
  start_time: '09:00',
  end_time: '18:00',
  grace_minutes: 0,
}

export default function WorkSchedulesPage() {
  const navigate = useNavigate()
  const {
    items: schedules,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    refetch,
  } = usePagedList<WorkSchedule, WorkScheduleListParams>({
    fetcher: workSchedulesService.list,
    itemsKey: 'schedules',
    initialParams: { page: 1, limit: 10 },
  })

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<WorkSchedule | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [toDelete, setToDelete] = useState<WorkSchedule | null>(null)

  const openCreate = () => {
    setForm(EMPTY_FORM)
    setFormError(null)
    setEditing(null)
    setDialogOpen(true)
  }

  const openEdit = (schedule: WorkSchedule) => {
    setForm({
      start_time: schedule.start_time.slice(0, 5),
      end_time: schedule.end_time.slice(0, 5),
      grace_minutes: schedule.grace_minutes,
    })
    setFormError(null)
    setEditing(schedule)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      start_time: parseTimeInput(form.start_time),
      end_time: parseTimeInput(form.end_time),
      grace_minutes: form.grace_minutes,
    }

    try {
      setSubmitting(true)
      setFormError(null)
      if (editing) {
        await workSchedulesService.update(editing.id, payload)
      } else {
        await workSchedulesService.create(payload)
      }
      setDialogOpen(false)
      setEditing(null)
      await refetch()
    } catch {
      setFormError(
        editing
          ? "Jadvalni yangilab bo'lmadi. Bunday vaqtdagi jadval allaqachon bo'lishi mumkin."
          : "Jadval yaratilmadi. Bunday vaqtdagi jadval allaqachon bo'lishi mumkin.",
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

  const goToDetail = (schedule: WorkSchedule) => {
    navigate(`/work-schedules/${schedule.id}`)
  }

  const stop = (e: React.MouseEvent) => e.stopPropagation()

  return (
    <>
      <PageHeader
        title="Ish jadvallari"
        description="Ish vaqtlari shabloni va ularga biriktirilgan xodimlar soni"
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Yangi jadval
          </Button>
        }
      />

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
              description="Birinchi ish jadvalini yarating va keyin unga xodimlarni biriktiring."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Boshlanish</TableHead>
                    <TableHead>Tugash</TableHead>
                    <TableHead>Imkoniyat</TableHead>
                    <TableHead>Xodimlar soni</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedules.map((schedule) => (
                    <TableRow
                      key={schedule.id}
                      onClick={() => goToDetail(schedule)}
                      className="cursor-pointer"
                    >
                      <TableCell className="tabular-nums font-medium">
                        {formatTimeOnly(schedule.start_time)}
                      </TableCell>
                      <TableCell className="tabular-nums">
                        {formatTimeOnly(schedule.end_time)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {schedule.grace_minutes} daq.
                      </TableCell>
                      <TableCell>{schedule.employee_count}</TableCell>
                      <TableCell>
                        <div
                          className="flex items-center justify-end gap-1"
                          onClick={stop}
                        >
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
                            aria-label="O'chirish"
                            onClick={() => setToDelete(schedule)}
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
        open={dialogOpen}
        onOpenChange={(next) => {
          setDialogOpen(next)
          if (!next) setEditing(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editing ? 'Jadvalni tahrirlash' : 'Yangi ish jadvali'}
            </DialogTitle>
            <DialogDescription>
              {editing
                ? "Vaqtlar o'zgarishi shu jadvalga biriktirilgan barcha xodimlarga taalluqli bo'ladi."
                : "Yangi shablon yarating. Xodimlarni keyinroq detallar sahifasida biriktirasiz."}
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
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
                onClick={() => setDialogOpen(false)}
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
            <AlertDialogTitle>Jadvalni o'chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete && toDelete.employee_count > 0
                ? `Ushbu jadvalga ${toDelete.employee_count} xodim biriktirilgan. O'chirilgandan keyin ular jadvalsiz qoladi.`
                : "Jadval o'chiriladi. Davom etamizmi?"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Bekor qilish</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
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
