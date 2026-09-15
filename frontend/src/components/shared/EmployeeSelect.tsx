import { Check, ChevronsUpDown, Search } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { employeesService } from '@/services/employees'
import type { Employee } from '@/types/employee'

type Props = {
  value: number | null
  onChange: (next: number | null) => void
  id?: string
  allLabel?: string
  className?: string
}

const PAGE_SIZE = 20

/**
 * Picks one employee, searched on the server.
 *
 * A plain select cannot do this job here: there are several hundred employees,
 * far more than a dropdown can hold, and the page used to load only the first
 * two hundred — so everyone after that was unreachable rather than merely
 * inconvenient to find.
 */
export function EmployeeSelect({
  value,
  onChange,
  id,
  allLabel = 'Barcha xodimlar',
  className,
}: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Employee[]>([])
  const [loading, setLoading] = useState(true)
  // The chosen employee may be nowhere in the current results — they were found
  // by a search since typed over — so their name is fetched and cached apart
  // from the list, and only counts while it still matches the chosen id.
  const [cached, setCached] = useState<Employee | null>(null)
  const selected = value !== null && cached?.id === value ? cached : null
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (value === null || cached?.id === value) return
    let cancelled = false
    employeesService
      .get(value)
      .then((emp) => {
        if (!cancelled) setCached(emp)
      })
      .catch((err) => console.error('Failed to load employee', err))
    return () => {
      cancelled = true
    }
  }, [value, cached?.id])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    // Debounced, so typing a name does not fire a request per keystroke.
    const timer = setTimeout(() => {
      setLoading(true)
      employeesService
        .list({ limit: PAGE_SIZE, search: query.trim() || undefined })
        .then((res) => {
          if (!cancelled) setResults(res.employees)
        })
        .catch((err) => console.error('Failed to search employees', err))
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    }, 250)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [query, open])

  const pick = (next: number | null) => {
    onChange(next)
    setOpen(false)
    setQuery('')
  }

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (next) setTimeout(() => searchRef.current?.focus(), 0)
        else setQuery('')
      }}
    >
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn('w-full justify-between font-normal', className)}
        >
          <span className="truncate">{selected?.full_name ?? allLabel}</span>
          <ChevronsUpDown className="size-4 shrink-0 opacity-50" aria-hidden />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] min-w-64 p-0">
        <div className="relative border-b">
          <Search
            className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            ref={searchRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ism yoki JSHIR bo‘yicha..."
            className="border-0 pl-8 shadow-none focus-visible:ring-0"
          />
        </div>
        <div className="max-h-64 overflow-y-auto p-1">
          <button
            type="button"
            onClick={() => pick(null)}
            className="flex w-full items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent"
          >
            <span>{allLabel}</span>
            {value === null ? <Check className="size-4" aria-hidden /> : null}
          </button>
          {loading ? (
            <p className="px-2 py-3 text-center text-sm text-muted-foreground">
              Qidirilmoqda...
            </p>
          ) : results.length === 0 ? (
            <p className="px-2 py-3 text-center text-sm text-muted-foreground">
              Xodim topilmadi
            </p>
          ) : (
            results.map((emp) => (
              <button
                key={emp.id}
                type="button"
                onClick={() => pick(emp.id)}
                className="flex w-full items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent"
              >
                <span className="min-w-0">
                  <span className="block truncate">{emp.full_name}</span>
                  <span className="block truncate text-xs text-muted-foreground tabular-nums">
                    {emp.jshir}
                  </span>
                </span>
                {value === emp.id ? (
                  <Check className="size-4 shrink-0" aria-hidden />
                ) : null}
              </button>
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
