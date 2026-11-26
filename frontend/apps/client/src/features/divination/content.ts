export const spreads = [
  { id: 'single', name: '当下一张', positions: ['此刻'], guide: '把一个宽泛的顾虑具体化。' },
  {
    id: 'timeline',
    name: '过去 · 现在 · 未来',
    positions: ['过去', '现在', '未来'],
    guide: '把既有条件、当下状态与下一步分开观察。',
  },
  {
    id: 'relationship',
    name: '关系探索',
    positions: ['我在意的', '对方可能在意的', '适合的沟通'],
    guide: '准备一项能和对方核对的沟通问题。',
  },
  {
    id: 'choices',
    name: '两难选择',
    positions: ['选项 A', '选项 B', '决策依据'],
    guide: '列出两个选项，再补一个可比较的条件。',
  },
  {
    id: 'review',
    name: '阶段回顾',
    positions: ['已有进展', '暂时阻力', '接下来'],
    guide: '回看这一阶段的实际进展，选一个小目标。',
  },
]

export const verses = [
  {
    title: '云开见月',
    verse: '云行山未动，静水自明月。',
    reading: '把已知和仍需验证的事分开，先核实一个有答案的疑问。',
  },
  {
    title: '松间缓行',
    verse: '松间有微径，缓步到清泉。',
    reading: '把大问题拆成小行动，选一项最容易开始且可以复盘的。',
  },
  {
    title: '潮退见岸',
    verse: '静候一潮落，方知岸几重。',
    reading: '先记录当下的情绪，允许信息多一点时再做判断。',
  },
  {
    title: '晨光入窗',
    verse: '不待长夜尽，微光已入窗。',
    reading: '先找一个已经可用的人、物或时间段，再试一个小变化。',
  },
]

export const answerPages = [
  '今天先做一件可逆的小事。',
  '从对方的角度重新说一遍。',
  '让问题具体到一个日期。',
  '给自己一天重新观察。',
  '先问一个真正想知道的问题。',
  '把手上已有的线索列出来。',
  '暂时留一个备选方案。',
  '记下什么会让你改变主意。',
]

export const planets = ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星', '天王星', '海王星', '冥王星']
export const planetThemes = ['表达', '感受', '沟通', '吸引', '行动', '扩展', '边界', '突破', '想象', '更新']
export const houses = [
  '自我',
  '资源',
  '交流',
  '家庭',
  '创造',
  '日常',
  '关系',
  '共享',
  '远行',
  '事业',
  '社群',
  '内省',
]

export function sample<T>(items: readonly T[]): T {
  return items[Math.floor(Math.random() * items.length)]!
}

export const dreamTopics = [
  {
    name: '在路上',
    text: '我走在一条没见过的路上，越走越安静。',
    note: '可以把道路看成场景转换，记录这段路让你想靠近什么。',
  },
  {
    name: '水与雨',
    text: '窗外一直下雨，我在等一个人敲门。',
    note: '先留意水带来的身体感受。醒来后最先想到的事情，可能能提示这个梦对你的意义。',
  },
  {
    name: '飞翔',
    text: '我好像在低空飞，能看见屋顶和树梢。',
    note: '试着分辨飞起时更接近轻松、兴奋，还是控制感的变化。',
  },
]
