import { Table2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { EmptyState } from '@/components/shared/EmptyState'
import { ErrorState } from '@/components/shared/ErrorState'
import { PageHeader } from '@/components/shared/PageHeader'
import { ScrollableTable } from '@/components/shared/ScrollableTable'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { cn } from '@/lib/utils'
import { tabelService } from '@/services/tabel'
import type {
  TabelCode,
  TabelMonthResponse,
  TabelRow,
} from '@/types/tabel'
import { TABEL_CODES } from '@/types/tabel'

const MONTHS = [
  'Yanvar',
  'Fevral',
  'Mart',
  'Aprel',
  'May',
  'Iyun',
  'Iyul',
  'Avgust',
  'Sentabr',
  'Oktabr',
  'Noyabr',
  'Dekabr',
]

const CODE_CLASS: Record<TabelCode, string> = {
  B: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
  A: 'bg-muted text-muted-foreground',
  V: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  VU: 'bg-sky-500/15 text-sky-600 dark:text-sky-400',
  N: 'bg-sky-500/15 text-sky-600 dark:text-sky-400',
  G: 'bg-violet-500/15 text-violet-600 dark:text-violet-400',
  O: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
  OU: 'bg-violet-500/15 text-violet-600 dark:text-violet-400',
  R: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  RP: 'bg-violet-500/15 text-violet-600 dark:text-violet-400',
  S: 'bg-pink-500/15 text-pink-600 dark:text-pink-400',
  P: 'bg-destructive/15 text-destructive',
  F: 'bg-destructive/15 text-destructive',
}

function pad(value: number) {
  return String(value).padStart(2, '0')
}

type EditingCell = {
  row: TabelRow
  day: number
  date: string
  current: TabelCode | null
}

export default function TabelPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [department, setDepartment] = useState('')
  const [search, setSearch] = useState('')

  const [data, setData] = useState<TabelMonthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const [editing, setEditing] = useState<EditingCell | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await tabelService.getMonth({
        year,
        month,
        department: department.trim() || undefined,
        search: search.trim() || undefined,
      })
      setData(res)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed'))
    } finally {
      setLoading(false)
    }
  }, [year, month, department, search])

  useEffect(() => {
    const id = setTimeout(load, 300)
    return () => clearTimeout(id)
  }, [load])

  const dayNumbers = useMemo(() => {
    if (!data) return []
    return Array.from({ length: data.days_in_month }, (_, i) => i + 1)
  }, [data])

  const isWeekend = (day: number) => {
    const d = new Date(year, month - 1, day)
    return d.getDay() === 0 || d.getDay() === 6
  }

  const openCell = (row: TabelRow, day: number) => {
    const cell = row.cells.find((c) => c.day === day)
    setEditing({
      row,
      day,
      date: `${year}-${pad(month)}-${pad(day)}`,
      current: cell?.code ?? null,
    })
  }

  const applyCode = async (code: TabelCode | null) => {
    if (!editing) return
    try {
      setSaving(true)
      if (code === null) {
        await tabelService.deleteEntry({
          employee_id: editing.row.employee_id,
          date: editing.date,
        })
      } else {
        await tabelService.upsertEntry({
          employee_id: editing.row.employee_id,
          date: editing.date,
          code,
        })
      }
      setEditing(null)
      await load()
    } catch (err) {
      console.error('Failed to save tabel entry', err)
    } finally {
      setSaving(false)
    }
  }

  const years = useMemo(() => {
    const current = now.getFullYear()
    return [current - 2, current - 1, current, current + 1]
  }, [now])

  return (
    <>
      <PageHeader
        title="Tabel"
        description="Oylik ish vaqtini hisobga olish jadvali"
      />

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-2">
            <Label htmlFor="tabel-year">Yil</Label>
            <Select
              value={String(year)}
              onValueChange={(v) => setYear(Number(v))}
            >
              <SelectTrigger id="tabel-year" className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {years.map((y) => (
                  <SelectItem key={y} value={String(y)}>
                    {y}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="tabel-month">Oy</Label>
            <Select
              value={String(month)}
              onValueChange={(v) => setMonth(Number(v))}
            >
              <SelectTrigger id="tabel-month" className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MONTHS.map((label, idx) => (
                  <SelectItem key={label} value={String(idx + 1)}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="tabel-department">Bo'lim</Label>
            <Input
              id="tabel-department"
              placeholder="Barcha bo'limlar"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-52"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tabel-search">Qidirish</Label>
            <Input
              id="tabel-search"
              placeholder="F.I.Sh. yoki JSHIR"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-52"
            />
          </div>
          {data ? (
            <div className="ml-auto text-sm text-muted-foreground">
              Oydagi ish kunlari:{' '}
              <span className="font-semibold text-foreground tabular-nums">
                {data.working_days}
              </span>
            </div>
          ) : null}
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        {error ? (
          <div className="p-6">
            <ErrorState onRetry={load} />
          </div>
        ) : loading ? (
          <div className="space-y-2 p-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !data || data.rows.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Table2}
              title="Xodimlar topilmadi"
              description="Tanlangan filtr bo'yicha natija yo'q."
            />
          </div>
        ) : (
          <ScrollableTable>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="sticky left-0 z-10 min-w-56 bg-card">
                    F.I.Sh.
                  </TableHead>
                  {dayNumbers.map((day) => (
                    <TableHead
                      key={day}
                      className={cn(
                        'w-9 px-0 text-center tabular-nums',
                        isWeekend(day) && 'text-destructive',
                      )}
                    >
                      {day}
                    </TableHead>
                  ))}
                  <TableHead className="text-right">Jami</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.rows.map((row) => (
                  <TableRow key={row.employee_id}>
                    <TableCell className="sticky left-0 z-10 bg-card">
                      <div className="font-medium">{row.full_name}</div>
                      {row.position ? (
                        <div className="text-xs text-muted-foreground">
                          {row.position}
                        </div>
                      ) : null}
                    </TableCell>
                    {row.cells.map((cell) => (
                      <TableCell key={cell.day} className="p-0.5 text-center">
                        <button
                          type="button"
                          onClick={() => openCell(row, cell.day)}
                          className={cn(
                            'inline-flex size-8 items-center justify-center rounded text-xs font-medium transition-colors hover:ring-2 hover:ring-ring',
                            cell.code
                              ? CODE_CLASS[cell.code]
                              : 'text-muted-foreground hover:bg-accent',
                            cell.source === 'manual' &&
                              'ring-1 ring-inset ring-foreground/20',
                          )}
                          aria-label={`${row.full_name} — ${cell.day}-kun`}
                        >
                          {cell.code ?? '·'}
                        </button>
                      </TableCell>
                    ))}
                    <TableCell className="text-right font-semibold tabular-nums">
                      {row.worked_days}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollableTable>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold">Shartli belgilar</h2>
        <div className="grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {TABEL_CODES.map(({ code, label }) => (
            <div key={code} className="flex items-center gap-2">
              <span
                className={cn(
                  'inline-flex size-6 shrink-0 items-center justify-center rounded text-xs font-medium',
                  CODE_CLASS[code],
                )}
              >
                {code}
              </span>
              <span className="text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </Card>

      <Dialog
        open={!!editing}
        onOpenChange={(next) => !next && setEditing(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Belgi tanlash</DialogTitle>
            <DialogDescription>
              {editing
                ? `${editing.row.full_name} — ${editing.day}-${MONTHS[month - 1]}`
                : null}
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            {TABEL_CODES.map(({ code, label }) => (
              <button
                key={code}
                type="button"
                disabled={saving}
                onClick={() => applyCode(code)}
                title={label}
                className={cn(
                  'flex flex-col items-center gap-1 rounded-md border p-2 text-center transition-colors hover:ring-2 hover:ring-ring disabled:opacity-50',
                  editing?.current === code && 'ring-2 ring-ring',
                )}
              >
                <span
                  className={cn(
                    'inline-flex size-7 items-center justify-center rounded text-sm font-semibold',
                    CODE_CLASS[code],
                  )}
                >
                  {code}
                </span>
                <span className="line-clamp-2 text-[10px] leading-tight text-muted-foreground">
                  {label}
                </span>
              </button>
            ))}
          </div>
          <Button
            type="button"
            variant="outline"
            disabled={saving}
            onClick={() => applyCode(null)}
          >
            Avto (tozalash)
          </Button>
        </DialogContent>
      </Dialog>
    </>
  )
}
