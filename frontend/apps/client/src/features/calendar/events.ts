import { dateKey } from '../../shared/storage'
import { accountStore } from '../../shared/api'

export interface CalendarEvent {
  id: string
  title: string
  date: string
  repeat: string
  reminder: boolean
  birthday: boolean
}
export const events = accountStore<CalendarEvent[]>('events', [])
export function happensOn(event: CalendarEvent, value = dateKey()) {
  if (event.date === value) return true
  if (value < event.date) return false
  if (event.repeat === '每年') return value.slice(5) === event.date.slice(5)
  if (event.repeat === '每月') return value.slice(8) === event.date.slice(8)
  if (event.repeat === '每周')
    return new Date(value + 'T12:00:00').getDay() === new Date(event.date + 'T12:00:00').getDay()
  return false
}
