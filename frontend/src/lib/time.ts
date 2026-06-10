export function todayIso(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

export function formatTimeOnly(value: string | null | undefined): string {
  if (!value) return '—'
  const match = String(value).match(/(\d{1,2}):(\d{2})/)
  if (!match) return String(value)
  return `${match[1].padStart(2, '0')}:${match[2]}`
}

export function parseTimeInput(value: string): string {
  const trimmed = (value ?? '').trim()
  if (!trimmed) return trimmed
  const match = trimmed.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
  if (!match) return trimmed
  const hh = match[1].padStart(2, '0')
  const mm = match[2]
  const ss = match[3] ?? '00'
  return `${hh}:${mm}:${ss}`
}
