import { dateKey, localStore, makeId, readPreviousWebData } from '../../shared/storage'
import { cards, type DrawnCard } from './tarot'
import { hexagram, type Yao } from './liuyao'
import type { BaziReading } from '../charts/bazi'
import { destination, type Destination } from '../../shared/navigation'

export interface ReadingSection {
  title: string
  content: string
}
export interface Reading {
  id: string
  kind: string
  title: string
  topic: string
  summary: string
  sections: ReadingSection[]
  createdAt: string
  date: string
  note: string
  saved: boolean
  version: string
  cards?: DrawnCard[]
  lines?: Yao[]
  bazi?: BaziReading
  source?: Destination
}

type PreviousReading = {
  id: string
  question: string
  createdAt: string
  note: string
  saved: boolean
} & (
  | { kind: 'tarot'; value: { cards: DrawnCard[] } }
  | { kind: 'bazi'; value: BaziReading }
  | { kind: 'liuyao'; value: { lines: Yao[] } }
  | { kind: 'oracle'; value: { title: string; verse: string; reading: string } }
  | { kind: 'dream'; value: { mood: string } }
)

function previousReadings(): Reading[] {
  const previous = readPreviousWebData<PreviousReading[]>('results', [])
  if (!Array.isArray(previous)) return []
  return previous.flatMap((item): Reading[] => {
    if (!item?.value || !item.id || typeof item.createdAt !== 'string') return []
    const common = {
      id: item.id,
      kind: item.kind,
      topic: item.question || '',
      date: item.createdAt.slice(0, 10),
      createdAt: item.createdAt,
      note: item.note || '',
      saved: item.saved,
      version: 'prototype-v1',
    }
    switch (item.kind) {
      case 'tarot':
        return [
          {
            ...common,
            title: '塔罗占卜',
            summary: item.value.cards.map((card) => cards[card.index]?.[0]).join(' · '),
            cards: item.value.cards,
            sections: item.value.cards.map((card) => ({
              title: card.position,
              content: cards[card.index]?.[card.reversed ? 2 : 1] || '',
            })),
            source: destination('divination', 'tarot'),
          },
        ]
      case 'bazi':
        return [
          {
            ...common,
            title: '八字命盘',
            summary: item.value.pillars.map((pillar) => pillar.text).join(' · '),
            sections: [],
            bazi: item.value,
            source: destination('charts', 'bazi'),
          },
        ]
      case 'liuyao':
        return [
          {
            ...common,
            title: '六爻问事',
            summary: hexagram(item.value.lines),
            lines: item.value.lines,
            sections: [],
            source: destination('divination', 'liuyao'),
          },
        ]
      case 'oracle':
        return [
          {
            ...common,
            title: '问签 · ' + item.value.title,
            summary: item.value.verse,
            sections: [{ title: '签文释义', content: item.value.reading }],
            source: destination('divination', 'oracle'),
          },
        ]
      case 'dream':
        return [
          {
            ...common,
            title: '梦境记录',
            summary: '醒来的感受 · ' + item.value.mood,
            sections: [],
            source: destination('divination', 'dream'),
          },
        ]
      default:
        return []
    }
  })
}

export const readings = localStore<Reading[]>('readings', previousReadings())

export function createReading(
  input: Omit<Reading, 'id' | 'createdAt' | 'date' | 'note' | 'saved' | 'version'>,
  saved = false,
) {
  const item = {
    ...input,
    id: makeId(),
    date: dateKey(),
    createdAt: new Date().toISOString(),
    note: '',
    saved,
    version: 'mock-v1',
  }
  return readings.write([item, ...readings.state.value]) ? item : undefined
}

export function updateReading(id: string, patch: Partial<Pick<Reading, 'note' | 'saved'>>) {
  return readings.write(readings.state.value.map((item) => (item.id === id ? { ...item, ...patch } : item)))
}
