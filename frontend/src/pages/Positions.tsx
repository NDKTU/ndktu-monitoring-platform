import { Briefcase, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { useState } from 'react'
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
import { positionsService } from '@/services/positions'
import type { Position, PositionCreateInput, PositionListParams } from '@/types/position'

const EMPTY_FORM: PositionCreateInput = {
  name: '',
}

export default function PositionsPage() {
  const {
    items: positions,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<Position, PositionListParams>({
    fetcher: positionsService.list,
    itemsKey: 'positions',
    initialParams: { page: 1, limit: 10 },
  })

  const [search, setSearch] = useState('')

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
  const [editing, setEditing] = useState<Position | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<PositionCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<Position | null>(null)

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

  const openEdit = (position: Position) => {
    setEditing(position)
    setForm({
      name: position.name,
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
        await positionsService.update(editing.id, cleaned)
      } else {
        await positionsService.create(cleaned)
      }
      setDialogOpen(false)
      resetForm()
      await refetch()
    } catch {
      setSubmitError(
        editing
          ? "Lavozimni yangilab bo'lmadi. Lavozim nomi band bo'lishi mumkin."
          : "Lavozimni yaratib bo'lmadi. Lavozim nomi band bo'lishi mumkin.",
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await positionsService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete position', err)
    }
  }

  return (
    <>
      <PageHeader
        title="Lavozimlar"
        description="Xodimlarning lavozimlari ro'yxatini boshqarish"
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" aria-hidden />
            Lavozim qo‘shish
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
            <Label htmlFor="positions-search" className="sr-only">
              Lavozim nomi bo‘yicha qidirish
            </Label>
            <Input
              id="positions-search"
              type="search"
              value={search}
              onChange={(e) => applyFilters({ search: e.target.value })}
              placeholder="Lavozim nomi bo‘yicha…"
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
        ) : positions.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Briefcase}
              title="Lavozimlar topilmadi"
              description="Qidiruv shartlarini o‘zgartiring yoki yangi lavozim qo‘shing."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nomi</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead className="w-24 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {positions.map((pos) => (
                    <TableRow key={pos.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="grid size-8 place-items-center rounded-full bg-muted text-muted-foreground">
                            <Briefcase className="size-4" aria-hidden />
                          </div>
                          <span className="font-medium">{pos.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        #{pos.id}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label={`${pos.name} lavozimini tahrirlash`}
                            onClick={() => openEdit(pos)}
                          >
                            <Pencil className="size-4" aria-hidden />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            aria-label={`${pos.name} lavozimini o‘chirish`}
                            onClick={() => setToDelete(pos)}
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
              {isEditing ? 'Lavozimni tahrirlash' : 'Yangi lavozim'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Lavozim nomini yangilang.'
                : 'Tizim xodimlari uchun yangi lavozim yarating.'}
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="name">Lavozim nomi</Label>
              <Input
                id="name"
                required
                value={form.name}
                onChange={(e) =>
                  setForm({ ...form, name: e.target.value })
                }
                placeholder="Mutaxassis"
                autoComplete="off"
              />
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
            <AlertDialogTitle>Lavozimni o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete?.name} lavozimini o‘chirmoqchimisiz? Bu lavozimga ega bo'lgan xodimlar uchun lavozim bo'sh bo'lib qoladi.
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
