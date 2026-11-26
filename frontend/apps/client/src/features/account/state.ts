import { computed } from 'vue'
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
    timezone: 'UTC+08:00',
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
    timezone: 'UTC+08:00',
    currentCity: '',
  },
]
export const account = localStore<Account | null>('account', null)
export const profiles = localStore<BirthProfile[]>('profiles', [])
const legacyJournal = readStorage<Omit<JournalEntry, 'date'>[]>('xuanji:mini:journal:v1', [])
export const journal = localStore<JournalEntry[]>(
  'journal',
  (Array.isArray(legacyJournal) ? legacyJournal : []).map((entry) => {
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
export const favorites = localStore<Favorite[]>('favorites', [])
export const shares = localStore<SharedItem[]>('shares', [])
export const feedback = localStore<Feedback[]>('feedback', [])
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
  return account.write(
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

export function updateAccount(changes: Partial<Account>) {
  if (!account.state.value) return false
  return account.write({ ...account.state.value, ...changes })
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
