import { Building2, Pencil, Plus, Search, Trash2 } from 'lucide-react'
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
import { trimFormStrings } from '@/lib/validation'
import { departmentsService } from '@/services/departments'
import { workSchedulesService } from '@/services/workSchedules'
import type { Department, DepartmentCreateInput, DepartmentListParams } from '@/types/department'
import type { WorkSchedule } from '@/types/workSchedule'

const EMPTY_FORM: DepartmentCreateInput = {
  name: '',
  work_schedule_id: null,
}

export default function DepartmentsPage() {
  const {
    items: departments,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<Department, DepartmentListParams>({
    fetcher: departmentsService.list,
    itemsKey: 'departments',
    initialParams: { page: 1, limit: 10 },
  })

  const [search, setSearch] = useState('')
  const [schedules, setSchedules] = useState<WorkSchedule[]>([])

  const applyFilters = (next: Partial<{ search: string }>) => {
    if (next.search !== undefined) setSearch(next.search)

    setParams((prev) => {
      const s = next.search ?? search
      return {
        ...prev,
        search: s || undefined,
      }
    })
  }

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Department | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<DepartmentCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<Department | null>(null)

  const isEditing = editing !== null

  useEffect(() => {
    if (dialogOpen) {
      workSchedulesService
        .list({ limit: 100 })
        .then((res) => setSchedules(res.schedules))
        .catch(console.error)
    }
  }, [dialogOpen])

  const resetForm = () => {
    setForm(EMPTY_FORM)
    setSubmitError(null)
    setEditing(null)
  }

  const openCreate = () => {
    resetForm()
    setDialogOpen(true)
  }

  const openEdit = (dept: Department) => {
    setEditing(dept)
    setForm({
      name: dept.name,
      work_schedule_id: dept.work_schedule_id ?? null,
    })
    setSubmitError(null)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleaned = trimFormStrings(form)
    if (!cleaned.name.trim()) return

    try {
      setSubmitting(true)
      setSubmitError(null)
      setForm(cleaned)
      if (editing) {
        await departmentsService.update(editing.id, cleaned)
      } else {
        await departmentsService.create(cleaned)
      }
      setDialogOpen(false)
      resetForm()
      await refetch()
    } catch {
      setSubmitError(
        editing
          ? "Bo'limni yangilab bo'lmadi. Bo'lim nomi band bo'lishi mumkin."
          : "Bo'limni yaratib bo'lmadi. Bo'lim nomi band bo'lishi mumkin.",
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await departmentsService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete department', err)
    }
  }

  return (
    <>
      <PageHeader
        title="Bo'limlar"
        description="Tashkilot bo'limlari ro'yxatini va ularga biriktirilgan ish grafiklarini boshqarish"
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Bo‘lim qo‘shish
          </Button>
        }
      />

      <Card>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative w-full sm:max-w-sm">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Label htmlFor="departments-search" className="sr-only">
              Bo'lim nomi bo‘yicha qidirish
            </Label>
            <Input
              id="departments-search"
              type="search"
              value={search}
              onChange={(e) => applyFilters({ search: e.target.value })}
              placeholder="Bo'lim nomi bo‘yicha…"
              className="pl-9"
            />
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
        ) : departments.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Building2}
              title="Bo'limlar topilmadi"
              description="Qidiruv shartlarini o‘zgartiring yoki yangi bo'lim qo‘shing."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nomi</TableHead>
                    <TableHead>Ish jadvali</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {departments.map((dept) => (
                    <TableRow key={dept.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="grid size-8 place-items-center rounded-full bg-muted text-muted-foreground">
                            <Building2 className="size-4" aria-hidden />
                          </div>
                          <span className="font-medium">{dept.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {dept.work_schedule ? (
                          <span className="font-mono text-muted-foreground">
                            {dept.work_schedule.start_time.substring(0, 5)} - {dept.work_schedule.end_time.substring(0, 5)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground italic">Belgilanmagan</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        #{dept.id}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label={`${dept.name} bo'limini tahrirlash`}
                            onClick={() => openEdit(dept)}
                          >
                            <Pencil className="size-4" aria-hidden />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            aria-label={`${dept.name} bo'limini o‘chirish`}
                            onClick={() => setToDelete(dept)}
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
          if (!next) resetForm()
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? "Bo'limni tahrirlash" : "Yangi bo'lim"}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Bo'lim ma'lumotlarini yangilang."
                : "Tizim xodimlari uchun yangi bo'lim yarating."}
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="name">Bo'lim nomi</Label>
              <Input
                id="name"
                required
                value={form.name}
                onChange={(e) =>
                  setForm({ ...form, name: e.target.value })
                }
                placeholder="Moliya bo'limi"
                autoComplete="off"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="work_schedule">Ish jadvali</Label>
              <Select
                value={form.work_schedule_id ? String(form.work_schedule_id) : 'none'}
                onValueChange={(val) =>
                  setForm({
                    ...form,
                    work_schedule_id: val === 'none' ? null : Number(val),
                  })
                }
              >
                <SelectTrigger id="work_schedule">
                  <SelectValue placeholder="Ish jadvalini tanlang" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Belgilanmagan (Jadvalsiz)</SelectItem>
                  {schedules.map((sched) => (
                    <SelectItem key={sched.id} value={String(sched.id)}>
                      {sched.start_time.substring(0, 5)} - {sched.end_time.substring(0, 5)} (Kechikish: {sched.grace_minutes} daqiqa)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {submitError ? (
              <p
                role="alert"
                className="text-sm font-medium text-destructive"
              >
                {submitError}
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
                  ? isEditing
                    ? 'Saqlanmoqda…'
                    : 'Yaratilmoqda…'
                  : isEditing
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
            <AlertDialogTitle>Bo'limni o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete?.name} bo'limini o‘chirmoqchimisiz? Bu bo'limga tegishli bo'lgan xodimlar uchun bo'lim bo'sh bo'lib qoladi.
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
