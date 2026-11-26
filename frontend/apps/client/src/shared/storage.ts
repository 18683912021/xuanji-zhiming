import { shallowRef } from 'vue'

export function readStorage<T>(key: string, fallback: T): T {
  try {
    const value: unknown = uni.getStorageSync(key)
    return value === '' || value == null ? fallback : (value as T)
  } catch {
    return fallback
  }
}

export function localStore<T>(name: string, initial: T) {
  const key = 'xuanji:client:' + name
  const state = shallowRef(readStorage(key, initial))
  function write(value: T) {
    try {
      uni.setStorageSync(key, value)
      state.value = value
      return true
    } catch {
      uni.showToast({ title: '本机保存失败，请重试。', icon: 'none' })
      return false
    }
  }
  return { state, write }
}

export const makeId = () => Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12)

export function dateKey(date = new Date()) {
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()]
    .map((part) => String(part).padStart(2, '0'))
    .join('-')
}

export function parseDate(value: string) {
  return new Date(value + 'T12:00:00')
}

export function offsetDate(value: string, days: number) {
  const date = parseDate(value)
  date.setDate(date.getDate() + days)
  return dateKey(date)
}

export function displayDate(value: string) {
  return value.slice(0, 10).replace(/-/g, '·')
}

export function readPreviousWebData<T>(key: string, fallback: T): T {
  // #ifdef H5
  try {
    const raw = window.localStorage.getItem('xuanji:v1:' + key)
    if (raw) return JSON.parse(raw) as T
  } catch {
    // An inaccessible or invalid browser entry is treated as empty.
  }
  // #endif
  return fallback
}
