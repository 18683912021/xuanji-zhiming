import { dateKey, makeId, readPreviousWebData } from '../../shared/storage'
import { accountStore, api, identity, live, requireVisitor } from '../../shared/api'
import { type NatalResult } from '../charts/astro'
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
  online?: boolean
  natal?: NatalResult
  dice?: { planet: number; sign: string; house: number }
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

export const readings = accountStore<Reading[]>('readings', live ? [] : previousReadings())

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

export async function updateReading(id: string, patch: Partial<Pick<Reading, 'note' | 'saved'>>) {
  const item = readings.state.value.find((value) => value.id === id)
  if (item?.online) {
    remember(project(await api<ApiReading>('/readings/' + id, { method: 'PUT', body: patch })))
    return true
  }
  return readings.write(readings.state.value.map((value) => value.id === id ? { ...value, ...patch } : value))
}

export async function removeReading(id: string) {
  if (readings.state.value.find((item) => item.id === id)?.online) await api('/readings/' + id, { method: 'DELETE' })
  return readings.write(readings.state.value.filter((item) => item.id !== id))
}

type WireResult =
  | { kind: 'tarot' | 'daily'; result: { spread: { id: string; name: string }; cards: (DrawnCard & { name: string; meaning: string })[] } }
  | { kind: 'oracle'; result: { title: string; verse: string; reading: string; source: string } }
  | { kind: 'liuyao'; result: { hexagram: string; changed_hexagram: string | null; moving_lines: number[]; lines: { name: string; value: Yao }[] } }
  | { kind: 'bazi'; result: {
    solar_date: string; timezone: string; day_boundary: string;
    birth_snapshot: { calendar: string; birth_time: string | null };
    pillars: Record<string, { ganzhi: string; elements: string; hidden_stems: string[]; stem_ten_god: string | null; nayin: string; void: string; growth_stage?: string | null } | null>;
  } }
  | { kind: 'astro'; result: NatalResult }
  | { kind: 'dice'; result: { planet_index: number; planet: string; sign: string; sign_name: string; house: number } }
  | { kind: 'book'; result: { answer: string } }
  | { kind: 'dream'; result: { mood: string } }

type ApiReading = WireResult & {
  id: string
  note: string
  saved: boolean
  rules_version: string
  created_at: string
  request_data: { question?: string; date?: string; text?: string }
}

function project(value: ApiReading): Reading {
  const common = {
    id: value.id, kind: value.kind, createdAt: value.created_at,
    date: value.request_data.date || dateKey(new Date(value.created_at)),
    topic: value.request_data.question || '', note: value.note || '', saved: value.saved,
    version: value.rules_version, online: true,
  }
  switch (value.kind) {
    case 'tarot':
    case 'daily': {
      const daily = value.kind === 'daily'
      return {
        ...common, title: daily ? '今日塔罗' : '塔罗 · ' + value.result.spread.name,
        summary: value.result.cards.map((card) => card.name + ' · ' + (card.reversed ? '逆位' : '正位')).join(' / '),
        cards: value.result.cards.map((card) => ({ ...card, position: daily ? '今日' : card.position })),
        sections: value.result.cards.map((card) => ({
          title: (daily ? '今日' : card.position) + ' · ' + card.name,
          content: card.meaning,
        })),
        source: destination('divination', value.kind, { spread: value.result.spread.id }),
      }
    }
    case 'oracle':
      return {
        ...common, title: '问签 · ' + value.result.title, summary: value.result.verse,
        sections: [{ title: '签文释义', content: value.result.reading }, { title: '出处', content: value.result.source }],
        source: destination('divination', 'oracle'),
      }
    case 'liuyao': {
      const { result } = value
      return {
        ...common, title: '六爻 · ' + result.hexagram,
        summary: result.hexagram + (result.changed_hexagram ? ' → ' + result.changed_hexagram : ' · 静卦'),
        lines: result.lines.map((line) => line.value),
        sections: [{
          title: '爻序与动爻', content: result.moving_lines.length
            ? '动爻为' + result.moving_lines.map((index) => result.lines[index - 1]?.name).join('、') + '，由下往上读取。'
            : '此卦无动爻。',
        }],
        source: destination('divination', 'liuyao'),
      }
    }
    case 'bazi': {
      const result = value.result
      const pillars = ['year', 'month', 'day', 'hour'].map((name, index) => {
        const data = result.pillars[name]
        return {
          label: ['年柱', '月柱', '日柱', '时柱'][index]!,
          text: data?.ganzhi || (name === 'hour' ? '时辰不详' : '待确定'),
          elements: data?.elements || '—', hidden: data?.hidden_stems.join('、') || '—',
          deity: data?.stem_ten_god || undefined, sound: data?.nayin, void: data?.void, stage: data?.growth_stage || undefined,
        }
      })
      return {
        ...common, title: '八字命盘', summary: pillars.map((item) => item.text).join(' · '),
        sections: [
          { title: '出生资料快照', content: result.solar_date + ' · ' + (result.birth_snapshot.birth_time || '时辰不详') + ' · ' + result.timezone },
          { title: '排盘口径', content: '当地钟表时刻 · ' + (result.day_boundary === 'local_23' ? '23 时换日' : '午夜换日') },
        ],
        bazi: {
          pillars, solarDate: result.solar_date, lateZi: result.day_boundary === 'local_23',
          calendar: result.birth_snapshot.calendar === 'lunar' ? '农历输入' : '公历输入',
        },
        source: destination('charts', 'bazi'),
      }
    }
    case 'dice': {
      const result = value.result
      return {
        ...common, title: '星座骰子',
        summary: result.planet + ' · ' + result.sign_name + ' · 第' + result.house + '宫',
        dice: { planet: result.planet_index, sign: result.sign, house: result.house - 1 },
        sections: [{ title: '本次结果', content: '从行星、星座和宫位三个角度梳理问题。' }],
        source: destination('divination', 'dice'),
      }
    }
    case 'book':
      return {
        ...common, title: '答案之书', summary: value.result.answer,
        sections: [{ title: '留给自己', content: '这句话让你最先想到哪件眼下可以尝试的事？' }],
        source: destination('divination', 'book'),
      }
    case 'dream':
      return {
        ...common, title: '梦境记录', topic: value.request_data.text || '',
        summary: '醒来的感受 · ' + value.result.mood,
        sections: [{ title: '梦境观察', content: '记录醒来时的感受，也可以带上这份记录与解梦助手继续对话。' }],
        source: destination('divination', 'dream'),
      }
    case 'astro':
      return {
        ...common, title: '西洋本命盘', summary: '上升点 ' + value.result.ascendant.toFixed(2) + '°',
        natal: value.result,
        sections: value.result.planets.map((body) => ({
          title: body.name, content: body.longitude.toFixed(2) + '° · 第 ' + body.house + ' 宫' + (body.retrograde ? ' · 逆行' : ''),
        })),
        source: destination('charts', 'astro'),
      }
  }
}

function remember(item: Reading) {
  readings.write([item, ...readings.state.value.filter((value) => value.id !== item.id)])
  return item
}

export async function performReading(kind: WireResult['kind'], payload: object, key: string, timezone?: string) {
  const user = await requireVisitor()
  const path = kind === 'daily' ? 'daily-tarot?timezone=' + encodeURIComponent(timezone || 'Asia/Shanghai') : kind
  const result = await api<ApiReading>('/readings/' + path, { method: 'POST', body: payload, key })
  const item = project(result)
  if (identity.value?.id === user.id) remember(item)
  return item
}

export async function refreshReadings() {
  const user = identity.value
  if (!live || !user) return
  const values = await api<ApiReading[]>('/readings?limit=100')
  if (identity.value?.id !== user.id) return
  const items = [...values.map(project), ...readings.state.value.filter((item) => !item.online)]
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  readings.write(items)
}

export async function fetchReading(id: string) {
  if (!live || !identity.value || !/^[a-f0-9-]{36}$/i.test(id)) return
  const user = identity.value.id
  const item = project(await api<ApiReading>('/readings/' + id))
  if (identity.value?.id === user) remember(item)
}
