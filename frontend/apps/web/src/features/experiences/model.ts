import type { BaziReading } from '@/features/bazi/chart'
import type { DrawnCard } from '@/features/tarot/tarot'
import type { Yao } from '@/features/liuyao/liuyao'

type ReadingByKind = {
  tarot: { cards: DrawnCard[] }
  liuyao: { lines: Yao[] }
  bazi: BaziReading
  oracle: { title: string; verse: string; reading: string }
  dream: { mood: string }
}
export type ResultKind = keyof ReadingByKind

export type NewExperience = {
  [Kind in ResultKind]: {
    kind: Kind
    question: string
    value: ReadingByKind[Kind]
  }
}[ResultKind]

export type Experience = NewExperience & {
  id: string
  createdAt: string
  saved: boolean
  note: string
}

export type Conversation = {
  id: string
  experienceId: string
  createdAt: string
  questions: string[]
}

export const kindNames: Record<ResultKind, string> = {
  tarot: '塔罗占卜',
  liuyao: '六爻问事',
  bazi: '八字命盘',
  oracle: '占卜问签',
  dream: '梦境记录',
}
