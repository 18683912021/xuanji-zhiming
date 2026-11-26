import { readLocal, removeLocal, writeLocal } from '@/shared/storage'
import type { Yao } from './liuyao'

const draftKey = 'xuanji:v1:liuyao-draft'
type CastMode = 'cast' | 'manual'
type Draft = {
  question: string
  lines: Yao[]
  mode: CastMode
  manual: (Yao | '')[]
}

function isYao(value: unknown): value is Yao {
  return value === 6 || value === 7 || value === 8 || value === 9
}

export function loadDraft(): Draft {
  const stored = readLocal<Partial<Draft> | null>(draftKey, null)
  const manual = Array.isArray(stored?.manual) ? stored.manual : []
  return {
    question: typeof stored?.question === 'string' ? stored.question : '',
    lines: Array.isArray(stored?.lines) ? stored.lines.filter(isYao).slice(0, 6) : [],
    mode: stored?.mode === 'manual' ? 'manual' : 'cast',
    manual: Array.from({ length: 6 }, (_, index) => {
      const value = manual[index]
      return isYao(value) ? value : ''
    }),
  }
}

export function saveDraft(draft: Draft) {
  writeLocal(draftKey, draft)
}

export function clearDraft() {
  removeLocal(draftKey)
}
