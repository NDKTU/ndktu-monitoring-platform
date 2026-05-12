import { Plus, Search, ShieldCheck, Trash2, User as UserIcon } from 'lucide-react'
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
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
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
import { usersService } from '@/services/users'
import type { User, UserCreateInput, UserListParams } from '@/types/user'

type StatusFilter = 'all' | 'true' | 'false'

const EMPTY_FORM: UserCreateInput = {
  username: '',
  password: '',
  is_active: true,
  is_superuser: false,
}

export default function UsersPage() {
  const {
    items: users,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<User, UserListParams>({
    fetcher: usersService.list,
    itemsKey: 'users',
    initialParams: { page: 1, limit: 10 },
  })

  const [search, setSearch] = useState('')
  const [active, setActive] = useState<StatusFilter>('all')
  const [superuser, setSuperuser] = useState<StatusFilter>('all')

  const applyFilters = (
    next: Partial<{
      search: string
      active: StatusFilter
      superuser: StatusFilter
    }>,
  ) => {
    if (next.search !== undefined) setSearch(next.search)
    if (next.active !== undefined) setActive(next.active)
    if (next.superuser !== undefined) setSuperuser(next.superuser)

    setParams((prev) => {
      const s = next.search ?? search
      const a = next.active ?? active
      const su = next.superuser ?? superuser
      return {
        ...prev,
        search: s || undefined,
        is_active: a === 'all' ? undefined : a === 'true',
        is_superuser: su === 'all' ? undefined : su === 'true',
      }
    })
  }

  const [createOpen, setCreateOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<UserCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<User | null>(null)

  const resetForm = () => {
    setForm(EMPTY_FORM)
    setSubmitError(null)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSubmitting(true)
      setSubmitError(null)
      await usersService.create(form)
      setCreateOpen(false)
      resetForm()
      await refetch()
    } catch {
      setSubmitError("Foydalanuvchini yaratib bo'lmadi. Qayta urinib ko‘ring.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await usersService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete user', err)
    }
  }

  return (
    <>
      <PageHeader
        title="Foydalanuvchilar"
        description="Tizim hisoblari va kirish huquqlarini boshqarish"
        actions={
          <Button
            onClick={() => {
              resetForm()
              setCreateOpen(true)
            }}
          >
            <Plus className="size-4" aria-hidden />
            Qo‘shish
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
            <Label htmlFor="users-search" className="sr-only">
              Foydalanuvchi nomi bo‘yicha qidirish
            </Label>
            <Input
              id="users-search"
              type="search"
              value={search}
              onChange={(e) => applyFilters({ search: e.target.value })}
              placeholder="Foydalanuvchi nomi bo‘yicha…"
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Select
              value={active}
              onValueChange={(v) => applyFilters({ active: v as StatusFilter })}
            >
              <SelectTrigger
                className="w-full sm:w-40"
                aria-label="Holat filtri"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha holatlar</SelectItem>
                <SelectItem value="true">Faol</SelectItem>
                <SelectItem value="false">Faol emas</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={superuser}
              onValueChange={(v) =>
                applyFilters({ superuser: v as StatusFilter })
              }
            >
              <SelectTrigger
                className="w-full sm:w-40"
                aria-label="Rol filtri"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha rollar</SelectItem>
                <SelectItem value="true">Admin</SelectItem>
                <SelectItem value="false">Oddiy</SelectItem>
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
        ) : users.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={UserIcon}
              title="Foydalanuvchilar topilmadi"
              description="Filtrni o‘zgartiring yoki yangi foydalanuvchi qo‘shing."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Foydalanuvchi</TableHead>
                    <TableHead>Holati</TableHead>
                    <TableHead>Roli</TableHead>
                    <TableHead className="w-16 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="grid size-8 place-items-center rounded-full bg-muted text-muted-foreground">
                            <UserIcon className="size-4" aria-hidden />
                          </div>
                          <span className="font-medium">{user.username}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'secondary' : 'outline'}>
                          {user.is_active ? 'Faol' : 'Faol emas'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.is_superuser ? (
                          <span className="inline-flex items-center gap-1.5 text-sm font-medium">
                            <ShieldCheck
                              className="size-4 text-emerald-500"
                              aria-hidden
                            />
                            Admin
                          </span>
                        ) : (
                          <span className="text-sm text-muted-foreground">
                            Oddiy
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            aria-label={`${user.username} foydalanuvchisini o‘chirish`}
                            onClick={() => setToDelete(user)}
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
        open={createOpen}
        onOpenChange={(next) => {
          setCreateOpen(next)
          if (!next) resetForm()
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yangi foydalanuvchi</DialogTitle>
            <DialogDescription>
              Tizim foydalanuvchisi uchun hisob yarating.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleCreate}>
            <div className="space-y-2">
              <Label htmlFor="username">Foydalanuvchi nomi</Label>
              <Input
                id="username"
                required
                value={form.username}
                onChange={(e) =>
                  setForm({ ...form, username: e.target.value })
                }
                placeholder="ali_valiev"
                autoComplete="off"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Parol</Label>
              <Input
                id="password"
                type="password"
                required
                value={form.password}
                onChange={(e) =>
                  setForm({ ...form, password: e.target.value })
                }
                autoComplete="new-password"
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="is_superuser"
                checked={form.is_superuser ?? false}
                onCheckedChange={(checked) =>
                  setForm({ ...form, is_superuser: checked === true })
                }
              />
              <Label htmlFor="is_superuser" className="cursor-pointer">
                Admin huquqlarini berish
              </Label>
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
                onClick={() => setCreateOpen(false)}
              >
                Bekor qilish
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Yaratilmoqda…' : 'Yaratish'}
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
            <AlertDialogTitle>Foydalanuvchini o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete?.username} hisobini o‘chirmoqchimisiz? Bu amal qaytarib
              bo‘lmaydi.
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
