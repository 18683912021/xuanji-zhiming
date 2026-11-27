import { api, identity, live, streamPost } from '../../shared/api'
import { readings, fetchReading } from '../divination/records'
import { officialRoles, readingContext, sessions, type Message, type Role, type Session } from './state'

interface ApiConversation {
  id: string
  role: string
  title: string
  reading_id: string | null
  updated_at: string
}

interface ApiTurn {
  client_message_id: string
  question: string
  status: 'running' | 'stopped' | 'failed' | 'complete'
  reply: { text: string; citations: NonNullable<Message['citations']>; follow_up: string | null } | null
  error_code: string | null
  task: 'general' | 'reading'
}

export const roleKinds: Record<string, string[]> = {
  astrologer: ['astro', 'dice'], tarot: ['tarot', 'daily'], diviner: ['liuyao', 'oracle', 'book'],
  dream: ['dream'], report: ['astro', 'bazi'],
}

export function cloudRole(role: string) {
  return live && Object.prototype.hasOwnProperty.call(roleKinds, role)
}

function fromApi(value: ApiConversation, messages: Message[] = []): Session {
  return {
    id: value.id, roleId: value.role,
    roleName: officialRoles.find((role) => role.id === value.role)?.name || value.role,
    title: value.title, context: readingContext(value.reading_id || undefined),
    messages, updated: value.updated_at, online: true,
  }
}

function setSession(value: Session) {
  sessions.write([value, ...sessions.state.value.filter((item) => item.id !== value.id)])
  return value
}

function mapTurn(value: ApiTurn): Message {
  const citations = value.reply?.citations
  const context = citations?.map((citation) => readingContext(citation.id)).find(Boolean)
  return {
    id: value.client_message_id, question: value.question,
    status: value.status === 'running' ? 'stopped' : value.status,
    answer: value.reply?.text, citations, context, remote: true, task: value.task,
  }
}

export async function refreshConversations() {
  const user = identity.value
  if (!live || !user || user.is_guest) return
  const items = await api<ApiConversation[]>('/ai/conversations?limit=100')
  if (identity.value?.id !== user.id) return
  const old = sessions.state.value
  sessions.write([
    ...items.map((item) => fromApi(item, old.find((value) => value.id === item.id)?.messages)),
    ...old.filter((item) => !item.online),
  ])
}

export async function hydrateConversation(id: string) {
  const user = identity.value
  if (!live || !user || user.is_guest || !/^[a-f0-9-]{36}$/i.test(id)) return
  const [meta, turns] = await Promise.all([
    api<ApiConversation>('/ai/conversations/' + id),
    api<ApiTurn[]>('/ai/conversations/' + id + '/turns?limit=100'),
  ])
  if (meta.reading_id && !readings.state.value.some((item) => item.id === meta.reading_id))
    await fetchReading(meta.reading_id).catch(() => undefined)
  if (identity.value?.id === user.id) setSession(fromApi(meta, turns.map(mapTurn)))
}

export async function newRemoteSession(role: Role, readingId?: string) {
  const item = await api<ApiConversation>('/ai/conversations', {
    method: 'POST', body: { role: role.id, reading_id: readingId, title: readingContext(readingId)?.title },
  })
  return setSession(fromApi(item))
}

export async function updateRemoteSession(item: Session, change: { reading_id?: string | null; title?: string }) {
  const value = await api<ApiConversation>('/ai/conversations/' + item.id, { method: 'PUT', body: change })
  return setSession(fromApi(value, item.messages))
}

export async function removeRemoteSession(id: string) {
  await api('/ai/conversations/' + id, { method: 'DELETE' })
  sessions.write(sessions.state.value.filter((item) => item.id !== id))
}

export function sendRemoteTurn(
  session: Session, message: Message, onEvent: (event: string, reply: Message, code: string | null) => void,
) {
  const owner = identity.value?.id
  return streamPost<ApiTurn>('/ai/conversations/' + session.id + '/turns', {
    client_message_id: message.id,
    text: message.question,
    task: message.task || 'general',
    retry: Boolean(message.remote),
  }, (event, wire) => {
    if (identity.value?.id === owner) onEvent(event, mapTurn(wire), wire.error_code)
  })
}
