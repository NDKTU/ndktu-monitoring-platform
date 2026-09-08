/**
 * UI feature flags.
 *
 * These features are intentionally kept in the codebase — backend endpoints,
 * database columns and TypeScript types are all untouched — but hidden from the
 * UI because they are not needed right now. Flip a flag back to `true` to
 * restore the corresponding screens and fields.
 */
export const FEATURES = {
  /** Lavozimlar (positions): sidebar entry, route, and employee position field. */
  SHOW_POSITIONS: false,

  /**
   * Bo'limlar (departments): sidebar entry, route, employee department field
   * and the Tabel department filter.
   *
   * Note: a department also carries the work schedule that EmployeeDetail and
   * WorkScheduleDetail read. That logic still works off existing data; with
   * this flag off there is simply no UI to change the linkage.
   */
  SHOW_DEPARTMENTS: false,

  /** Ish stavkasi (work rate): employee form field, table column, detail row. */
  SHOW_WORK_RATE: false,
} as const
