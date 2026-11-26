import { localStore } from '../../shared/storage'
import type { Yao } from './liuyao'

export const liuyaoDraft = localStore('liuyao-draft', {
  question: '',
  lines: [] as Yao[],
  method: 'coins',
})
