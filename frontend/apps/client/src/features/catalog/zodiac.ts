export const signs = [
  {
    id: 'aries',
    name: '白羊座',
    glyph: '♈︎',
    range: '03.21 – 04.19',
    element: '火',
    planet: '火星',
    house: '第一宫',
    quality: '开创',
    prompt: '把最想开始的事拆成今天能完成的一步。',
    relationship: '直接说出目的，也给对方留一点回应时间。',
  },
  {
    id: 'taurus',
    name: '金牛座',
    glyph: '♉︎',
    range: '04.20 – 05.20',
    element: '土',
    planet: '金星',
    house: '第二宫',
    quality: '固定',
    prompt: '留意哪些稳定的安排值得继续。',
    relationship: '一起安排一件有具体时间和地点的小事。',
  },
  {
    id: 'gemini',
    name: '双子座',
    glyph: '♊︎',
    range: '05.21 – 06.21',
    element: '风',
    planet: '水星',
    house: '第三宫',
    quality: '变动',
    prompt: '写下最有意思的新线索，挑一条去查证。',
    relationship: '从好奇的问题开始，让交流有来有回。',
  },
  {
    id: 'cancer',
    name: '巨蟹座',
    glyph: '♋︎',
    range: '06.22 – 07.22',
    element: '水',
    planet: '月亮',
    house: '第四宫',
    quality: '开创',
    prompt: '给自己留一段能从忙碌中恢复的时间。',
    relationship: '确认哪些话题适合谈，哪些需要一点空间。',
  },
  {
    id: 'leo',
    name: '狮子座',
    glyph: '♌︎',
    range: '07.23 – 08.22',
    element: '火',
    planet: '太阳',
    house: '第五宫',
    quality: '固定',
    prompt: '分享最近一项具体进展，听听别人的观察。',
    relationship: '把感谢落到一件对方实际做过的事上。',
  },
  {
    id: 'virgo',
    name: '处女座',
    glyph: '♍︎',
    range: '08.23 – 09.22',
    element: '土',
    planet: '水星',
    house: '第六宫',
    quality: '变动',
    prompt: '挑一个反复卡住的步骤，先修好最小的细节。',
    relationship: '商量好怎么分工，也允许彼此有自己的做法。',
  },
  {
    id: 'libra',
    name: '天秤座',
    glyph: '♎︎',
    range: '09.23 – 10.23',
    element: '风',
    planet: '金星',
    house: '第七宫',
    quality: '开创',
    prompt: '遇到两种偏好时，先想清楚自己最想保留哪项。',
    relationship: '让双方都说一个当前最看重的条件。',
  },
  {
    id: 'scorpio',
    name: '天蝎座',
    glyph: '♏︎',
    range: '10.24 – 11.22',
    element: '水',
    planet: '冥王星',
    house: '第八宫',
    quality: '固定',
    prompt: '选一件在意的事深入了解，把其余问题留到下次。',
    relationship: '从感受出发，和对方核对你们理解的是否相同。',
  },
  {
    id: 'sagittarius',
    name: '射手座',
    glyph: '♐︎',
    range: '11.23 – 12.21',
    element: '火',
    planet: '木星',
    house: '第九宫',
    quality: '变动',
    prompt: '做一次小范围的新尝试，记下真实感受。',
    relationship: '试一次共同的新体验，之后各自说说收获。',
  },
  {
    id: 'capricorn',
    name: '摩羯座',
    glyph: '♑︎',
    range: '12.22 – 01.19',
    element: '土',
    planet: '土星',
    house: '第十宫',
    quality: '开创',
    prompt: '为本周的长期目标设一个看得见的进度节点。',
    relationship: '把原先模糊的时间和责任一起说清楚。',
  },
  {
    id: 'aquarius',
    name: '水瓶座',
    glyph: '♒︎',
    range: '01.20 – 02.18',
    element: '风',
    planet: '天王星',
    house: '第十一宫',
    quality: '固定',
    prompt: '换一个角度，重新讲出自己熟悉的问题。',
    relationship: '留出独立空间，再约一次明确的交流。',
  },
  {
    id: 'pisces',
    name: '双鱼座',
    glyph: '♓︎',
    range: '02.19 – 03.20',
    element: '水',
    planet: '海王星',
    house: '第十二宫',
    quality: '变动',
    prompt: '给自己的感受起个名字，看看它和近况如何相连。',
    relationship: '听完对方的感受，再复述一次你听见的重点。',
  },
]
export type Zodiac = (typeof signs)[number]
export function signById(id?: string) {
  return signs.find((sign) => sign.id === id) ?? signs[0]!
}

export function birthdaySign(value: string) {
  const monthDay = Number(value.slice(5).replace('-', ''))
  const boundaries = [321, 420, 521, 622, 723, 823, 923, 1024, 1123, 1222, 120, 219]
  const ordered = boundaries
    .map((boundary, index) => ({ boundary, sign: signs[index]! }))
    .sort((a, b) => b.boundary - a.boundary)
  return ordered.find((item) => monthDay >= item.boundary)?.sign ?? signs[9]!
}

export function compatibility(a: Zodiac, b: Zodiac) {
  const first = signs.indexOf(a)
  const second = signs.indexOf(b)
  const distance = Math.min(Math.abs(first - second), 12 - Math.abs(first - second))
  const score = a.element === b.element ? 88 + distance : 69 + [0, 4, 12, 8, 10, 6, 16][distance]!
  return { score, ease: Math.min(98, score + 4), rhythm: score - 5, space: score + 1 }
}
