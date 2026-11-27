import { shallowRef, watch, type Ref } from 'vue'
import { api, live } from '../../shared/api'
import { deviceTimezone } from '../account/birth'
import { signs, type Zodiac } from './zodiac'

interface Fortune {
  sign: string
  date: string
  summary: string
  relationship: string
}
interface CalendarInfo {
  date: string
  lunar: { label: string }
  solar_term: string | null
  festivals: string[]
  moon_phase?: { name: string; elongation: number; timezone: string }
}

export async function refreshZodiac() {
  if (!live) return
  const items = await api<Zodiac[]>('/zodiac')
  if (items.length === 12) signs.splice(0, signs.length, ...items)
}

export function useFortune(sign: Readonly<Ref<Zodiac>>, date: Readonly<Ref<string>>) {
  const result = shallowRef<Fortune>()
  watch([sign, date], ([current, day], _old, onCleanup) => {
    result.value = undefined
    if (!live) return
    let active = true
    onCleanup(() => { active = false })
    void api<Fortune>('/fortune/' + current.id + '?day=' + encodeURIComponent(day))
      .then((data) => { if (active) result.value = data })
      .catch(() => undefined)
  }, { immediate: true })
  return result
}

export function useCalendar(date: Readonly<Ref<string>>) {
  const result = shallowRef<CalendarInfo>()
  watch(date, (day, _old, onCleanup) => {
    result.value = undefined
    if (!live) return
    let active = true
    onCleanup(() => { active = false })
    const query = 'day=' + encodeURIComponent(day) + '&timezone=' + encodeURIComponent(deviceTimezone())
    void api<CalendarInfo>('/calendar/day?' + query)
      .then((data) => { if (active) result.value = data })
      .catch(() => undefined)
  }, { immediate: true })
  return result
}
