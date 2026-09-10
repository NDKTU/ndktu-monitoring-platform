import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { DayStatus } from '@/types/dailyAttendance'

const STATUS_MAP: Record<
  DayStatus,
  { label: string; className: string }
> = {
  ON_TIME: {
    label: 'Vaqtida',
    className:
      'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-transparent',
  },
  LATE_ARRIVAL: {
    label: 'Kech kelgan',
    className:
      'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-transparent',
  },
  EARLY_LEAVE: {
    label: 'Erta ketgan',
    className:
      'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-transparent',
  },
  LATE_AND_EARLY: {
    label: 'Kech va erta',
    className: 'bg-destructive/15 text-destructive border-transparent',
  },
  NO_ENTER: {
    label: 'Kirish yo‘q',
    className: 'bg-destructive/15 text-destructive border-transparent',
  },
  NO_EXIT: {
    label: 'Chiqish yo‘q',
    className: 'bg-destructive/15 text-destructive border-transparent',
  },
  ABSENT: {
    label: 'Kelmagan',
    className: 'bg-destructive/15 text-destructive border-transparent',
  },
  DAY_OFF: {
    label: 'Dam olish',
    className: 'bg-muted text-muted-foreground border-transparent',
  },
}

type StatusBadgeProps = {
  status: DayStatus | null
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  if (!status) {
    return (
      <span className={cn('text-sm text-muted-foreground', className)}>—</span>
    )
  }
  const config = STATUS_MAP[status]
  return (
    <Badge variant="secondary" className={cn(config.className, className)}>
      {config.label}
    </Badge>
  )
}
