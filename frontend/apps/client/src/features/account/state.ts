import { computed } from 'vue'
import { accountStore, api, apiMessage, identity, live, signOut, type Identity } from '../../shared/api'
import { toast } from '../../shared/navigation'
import { birthInput } from './birth'
import { dateKey, localStore, makeId, readStorage } from '../../shared/storage'
import type { Destination } from '../../shared/navigation'

export interface Account {
  nickname: string
  identity: string
  bio: string
  birth: string
  mbti: string
  publicBirthday: boolean
  publicSign: boolean
  publicMbti: boolean
  theme: string
}
export interface BirthProfile {
  id: string
  name: string
  relation: string
  gender: string
  date: string
  time: string
  city: string
  timezone: string
  occurrence?: string
  currentCity: string
}
export interface JournalEntry {
  id: string
  title: string
  content: string
  updated: string
  date: string
  sourceId?: string
}
export interface Favorite {
  id: string
  title: string
  to: Destination
}
export interface SharedItem {
  id: string
  title: string
  summary: string
  createdAt: string
  online?: boolean
  expiresAt?: string
}
export interface Feedback {
  id: string
  category: string
  text: string
  createdAt: string
}

export const profileExamples: BirthProfile[] = [
  {
    id: 'sample-lin',
    name: '林晚',
    relation: '示例',
    gender: '女',
    date: '1996-10-12',
    time: '09:30',
    city: '杭州',
    timezone: 'Asia/Shanghai',
    currentCity: '',
  },
  {
    id: 'sample-mu',
    name: '顾宁',
    relation: '示例',
    gender: '男',
    date: '1995-02-04',
    time: '14:15',
    city: '成都',
    timezone: 'Asia/Shanghai',
    currentCity: '',
  },
]
const demoAccount = localStore<Account | null>('account', null)

function projectAccount(user: Identity): Account {
  const details = user.details || {}
  return {
    nickname: user.display_name,
    identity: user.email || user.username || '',
    bio: String(details.bio || ''),
    birth: String(details.birth || ''),
    mbti: String(details.mbti || ''),
    publicBirthday: Boolean(details.public_birthday),
    publicSign: Boolean(details.public_sign),
    publicMbti: Boolean(details.public_mbti),
    theme: String(details.theme || '紫宸夜'),
  }
}

export const account = {
  state: computed(() => live
    ? identity.value && !identity.value.is_guest ? projectAccount(identity.value) : null
    : demoAccount.state.value),
}
export const profiles = accountStore<BirthProfile[]>('profiles', [])
const legacyJournal = readStorage<Omit<JournalEntry, 'date'>[]>('xuanji:mini:journal:v1', [])
export const journal = accountStore<JournalEntry[]>(
  'journal',
  (live || !Array.isArray(legacyJournal) ? [] : legacyJournal).map((entry) => {
    const parts = entry.updated.match(/(\d{4}) 年 (\d+) 月 (\d+) 日/)
    return {
      ...entry,
      date: parts
        ? parts
            .slice(1)
            .map((part) => part.padStart(2, '0'))
            .join('-')
        : dateKey(),
    }
  }),
)
export const favorites = accountStore<Favorite[]>('favorites', [])
export const shares = accountStore<SharedItem[]>('shares', [])
export const feedback = accountStore<Feedback[]>('feedback', [])
export const preferences = localStore('preferences', {
  sign: 'aries',
  fortuneMode: 'sign',
  reminders: true,
  messages: true,
  reducedMotion: false,
})
export const availableProfiles = computed(() => [...profiles.state.value, ...profileExamples])

export function login(identity: string) {
  const nickname = identity.trim().split('@')[0]!.slice(0, 16)
  const existing = readStorage<Account | null>('xuanji:client:last-account', null)
  return demoAccount.write(
    existing?.identity === identity
      ? existing
      : {
          nickname,
          identity,
          bio: '',
          birth: '',
          mbti: '',
          publicBirthday: false,
          publicSign: false,
          publicMbti: false,
          theme: '紫宸夜',
        },
  )
}

export async function updateAccount(changes: Partial<Account>) {
  if (!account.state.value) return false
  const value = { ...account.state.value, ...changes }
  if (!live) return demoAccount.write(value)
  try {
    identity.value = await api<Identity>('/me', {
      method: 'PUT', body: {
        display_name: value.nickname,
        details: {
          birth: value.birth || null, bio: value.bio, mbti: value.mbti, theme: value.theme,
          public_birthday: value.publicBirthday, public_sign: value.publicSign, public_mbti: value.publicMbti,
        },
      },
    })
    return true
  } catch (error) {
    toast(apiMessage(error))
    return false
  }
}

export async function logoutAccount() {
  if (live) await signOut()
  else demoAccount.write(null)
}

export function clearDemoAccount() {
  if (live) return
  uni.removeStorageSync('xuanji:client:last-account')
  demoAccount.write(null)
}

interface ApiProfile {
  id: string
  name: string
  birth: { year: number; month: number; day: number; birth_time: string | null; timezone: string; fold?: 0 | 1 | null }
  details: { relation?: string; gender?: string; city?: string; current_city?: string }
}

function profileFromApi(value: ApiProfile): BirthProfile {
  const { birth, details } = value
  return {
    id: value.id, name: value.name, relation: details.relation || '本人',
    gender: details.gender || '暂不填写', city: details.city || '',
    currentCity: details.current_city || '', timezone: birth.timezone,
    occurrence: birth.fold == null ? '' : String(birth.fold),
    time: birth.birth_time?.slice(0, 5) || '',
    date: [birth.year, birth.month, birth.day].map((part) => String(part).padStart(2, '0')).join('-'),
  }
}

interface ApiJournal {
  entry_date: string
  title: string
  body: string
  reading_id: string | null
  updated_at: string
}

function journalFromApi(value: ApiJournal): JournalEntry {
  return {
    id: value.entry_date, date: value.entry_date, title: value.title, content: value.body,
    sourceId: value.reading_id || undefined, updated: value.updated_at,
  }
}

export async function refreshPersonal() {
  const user = identity.value
  if (!live || !user || user.is_guest) return
  const [profileResult, journalResult] = await Promise.allSettled([
    api<ApiProfile[]>('/me/profiles?limit=100'),
    api<ApiJournal[]>('/me/journal?limit=100'),
  ])
  if (identity.value?.id !== user.id) return
  if (profileResult.status === 'fulfilled') profiles.write(profileResult.value.map(profileFromApi))
  if (journalResult.status === 'fulfilled') journal.write(journalResult.value.map(journalFromApi))
}

export async function saveBirthProfile(profile: BirthProfile) {
  let item = { ...profile, id: profile.id || makeId() }
  if (live) {
    const result = await api<ApiProfile>(profile.id ? '/me/profiles/' + profile.id : '/me/profiles', {
      method: profile.id ? 'PUT' : 'POST',
      body: {
        name: profile.name,
        birth: birthInput(profile.date, profile.time, profile.timezone, 'solar', false, profile.occurrence),
        details: { relation: profile.relation, gender: profile.gender, city: profile.city, current_city: profile.currentCity },
      },
    })
    item = profileFromApi(result)
  }
  profiles.write([item, ...profiles.state.value.filter((existing) => existing.id !== item.id)])
  return item
}

export async function deleteBirthProfile(id: string) {
  if (live) await api('/me/profiles/' + id, { method: 'DELETE' })
  profiles.write(profiles.state.value.filter((item) => item.id !== id))
}

export async function storeJournal(entry: JournalEntry, onlineReading: boolean) {
  const item = live ? journalFromApi(await api<ApiJournal>('/me/journal/' + entry.date, {
    method: 'PUT', body: {
      title: entry.title, body: entry.content,
      reading_id: onlineReading ? entry.sourceId : undefined,
    },
  })) : entry
  journal.write([item, ...journal.state.value.filter((existing) => existing.id !== item.id)])
  return item
}

export async function deleteJournal(entry: JournalEntry) {
  if (live) await api('/me/journal/' + entry.date, { method: 'DELETE' })
  journal.write(journal.state.value.filter((item) => item.id !== entry.id))
}

export function toggleFavorite(value: Favorite) {
  const items = favorites.state.value
  if (items.some((item) => item.id === value.id)) {
    favorites.write(items.filter((item) => item.id !== value.id))
  } else {
    favorites.write([{ ...value }, ...items])
  }
}

export function createShare(title: string, summary: string) {
  const data = { id: makeId(), title, summary, createdAt: dateKey() }
  return shares.write([data, ...shares.state.value]) ? data.id : undefined
}
