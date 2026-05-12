import {
  Camera as CameraIcon,
  CircleAlert,
  Plus,
  Power,
  PowerOff,
  Search,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Pagination } from '@/components/shared/Pagination'
import { ScrollableTable } from '@/components/shared/ScrollableTable'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { usePagedList } from '@/hooks/usePagedList'
import { camerasService } from '@/services/cameras'
import type {
  Camera,
  CameraCreateInput,
  CameraListParams,
} from '@/types/camera'

type DirectionFilter = 'all' | 'enter' | 'exit'
type ActiveFilter = 'all' | 'true' | 'false'

const EMPTY_FORM: CameraCreateInput = {
  device_ip: '',
  login: '',
  password: '',
  direction: 'enter',
  is_active: true,
}

export default function CamerasPage() {
  const {
    items: cameras,
    total,
    page,
    limit,
    loading,
    error,
    setPage,
    setLimit,
    setParams,
    refetch,
  } = usePagedList<Camera, CameraListParams>({
    fetcher: camerasService.list,
    itemsKey: 'cameras',
    initialParams: { page: 1, limit: 10 },
  })

  const [search, setSearch] = useState('')
  const [direction, setDirection] = useState<DirectionFilter>('all')
  const [active, setActive] = useState<ActiveFilter>('all')

  const applyFilters = (
    next: Partial<{
      search: string
      direction: DirectionFilter
      active: ActiveFilter
    }>,
  ) => {
    if (next.search !== undefined) setSearch(next.search)
    if (next.direction !== undefined) setDirection(next.direction)
    if (next.active !== undefined) setActive(next.active)

    setParams((prev) => {
      const s = next.search ?? search
      const d = next.direction ?? direction
      const a = next.active ?? active
      return {
        ...prev,
        search: s || undefined,
        direction: d === 'all' ? undefined : d,
        is_active: a === 'all' ? undefined : a === 'true',
      }
    })
  }

  const [createOpen, setCreateOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [form, setForm] = useState<CameraCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<Camera | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [toggleNotice, setToggleNotice] = useState<string | null>(null)

  const resetForm = () => {
    setForm(EMPTY_FORM)
    setSubmitError(null)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSubmitting(true)
      setSubmitError(null)
      await camerasService.create(form)
      setCreateOpen(false)
      resetForm()
      await refetch()
    } catch {
      setSubmitError("Kamerani yaratib bo'lmadi. Maydonlarni tekshirib qayta urinib ko‘ring.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!toDelete) return
    try {
      await camerasService.remove(toDelete.id)
      setToDelete(null)
      await refetch()
    } catch (err) {
      console.error('Failed to delete camera', err)
    }
  }

  const handleToggle = async (camera: Camera) => {
    setToggleNotice(null)
    setBusyId(camera.id)
    try {
      if (camera.is_active) {
        await camerasService.disconnect(camera.id)
        await refetch()
        return
      }

      await camerasService.connect(camera.id)
      await refetch()

      // The backend starts the Hikvision stream as a background task and
      // returns immediately. If the device is unreachable, the task fails
      // a few seconds later and marks the camera as inactive in the DB.
      // Re-check to surface that state to the user.
      window.setTimeout(async () => {
        try {
          const fresh = await camerasService.get(camera.id)
          await refetch()
          if (!fresh.is_active) {
            setToggleNotice(
              `${camera.device_ip} ga ulanib bo'lmadi. Qurilma o'chirilgan yoki tarmoqda mavjud emas.`,
            )
          }
        } catch (err) {
          console.error('Failed to verify camera state', err)
        }
      }, 4000)
    } catch (err) {
      console.error('Failed to toggle camera', err)
      setToggleNotice(
        `${camera.device_ip} ni ulashda xatolik yuz berdi. Qayta urinib ko'ring.`,
      )
      await refetch()
    } finally {
      setBusyId(null)
    }
  }

  return (
    <TooltipProvider delayDuration={200}>
      <PageHeader
        title="Kameralar"
        description="Videokuzatuv tarmog‘ini boshqarish"
        actions={
          <Button
            onClick={() => {
              resetForm()
              setCreateOpen(true)
            }}
          >
            <Plus className="size-4" aria-hidden />
            Kamera qo‘shish
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
            <Label htmlFor="camera-search" className="sr-only">
              IP yoki login bo‘yicha qidirish
            </Label>
            <Input
              id="camera-search"
              type="search"
              value={search}
              onChange={(e) => applyFilters({ search: e.target.value })}
              placeholder="IP yoki login bo‘yicha qidirish…"
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Select
              value={direction}
              onValueChange={(v) =>
                applyFilters({ direction: v as DirectionFilter })
              }
            >
              <SelectTrigger
                className="w-full sm:w-48"
                aria-label="Yo‘nalish filtri"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha yo‘nalishlar</SelectItem>
                <SelectItem value="enter">Kirish</SelectItem>
                <SelectItem value="exit">Chiqish</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={active}
              onValueChange={(v) =>
                applyFilters({ active: v as ActiveFilter })
              }
            >
              <SelectTrigger
                className="w-full sm:w-48"
                aria-label="Holat filtri"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Barcha holatlar</SelectItem>
                <SelectItem value="true">Onlayn</SelectItem>
                <SelectItem value="false">Uzilgan</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {toggleNotice ? (
        <Alert variant="destructive" role="status">
          <CircleAlert className="size-4" aria-hidden />
          <AlertTitle>Ulanish muvaffaqiyatsiz</AlertTitle>
          <AlertDescription>{toggleNotice}</AlertDescription>
        </Alert>
      ) : null}

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
        ) : cameras.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={CameraIcon}
              title="Kameralar topilmadi"
              description="Filtrni o‘zgartiring yoki birinchi kamerangizni qo‘shing."
            />
          </div>
        ) : (
          <>
            <ScrollableTable>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>IP manzil</TableHead>
                    <TableHead>Login</TableHead>
                    <TableHead>Yo‘nalish</TableHead>
                    <TableHead>Holati</TableHead>
                    <TableHead className="w-32 text-right">Amallar</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cameras.map((camera) => (
                    <TableRow key={camera.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="grid size-8 place-items-center rounded-md bg-muted text-muted-foreground">
                            <CameraIcon className="size-4" aria-hidden />
                          </div>
                          <span className="font-medium tabular-nums">
                            {camera.device_ip}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {camera.login}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {camera.direction === 'enter' ? 'Kirish' : 'Chiqish'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center gap-2 text-sm">
                          <span
                            className={
                              camera.is_active
                                ? 'size-2 rounded-full bg-emerald-500'
                                : 'size-2 rounded-full bg-muted-foreground/50'
                            }
                            aria-hidden
                          />
                          {camera.is_active ? 'Onlayn' : 'Uzilgan'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                disabled={busyId === camera.id}
                                onClick={() => handleToggle(camera)}
                                aria-label={
                                  camera.is_active ? 'Uzish' : 'Ulash'
                                }
                              >
                                {camera.is_active ? (
                                  <PowerOff className="size-4" aria-hidden />
                                ) : (
                                  <Power className="size-4" aria-hidden />
                                )}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              {camera.is_active ? 'Uzish' : 'Ulash'}
                            </TooltipContent>
                          </Tooltip>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive hover:text-destructive"
                                onClick={() => setToDelete(camera)}
                                aria-label="Kamerani o‘chirish"
                              >
                                <Trash2 className="size-4" aria-hidden />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>O‘chirish</TooltipContent>
                          </Tooltip>
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
            <DialogTitle>Yangi kamera</DialogTitle>
            <DialogDescription>
              Hikvision qurilmasining ulanish parametrlarini kiriting.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleCreate}>
            <div className="space-y-2">
              <Label htmlFor="device_ip">IP manzil</Label>
              <Input
                id="device_ip"
                required
                value={form.device_ip}
                onChange={(e) =>
                  setForm({ ...form, device_ip: e.target.value })
                }
                placeholder="192.168.1.10"
                autoComplete="off"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="login">Login</Label>
              <Input
                id="login"
                required
                value={form.login}
                onChange={(e) =>
                  setForm({ ...form, login: e.target.value })
                }
                placeholder="admin"
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
            <div className="space-y-2">
              <Label htmlFor="direction">Yo‘nalish</Label>
              <Select
                value={form.direction}
                onValueChange={(value) =>
                  setForm({
                    ...form,
                    direction: value as CameraCreateInput['direction'],
                  })
                }
              >
                <SelectTrigger id="direction">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="enter">Kirish</SelectItem>
                  <SelectItem value="exit">Chiqish</SelectItem>
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
            <AlertDialogTitle>Kamerani o‘chirish?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete?.device_ip} kamerasi o‘chiriladi, kuzatuv to‘xtaydi.
              Bu amal qaytarib bo‘lmaydi.
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
    </TooltipProvider>
  )
}
