import type { Calendar } from '../charts/bazi'

const oldZones: Record<string, string> = {
  'UTC+08:00': 'Asia/Shanghai',
  'UTC+00:00': 'Etc/UTC',
  'UTC+09:00': 'Asia/Tokyo',
  'UTC-05:00': 'Etc/GMT+5',
}
export const timezones = [
  { value: 'Asia/Shanghai', label: '中国 · Asia/Shanghai' },
  { value: 'Asia/Tokyo', label: '日本 · Asia/Tokyo' },
  { value: 'Europe/London', label: '英国 · Europe/London' },
  { value: 'America/New_York', label: '纽约 · America/New_York' },
  { value: 'America/Los_Angeles', label: '洛杉矶 · America/Los_Angeles' },
  { value: 'Etc/UTC', label: '固定 UTC+00:00' },
  { value: 'Etc/GMT+5', label: '固定 UTC−05:00' },
]

export const clockOccurrences = [
  { value: '', label: '默认（未重复）' },
  { value: '0', label: '第一次出现' },
  { value: '1', label: '第二次出现' },
]

export function birthInput(date: string, time: string, timezone: string, calendar: Calendar = 'solar', leap = false, occurrence = '') {
  const [year, month, day] = date.split('-').map(Number)
  const fold = time && (occurrence === '0' || occurrence === '1') ? Number(occurrence) : undefined
  return { year, month, day, birth_time: time || null, timezone: oldZones[timezone] || timezone, calendar, leap_month: leap, fold }
}

export function deviceTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai'
  } catch {
    return 'Asia/Shanghai'
  }
}
