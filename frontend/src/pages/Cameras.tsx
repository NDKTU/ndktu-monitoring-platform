import axios from 'axios'
import {
  Camera as CameraIcon,
  CircleAlert,
  Loader2,
  Pencil,
  Plus,
  Power,
  PowerOff,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
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
import { isValidIPv4, trimFormStrings } from '@/lib/validation'
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

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Camera | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [ipError, setIpError] = useState<string | null>(null)
  const [form, setForm] = useState<CameraCreateInput>(EMPTY_FORM)
  const [toDelete, setToDelete] = useState<Camera | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [toggleNotice, setToggleNotice] = useState<string | null>(null)

  useEffect(() => {
    if (!toggleNotice) return
    const timer = window.setTimeout(() => setToggleNotice(null), 6000)
    return () => window.clearTimeout(timer)
  }, [toggleNotice])

  const isEditing = editing !== null

  const resetForm = () => {
    setForm(EMPTY_FORM)
    setSubmitError(null)
    setIpError(null)
    setEditing(null)
  }

  const openCreate = () => {
    resetForm()
    setDialogOpen(true)
  }

  const openEdit = (camera: Camera) => {
    setEditing(camera)
    setForm({
      device_ip: camera.device_ip,
      login: camera.login,
      password: '',
      direction: camera.direction,
      is_active: camera.is_active,
    })
    setSubmitError(null)
    setIpError(null)
    setDialogOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const cleaned = trimFormStrings(form)

    if (!isValidIPv4(cleaned.device_ip)) {
      setIpError(
        "IP manzil noto‘g‘ri formatda. Misol: 192.168.1.10 (faqat raqamlar, 0–255 oralig‘ida).",
      )
      setSubmitError(null)
      return
    }

    try {
      setSubmitting(true)
      setSubmitError(null)
      setIpError(null)
      setForm(cleaned)
      if (editing) {
        const { password: _omit, ...rest } = cleaned
        void _omit
        await camerasService.update(editing.id, rest)
      } else {
        await camerasService.create(cleaned)
      }
      setDialogOpen(false)
      resetForm()
      await refetch()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setIpError(`Bunday IP manzilli kamera allaqachon mavjud: ${cleaned.device_ip}`)
      } else {
        setSubmitError(
          editing
            ? "Kamerani yangilab bo'lmadi. Maydonlarni tekshirib qayta urinib ko‘ring."
            : "Kamerani yaratib bo'lmadi. Maydonlarni tekshirib qayta urinib ko‘ring.",
        )
      }
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
      } else {
        await camerasService.connect(camera.id)
      }
      await refetch()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 503) {
        const detail = err.response.data?.detail
        const message =
          typeof detail === 'object' && detail !== null && 'message' in detail
            ? String((detail as { message: unknown }).message)
            : `${camera.device_ip} ga ulanib bo‘lmadi.`
        setToggleNotice(message)
      } else {
        console.error('Failed to toggle camera', err)
        setToggleNotice(
          `${camera.device_ip} ni ulashda xatolik yuz berdi. Qayta urinib ko‘ring.`,
        )
      }
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
          <Button onClick={openCreate}>
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
        <Alert variant="destructive" role="status" className="relative pr-10">
          <CircleAlert className="size-4" aria-hidden />
          <AlertTitle>Ulanish muvaffaqiyatsiz</AlertTitle>
          <AlertDescription>{toggleNotice}</AlertDescription>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1 size-7 text-destructive hover:bg-destructive/10"
            onClick={() => setToggleNotice(null)}
            aria-label="Yopish"
          >
            <X className="size-4" aria-hidden />
          </Button>
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
                                {busyId === camera.id ? (
                                  <Loader2
                                    className="size-4 animate-spin"
                                    aria-hidden
                                  />
                                ) : camera.is_active ? (
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
                                onClick={() => openEdit(camera)}
                                aria-label="Kamerani tahrirlash"
                              >
                                <Pencil className="size-4" aria-hidden />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Tahrirlash</TooltipContent>
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
        open={dialogOpen}
        onOpenChange={(next) => {
          setDialogOpen(next)
          if (!next) resetForm()
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? 'Kamerani tahrirlash' : 'Yangi kamera'}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Kamera parametrlarini yangilang. Parolni o‘zgartirib bo‘lmaydi.'
                : 'Hikvision qurilmasining ulanish parametrlarini kiriting.'}
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="device_ip">IP manzil</Label>
              <Input
                id="device_ip"
                required
                value={form.device_ip}
                onChange={(e) => {
                  const next = e.target.value.replace(/[^0-9.]/g, '')
                  setForm({ ...form, device_ip: next })
                  if (ipError) setIpError(null)
                }}
                placeholder="192.168.1.10"
                inputMode="decimal"
                pattern="^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$"
                aria-invalid={ipError ? true : undefined}
                aria-describedby={ipError ? 'device_ip-error' : undefined}
                autoComplete="off"
              />
              {ipError ? (
                <p
                  id="device_ip-error"
                  role="alert"
                  className="text-sm font-medium text-destructive"
                >
                  {ipError}
                </p>
              ) : null}
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
            {isEditing ? null : (
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
            )}
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
