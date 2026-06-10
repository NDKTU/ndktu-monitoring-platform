const IPV4_REGEX =
  /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$/

export function isValidIPv4(value: string): boolean {
  return IPV4_REGEX.test(value)
}

export function trimString<T extends string | null | undefined>(value: T): T {
  if (typeof value !== 'string') return value
  return value.trim() as T
}

export function trimFormStrings<T extends Record<string, unknown>>(form: T): T {
  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(form)) {
    result[key] = typeof value === 'string' ? value.trim() : value
  }
  return result as T
}
