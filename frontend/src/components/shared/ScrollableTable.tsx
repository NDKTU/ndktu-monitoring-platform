import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type ScrollableTableProps = {
  children: ReactNode
  className?: string
}

export function ScrollableTable({
  children,
  className,
}: ScrollableTableProps) {
  return (
    <div className={cn('relative', className)}>
      <div className="overflow-x-auto">{children}</div>
      <div
        aria-hidden
        className="pointer-events-none absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-foreground/15 to-transparent sm:hidden"
      />
    </div>
  )
}
