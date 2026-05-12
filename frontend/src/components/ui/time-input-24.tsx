import * as React from 'react'

import { cn } from '@/lib/utils'

type TimeInput24Props = {
  id?: string
  value: string
  onChange: (value: string) => void
  required?: boolean
  disabled?: boolean
  className?: string
}

function splitHM(value: string): [string, string] {
  const [h = '', m = ''] = value.split(':')
  return [h, m]
}

function clamp(num: number, min: number, max: number) {
  if (Number.isNaN(num)) return min
  return Math.min(max, Math.max(min, num))
}

function sanitize(part: string, max: number): string {
  const digits = part.replace(/\D/g, '').slice(0, 2)
  if (digits === '') return ''
  return String(clamp(Number(digits), 0, max))
}

function pad(part: string): string {
  if (part === '') return '00'
  return part.padStart(2, '0')
}

export function TimeInput24({
  id,
  value,
  onChange,
  required,
  disabled,
  className,
}: TimeInput24Props) {
  const [hRaw, mRaw] = splitHM(value)
  const [hours, setHours] = React.useState(hRaw)
  const [minutes, setMinutes] = React.useState(mRaw)

  React.useEffect(() => {
    const [h, m] = splitHM(value)
    setHours(h)
    setMinutes(m)
  }, [value])

  const emit = (h: string, m: string) => {
    onChange(`${pad(h)}:${pad(m)}`)
  }

  return (
    <div
      className={cn(
        'flex h-9 w-full items-center rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50 md:text-sm dark:bg-input/30',
        disabled && 'pointer-events-none cursor-not-allowed opacity-50',
        className,
      )}
    >
      <input
        id={id}
        type="text"
        inputMode="numeric"
        aria-label="Soat"
        required={required}
        disabled={disabled}
        value={hours}
        placeholder="00"
        maxLength={2}
        className="w-7 bg-transparent text-center tabular-nums outline-none"
        onChange={(e) => {
          const next = sanitize(e.target.value, 23)
          setHours(next)
          emit(next, minutes)
        }}
        onBlur={() => {
          const padded = pad(hours)
          setHours(padded)
          emit(padded, minutes)
        }}
      />
      <span className="text-muted-foreground">:</span>
      <input
        type="text"
        inputMode="numeric"
        aria-label="Daqiqa"
        required={required}
        disabled={disabled}
        value={minutes}
        placeholder="00"
        maxLength={2}
        className="w-7 bg-transparent text-center tabular-nums outline-none"
        onChange={(e) => {
          const next = sanitize(e.target.value, 59)
          setMinutes(next)
          emit(hours, next)
        }}
        onBlur={() => {
          const padded = pad(minutes)
          setMinutes(padded)
          emit(hours, padded)
        }}
      />
    </div>
  )
}
