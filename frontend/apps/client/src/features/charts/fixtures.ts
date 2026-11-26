import { signs } from '../catalog/zodiac'
import { houses, planets } from '../divination/content'

export const astroTypes = [
  '本命盘',
  '天象盘',
  '行运盘',
  '三限盘',
  '次限盘',
  '月返盘',
  '日返盘',
  '日弧盘',
  '法达盘',
  '小限盘',
  '地点重置盘',
]
export const synastryTypes = ['比较盘 A', '比较盘 B', '组合盘', '马盘 A', '马盘 B', '时空盘', '双盘行运']
export const ziweiHouses = [
  '命宫',
  '兄弟',
  '夫妻',
  '子女',
  '财帛',
  '疾厄',
  '迁移',
  '交友',
  '官禄',
  '田宅',
  '福德',
  '父母',
]
const ziweiStars = [
  '紫微',
  '天机',
  '太阳',
  '武曲',
  '天同',
  '廉贞',
  '天府',
  '太阴',
  '贪狼',
  '巨门',
  '天相',
  '天梁',
  '七杀',
  '破军',
]
export const mansions = [
  ['东方青龙', '角 亢 氐 房 心 尾 箕'],
  ['北方玄武', '斗 牛 女 虚 危 室 壁'],
  ['西方白虎', '奎 娄 胃 昴 毕 觜 参'],
  ['南方朱雀', '井 鬼 柳 星 张 翼 轸'],
] as const
export const cycleTypes = ['大运', '流年', '流月', '流日', '流时']
const aspects = ['合相', '六合', '刑相', '拱相', '对冲']
export const baseSettings = {
  preset: '现代',
  zodiac: '回归黄道',
  house: '普拉西德',
  extras: false,
  text: true,
  orb: '6',
  lateZi: false,
  solar: false,
}
export const astrologyKnowledge = [
  {
    id: 'planet',
    title: '行星',
    body: '行星传统上对应不同的表达、感受、沟通或行动主题。阅读时结合星座与宫位。',
  },
  {
    id: 'house',
    title: '十二宫',
    body: '宫位用于组织生活领域，例如第一宫与自我呈现、第七宫与一对一关系、第十宫与公共角色。',
  },
  { id: 'aspect', title: '相位', body: '相位描述两颗星体的角度关系，容许度用来表示与标准角度的最大偏离。' },
  {
    id: 'firdaria',
    title: '法达',
    body: '法达把人生历程按主导星体划为若干阶段。体验盘仅列出周期表的呈现样式。',
  },
]
export function fixtureSeed(value: string) {
  return Array.from(value).reduce((number, part) => (Math.imul(number, 31) + part.charCodeAt(0)) >>> 0, 7)
}
export function chartFixture(seed: number, extras: boolean) {
  return [...planets, ...(extras ? ['凯龙星', '婚神星', '北交点'] : [])].map((planet, index) => {
    const degree = ((seed % 360) + index * 37 + index * index * 3) % 360
    const house = Math.floor(((degree + 29) % 360) / 30)
    return {
      planet,
      degree,
      house: house + 1,
      topic: houses[house]!,
      sign: signs[Math.floor(degree / 30)]!,
      retrograde: index > 2 && (index + seed) % 5 === 0,
      aspect: aspects[(seed + index) % aspects.length]!,
    }
  })
}
export function ziweiFixture(seed: number) {
  return ziweiHouses.map((label, index) => ({
    label,
    star: ziweiStars[(seed + index * 3) % ziweiStars.length]!,
    transformation: ['化禄', '化权', '化科', '化忌', '—', '—'][(seed + index) % 6]!,
    period: 5 + index * 10 + '–' + (14 + index * 10) + ' 岁',
  }))
}
