export type TabelCode =
  | 'B'
  | 'A'
  | 'V'
  | 'VU'
  | 'N'
  | 'G'
  | 'O'
  | 'OU'
  | 'R'
  | 'RP'
  | 'S'
  | 'P'
  | 'F'

export type TabelCodeInfo = {
  code: TabelCode
  label: string
}

export const TABEL_CODES: TabelCodeInfo[] = [
  { code: 'B', label: 'Haqiqatda ishlangan kunlar' },
  { code: 'A', label: 'Dam olish va bayram kunlari' },
  { code: 'V', label: "Ma'muriyat ruxsati bilan ishda qatnashmagan kunlar" },
  { code: 'VU', label: 'Kechalardagi ish vaqti' },
  { code: 'N', label: "O'qish bo'yicha dam olishlar" },
  { code: 'G', label: "O'quv ta'tili" },
  { code: 'O', label: 'Bayramda ishlangan kunlar' },
  { code: 'OU', label: 'Davlat oldidagi majburiyatlar bajarish' },
  { code: 'R', label: 'Mehnatga layoqatsizlik' },
  { code: 'RP', label: "Keyingi va qo'shimcha mehnat ta'tili" },
  { code: 'S', label: "Tug'ish bilan bog'liq ta'tillar" },
  { code: 'P', label: 'Navbatdan tashqari ish soatlari' },
  { code: 'F', label: 'Progullar' },
]

export const TABEL_CODE_CLASS: Record<TabelCode, string> = {
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

export const TABEL_CODE_LABEL = new Map(
  TABEL_CODES.map((entry) => [entry.code, entry.label]),
)

export type TabelCellSource = 'auto' | 'manual'

export type TabelCell = {
  day: number
  code: TabelCode | null
  source: TabelCellSource
}

export type TabelRow = {
  employee_id: number
  full_name: string
  position: string | null
  department: string | null
  cells: TabelCell[]
  worked_days: number
  work_rate: number
}

export type TabelMonthResponse = {
  year: number
  month: number
  days_in_month: number
  working_days: number
  total: number
  page: number
  limit: number
  rows: TabelRow[]
}

export type TabelMonthParams = {
  year: number
  month: number
  department?: string
  search?: string
  page?: number
  limit?: number
}

export type TabelEntryUpsertInput = {
  employee_id: number
  date: string
  code: TabelCode
  comment?: string | null
}

export type TabelEntryDeleteInput = {
  employee_id: number
  date: string
}
