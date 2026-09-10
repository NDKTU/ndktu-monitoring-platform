import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { TabelCode } from '@/types/tabel'
import { TABEL_CODE_CLASS, TABEL_CODE_LABEL } from '@/types/tabel'

type TabelCodeBadgeProps = {
  code: TabelCode
  comment?: string | null
  className?: string
}

/** A tabel mark set by hand, shown wherever it explains a day. */
export function TabelCodeBadge({
  code,
  comment,
  className,
}: TabelCodeBadgeProps) {
  const label = TABEL_CODE_LABEL.get(code) ?? code
  return (
    <Badge
      variant="secondary"
      className={cn(TABEL_CODE_CLASS[code], 'border-transparent', className)}
      title={comment ? `${label} — ${comment}` : label}
    >
      {label}
    </Badge>
  )
}
