import { api, identity, live } from '../../shared/api'
import { readingContext, reports, type Report } from './state'

interface ApiReport {
  id: string
  reading_id: string | null
  template: string
  title: string
  category: string
  sections: Report['sections']
  created_at: string
}

export const onlineTemplates = ['astro', 'bazi', 'review']

function project(value: ApiReport): Report {
  return {
    id: value.id, template: value.template, title: value.title, category: value.category,
    source: readingContext(value.reading_id || undefined),
    sections: value.sections, createdAt: value.created_at.slice(0, 10), online: true,
  }
}

function remember(item: Report) {
  reports.write([item, ...reports.state.value.filter((value) => value.id !== item.id)])
  return item
}

export async function refreshReports() {
  const user = identity.value
  if (!live || !user || user.is_guest) return
  const result = await api<ApiReport[]>('/reports?limit=100')
  if (identity.value?.id === user.id)
    reports.write([...result.map(project), ...reports.state.value.filter((item) => !item.online)])
}

export async function hydrateReport(id: string) {
  const user = identity.value
  if (!live || !user || user.is_guest || !/^[a-f0-9-]{36}$/i.test(id)) return
  const item = project(await api<ApiReport>('/reports/' + id))
  if (identity.value?.id === user.id) remember(item)
}

export async function generateRemoteReport(template: string, readingId: string, key: string) {
  return remember(project(await api<ApiReport>('/reports', {
    method: 'POST', body: { template, reading_id: readingId }, key,
  })))
}

export async function deleteRemoteReport(id: string) {
  await api('/reports/' + id, { method: 'DELETE' })
  reports.write(reports.state.value.filter((item) => item.id !== id))
}
