const hasExplicitTimezone = (value: string) => /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)

export const parseApiDate = (value: string) => {
  const normalized = value.trim()
  const safeValue = hasExplicitTimezone(normalized) ? normalized : `${normalized}Z`
  return new Date(safeValue)
}

export const formatDateTime = (value: string, options?: Intl.DateTimeFormatOptions) => {
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('zh-CN', {
    hour12: false,
    timeZone: 'Asia/Shanghai',
    ...options,
  })
}
