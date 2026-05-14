import {
  ContactRound,
  Pencil,
  Plus,
  Search,
  Trash2,
  UserCheck,
  UserX,
} from 'lucide-react'
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
import { Badge } from '@/components/ui/badge'
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
import { employeesService } from '@/services/employees'
import type {
  Employee,
  EmployeeCreateInput,
  EmployeeListParams,
} from '@/types/employee'

type WorkFilter = 'all' | 'true' | 'false'

const EMPTY_FORM: EmployeeCreateInput = {
  first_name: '',
  last_name: '',
  third_name: '',
  passport_series: '',
  jshir: '',
  in_work: false,
  position: '',
  department: '',
}

function getInitials(employee: Pick<Employee, 'first_name' | 'last_name'>) {
  return `${employee.last_name?.[0] ?? ''}${employee.first_name?.[0] ?? ''}`.toUpperCase()
}

function buildImageUrl(path?: string | null) {
  if (!path) return null
  const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  return `${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
}

export default function EmployeesPage() {
  const navigate = useNavigate()

  const {
    items: employees,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<Employee, EmployeeListParams>({
    fetcher: employeesService.list,
    itemsKey: 'employees',
    initialParams: { page: 1, limit: 10 },
  })

  const [search, setSearch] = useState('')
  const [work, setWork] = useState<WorkFilter>('all')

  const applyFilters = (
    next: Partial<{ search: string; work: WorkFilter }>,
  ) => {
    if (next.search !== undefined) setSearch(next.search)
    if (next.work !== undefined) setWork(next.work)
    setParams((prev) => {
      const s = next.search ?? search
      const w = next.work ?? work
      return {
        ...prev,
        search: s || undefined,
        in_work: w === 'all' ? undefined : w === 'true',
      }
    })
  }

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Employee | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<EmployeeCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<Employee | null>(null)

  const isEditing = editing !== null

  const resetForm = () => {
    setForm(EMPTY_FORM)
    setSubmitError(null)
    setEditing(null)
  }

  const openCreate = () => {
    resetForm()
    setDialogOpen(true)
  }

  const openEdit = (employee: Employee) => {
    setEditing(employee)
    setForm({
      first_name: employee.first_name,
      last_name: employee.last_name,
      third_name: employee.third_name ?? '',
      passport_series: employee.passport_series ?? '',
      jshir: employee.jshir,
      in_work: employee.in_work,
      position: employee.position ?? '',
      department: employee.department ?? '',
    })
    setSubmitError(null)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleaned = trimFormStrings(form)
    try {
      setSubmitting(true)
      setSubmitError(null)
      setForm(cleaned)
      if (editing) {
        await employeesService.update(editing.id, cleaned)
      } else {
        await employeesService.create(cleaned)
      }
      setDialogOpen(false)
      resetForm()
      await refetch()
    } catch {
      setSubmitError(
        editing
          ? "Xodimni yangilab bo'lmadi. Maydonlarni tekshiring."
          : "Xodimni yaratib bo'lmadi. Maydonlarni tekshiring.",
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await employeesService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete employee', err)
    }
  }

  return (
    <>
      <PageHeader
        title="Xodimlar"
        description="Kuzatuv ostidagi xodimlarning biometrik bazasi"
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Xodim qo‘shish
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
            <Label htmlFor="employee-search" className="sr-only">
              Ism yoki JSHIR bo‘yicha qidirish
            </Label>
            <Input
              id="employee-search"
              type="search"
              value={search}
              onChange={(e) => applyFilters({ search: e.target.value })}
              placeholder="Ism yoki JSHIR bo‘yicha…"
              className="pl-9"
            />
          </div>
          <Select
            value={work}
            onValueChange={(v) => applyFilters({ work: v as WorkFilter })}
          >
            <SelectTrigger
              className="w-full sm:w-44"
              aria-label="Ishda bo‘lish filtri"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Hammasi</SelectItem>
              <SelectItem value="true">Ish joyida</SelectItem>
              <SelectItem value="false">Yo‘q</SelectItem>
            </SelectContent>
          </Select>
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
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : employees.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={ContactRound}
              title="Xodimlar topilmadi"
              description="Filtrni o‘zgartiring yoki birinchi xodimni qo‘shing."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Xodim</TableHead>
                    <TableHead>JSHIR</TableHead>
                    <TableHead>Pasport</TableHead>
                    <TableHead>Holati</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {employees.map((employee) => {
                    const avatar = buildImageUrl(employee.image_path)
                    return (
                      <TableRow
                        key={employee.id}
                        className="cursor-pointer"
                        onClick={() => navigate(`/employees/${employee.id}`)}
                      >
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="grid size-9 place-items-center overflow-hidden rounded-full bg-muted text-xs font-semibold text-muted-foreground">
                              {avatar ? (
                                <img
                                  src={avatar}
                                  alt=""
                                  className="size-full object-cover"
                                />
                              ) : (
                                getInitials(employee)
                              )}
                            </div>
                            <div className="min-w-0">
                              <div className="truncate font-medium">
                                {employee.full_name}
                              </div>
                              {employee.third_name ? (
                                <div className="text-xs text-muted-foreground">
                                  ID #{employee.id}
                                </div>
                              ) : null}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm tabular-nums">
                          {employee.jshir}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {employee.passport_series || '—'}
                        </TableCell>
                        <TableCell>
                          {employee.in_work ? (
                            <Badge
                              variant="secondary"
                              className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                            >
                              <UserCheck className="size-3" aria-hidden />
                              Ishda
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              <UserX className="size-3" aria-hidden />
                              Yo‘q
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label={`${employee.full_name} ni tahrirlash`}
                              onClick={() => openEdit(employee)}
                            >
                              <Pencil className="size-4" aria-hidden />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive hover:text-destructive"
                              aria-label={`${employee.full_name} ni o‘chirish`}
                              onClick={() => setToDelete(employee)}
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
        open={dialogOpen}
        onOpenChange={(next) => {
          setDialogOpen(next)
          if (!next) resetForm()
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Xodimni tahrirlash' : 'Yangi xodim'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Xodim maʼlumotlarini yangilang.'
                : 'Xodimning biometrik ma’lumotlarini kiriting.'}
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="last_name">Familiya</Label>
                <Input
                  id="last_name"
                  required
                  value={form.last_name}
                  onChange={(e) =>
                    setForm({ ...form, last_name: e.target.value })
                  }
                  placeholder="Valiyev"
                  autoComplete="off"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="first_name">Ism</Label>
                <Input
                  id="first_name"
                  required
                  value={form.first_name}
                  onChange={(e) =>
                    setForm({ ...form, first_name: e.target.value })
                  }
                  placeholder="Ali"
                  autoComplete="off"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="third_name">Otasining ismi</Label>
              <Input
                id="third_name"
                value={form.third_name ?? ''}
                onChange={(e) =>
                  setForm({ ...form, third_name: e.target.value })
                }
                placeholder="Akmal o‘g‘li"
                autoComplete="off"
              />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="jshir">JSHIR</Label>
                <Input
                  id="jshir"
                  required
                  value={form.jshir}
                  onChange={(e) => setForm({ ...form, jshir: e.target.value })}
                  placeholder="14 raqamli kod"
                  inputMode="numeric"
                  autoComplete="off"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="passport_series">Pasport seriyasi</Label>
                <Input
                  id="passport_series"
                  value={form.passport_series ?? ''}
                  onChange={(e) =>
                    setForm({ ...form, passport_series: e.target.value })
                  }
                  placeholder="AA1234567"
                  autoComplete="off"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="position">Lavozim</Label>
                <Input
                  id="position"
                  value={form.position ?? ''}
                  onChange={(e) =>
                    setForm({ ...form, position: e.target.value })
                  }
                  placeholder="Mutaxassis"
                  autoComplete="off"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="department">Bo'lim</Label>
                <Input
                  id="department"
                  value={form.department ?? ''}
                  onChange={(e) =>
                    setForm({ ...form, department: e.target.value })
                  }
                  placeholder="Kafedra / bo'lim"
                  autoComplete="off"
                />
              </div>
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
            <AlertDialogTitle>Xodimni o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete?.full_name} haqidagi ma’lumot o‘chiriladi. Davomat
              tarixi saqlanib qoladi, lekin bog‘liq xodim ko‘rsatilmaydi.
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
