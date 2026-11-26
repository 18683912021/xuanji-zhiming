export interface JournalEntry {
  id: string
  title: string
  content: string
  updated: string
}
const key = 'xuanji:mini:journal:v1'

export function journal() {
  try {
    const data = uni.getStorageSync(key)
    return Array.isArray(data) ? (data as JournalEntry[]) : []
  } catch {
    return []
  }
}

export function storeEntry(input: { id: string; title: string; content: string }) {
  const data = journal()
  const now = new Date()
  const updated = `${now.getFullYear()} 年 ${now.getMonth() + 1} 月 ${now.getDate()} 日`
  const id = input.id || `${now.getTime()}-${Math.random().toString(36).slice(2, 8)}`
  uni.setStorageSync(key, [{ ...input, id, updated }, ...data.filter((entry) => entry.id !== id)])
}

export function deleteEntry(id: string) {
  uni.setStorageSync(
    key,
    journal().filter((entry) => entry.id !== id),
  )
}
