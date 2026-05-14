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
}

export type TabelMonthResponse = {
  year: number
  month: number
  days_in_month: number
  working_days: number
  rows: TabelRow[]
}

export type TabelMonthParams = {
  year: number
  month: number
  department?: string
  search?: string
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
