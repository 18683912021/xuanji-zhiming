import { destination, go, type Query } from '../../shared/navigation'
import { refreshConversations } from '../ai/remote'
import { refreshReports } from '../ai/reports'
import { refreshReadings } from '../divination/records'
import { refreshPersonal } from './state'

export const minPasswordLength = 8
export const usernamePattern = /^[a-z][a-z0-9_]{2,23}$/i
export const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function guestReading(query: Query) {
  return [query.source, query.id].find((id) => id && /^[0-9a-f-]{36}$/i.test(id))
}

export function refreshAccountData() {
  return Promise.allSettled([refreshPersonal(), refreshReadings(), refreshConversations(), refreshReports()])
}

export function finishAuth(query: Query, moved?: string | null) {
  const { next, nextView, id, role, source, profile, report } = query
  const reading = guestReading(query)
  const handoffId = moved && reading === id ? moved : id
  const handoffSource = moved && reading === source ? moved : source
  if (next === 'ai') {
    return go(destination('ai', nextView || 'new', { id: handoffId, role, source: handoffSource, profile, report }), 'replace')
  }
  return go(destination('account', nextView || undefined, { id: handoffId, source: handoffSource }), 'replace')
}
