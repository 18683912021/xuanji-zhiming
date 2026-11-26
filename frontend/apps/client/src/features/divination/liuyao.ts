export type Yao = 6 | 7 | 8 | 9
export const yaoNames = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻'] as const
export const yaoLabels: Record<Yao, string> = { 6: '老阴', 7: '少阳', 8: '少阴', 9: '老阳' }
export const isYin = (value: Yao) => value % 2 === 0
export const isMoving = (value: Yao) => value === 6 || value === 9

const patterns = ['111', '110', '101', '100', '011', '010', '001', '000']
const names = [
  ['乾', '履', '同人', '无妄', '姤', '讼', '遁', '否'],
  ['夬', '兑', '革', '随', '大过', '困', '咸', '萃'],
  ['大有', '睽', '离', '噬嗑', '鼎', '未济', '旅', '晋'],
  ['大壮', '归妹', '丰', '震', '恒', '解', '小过', '豫'],
  ['小畜', '中孚', '家人', '益', '巽', '涣', '渐', '观'],
  ['需', '节', '既济', '屯', '井', '坎', '蹇', '比'],
  ['大畜', '损', '贲', '颐', '蛊', '蒙', '艮', '剥'],
  ['泰', '临', '明夷', '复', '升', '师', '谦', '坤'],
] as const

export function hexagram(lines: Yao[]) {
  const pattern = (part: Yao[]) => patterns.indexOf(part.map((v) => (isYin(v) ? '0' : '1')).join(''))
  return names[pattern(lines.slice(3, 6))]?.[pattern(lines.slice(0, 3))] ?? '未成卦'
}

export function changed(lines: Yao[]): Yao[] {
  return lines.map((v) => (v === 6 ? 7 : v === 9 ? 8 : v))
}

export function castCoins() {
  const coins = Array.from({ length: 3 }, () => (Math.random() < 0.5 ? 2 : 3))
  return { coins, value: coins.reduce<number>((sum, coin) => sum + coin, 0) as Yao }
}
