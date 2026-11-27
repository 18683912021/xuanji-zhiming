import { accountStore, live } from '../../shared/api'
import { computed } from 'vue'
import { localStore, makeId, dateKey, readPreviousWebData } from '../../shared/storage'
import { destination, type Destination } from '../../shared/navigation'
import { readings, type ReadingSection } from '../divination/records'
import { availableProfiles } from '../account/state'

export interface Role {
  id: string
  name: string
  glyph: string
  specialty: string
  opening: string
  questions: string[]
  privateRole?: boolean
}
export const officialRoles: Role[] = [
  {
    id: 'astrologer',
    name: 'AI 占星师',
    glyph: '⊙',
    specialty: '西洋本命盘与星骰',
    opening: '你想先了解某个占星概念，还是带一份盘面来一起看？',
    questions: ['怎样理解第七宫？', '可以从这份盘面看哪里？'],
  },
  {
    id: 'tarot',
    name: 'AI 塔罗师',
    glyph: '✧',
    specialty: '牌阵、牌位、正逆位',
    opening: '我们可以用当次牌面观察你的问题。你最想弄清哪一张牌？',
    questions: ['这张牌在现在的位置意味着什么？', '我能先尝试哪一件事？'],
  },
  {
    id: 'diviner',
    name: 'AI 占卜师',
    glyph: '䷀',
    specialty: '签文、卦象与动爻',
    opening: '可以带上当次的问签或卦象，看看哪条线索更贴近你的处境。',
    questions: ['怎样区分本卦与变卦？', '动爻可以怎样理解？'],
  },
  {
    id: 'dream',
    name: '解梦助手',
    glyph: '☾',
    specialty: '梦境主题与情绪记录',
    opening: '先说说醒来时最清楚的一个画面或感受。',
    questions: ['怎样整理这段梦境？', '我该记住哪些细节？'],
  },
  {
    id: 'report',
    name: '报告助手',
    glyph: '▧',
    specialty: '八字与西洋本命盘报告',
    opening: '可以打开一次体验或报告，我们一起看其中的依据。',
    questions: ['这份报告的主要结论是什么？', '哪些内容需要再确认？'],
  },
]
export const privateRoles = accountStore<Role[]>('roles', [])
export const roles = computed(() => [...officialRoles, ...privateRoles.state.value])
export function roleForReading(kind?: string) {
  if (kind === 'daily' || kind === 'tarot') return 'tarot'
  if (kind === 'oracle' || kind === 'liuyao' || kind === 'book') return 'diviner'
  if (kind === 'dream') return 'dream'
  if (kind === 'bazi' || kind === 'ziwei' || kind === 'match-bazi') return 'report'
  return 'astrologer'
}

export interface Context {
  id: string
  kind: 'reading' | 'profile' | 'report'
  title: string
  summary: string
  evidence?: ReadingSection
  to: Destination
}
export interface Message {
  id: string
  question: string
  answer?: string
  context?: Context
  status: 'complete' | 'stopped' | 'failed'
  remote?: boolean
  task?: 'general' | 'reading'
  citations?: { id: string; title: string; source: string; version: string }[]
}
export interface Session {
  id: string
  roleId: string
  roleName: string
  title: string
  context?: Context
  messages: Message[]
  updated: string
  online?: boolean
}
function previousSessions(): Session[] {
  const previous = readPreviousWebData<
    { id: string; experienceId: string; createdAt: string; questions: string[] }[]
  >('conversations', [])
  if (!Array.isArray(previous)) return []
  return previous.flatMap((item): Session[] => {
    if (!item?.id || !Array.isArray(item.questions)) return []
    const result = readings.state.value.find((entry) => entry.id === item.experienceId)
    const context = readingContext(item.experienceId)
    const roleId = roleForReading(result?.kind)
    return [
      {
        id: item.id,
        roleId,
        roleName: officialRoles.find((role) => role.id === roleId)!.name,
        title: context?.title || '原有解读对话',
        context,
        updated: item.createdAt || dateKey(),
        messages: item.questions.map((question, index) => ({
          id: item.id + '-' + index,
          question,
          context,
          status: 'stopped',
        })),
      },
    ]
  })
}

export const sessions = accountStore<Session[]>('sessions', live ? [] : previousSessions())
export const credits = accountStore('credits', { day: dateKey(), ai: 8, reports: 3 })
export const remaining = computed(() =>
  credits.state.value.day === dateKey()
    ? credits.state.value
    : {
        day: dateKey(),
        ai: 8,
        reports: 3,
      },
)

export const reportTemplates = [
  {
    id: 'bazi',
    name: '四柱与五行报告',
    category: '八字',
    description: '从日主、四柱和藏干整理当次命盘。',
    sections: ['命盘概览', '四柱结构', '行动回顾'],
  },
  {
    id: 'astro',
    name: '本命星盘报告',
    category: '占星',
    description: '沿着行星、宫位和相位阅读盘面。',
    sections: ['盘面概览', '重点配置', '延伸观察'],
  },
  {
    id: 'ziwei',
    name: '紫微十二宫报告',
    category: '紫微',
    description: '分宫查看传统主题、四化和当前流限。',
    sections: ['命身与四化', '十二宫索引', '当前阶段'],
  },
  {
    id: 'match',
    name: '关系与合盘报告',
    category: '关系',
    description: '从双方输入查看关系价值与磨合主题。',
    sections: ['双方资料', '关系主题', '沟通练习'],
  },
  {
    id: 'review',
    name: '近期自我观察报告',
    category: '通用',
    description: '从一次体验梳理主题和可复查的依据。',
    sections: ['原始体验', '回顾要点', '下一步'],
  },
]
export interface Report {
  id: string
  template: string
  title: string
  category: string
  source?: Context
  sections: ReadingSection[]
  createdAt: string
  online?: boolean
}
export const reports = accountStore<Report[]>('reports', [])

export function readingContext(id?: string): Context | undefined {
  const item = readings.state.value.find((reading) => reading.id === id)
  if (!item) return
  return {
    id: item.id,
    kind: 'reading',
    title: item.title,
    summary: item.summary,
    evidence: item.sections[0],
    to: destination('account', 'result', { id: item.id }),
  }
}
export function profileContext(id?: string): Context | undefined {
  const item = availableProfiles.value.find((profile) => profile.id === id)
  if (!item) return
  return {
    id: item.id,
    kind: 'profile',
    title: item.name + ' · 出生档案',
    summary: '已选择一份出生档案',
    to: destination(
      item.relation === '示例' ? 'charts' : 'account',
      item.relation === '示例' ? 'astro' : 'profile',
      { id: item.id },
    ),
  }
}
export function reportContext(id?: string): Context | undefined {
  const item = reports.state.value.find((report) => report.id === id)
  if (!item) return
  return {
    id: item.id,
    kind: 'report',
    title: item.title,
    summary: item.sections[0]?.content || '',
    evidence: item.sections[1],
    to: destination('ai', 'report', { id: item.id }),
  }
}

export function newSession(role: Role, context?: Context) {
  const session: Session = {
    id: makeId(),
    roleId: role.id,
    roleName: role.name,
    title: context?.title || role.name + ' · 新对话',
    context,
    messages: [],
    updated: new Date().toISOString(),
  }
  return sessions.write([session, ...sessions.state.value]) ? session : undefined
}
export function updateSession(id: string, change: Partial<Session>) {
  return sessions.write(
    sessions.state.value.map((item) =>
      item.id === id ? { ...item, ...change, updated: new Date().toISOString() } : item,
    ),
  )
}

export function mockReply(
  role: Role | undefined,
  question: string,
  context?: Context,
  history: Message[] = [],
) {
  const prior = history.filter((item) => item.status === 'complete').at(-1)
  const lead = '关于「' + question.slice(0, 72) + '」，'
  if (!context) {
    return (
      lead +
      (role?.id === 'astrologer'
        ? '可以先把占星概念拆成行星、星座与宫位来理解。个人盘面问题需要先关联一份命盘或出生档案。'
        : '可以先说出你最想看清的一个条件。若问题涉及某次测算，请先关联那份结果，就能一起看其中的依据。')
    )
  }
  const fact = context.evidence
    ? '「' + context.evidence.title + '」的记录是：' + context.evidence.content
    : '当前关联的是「' +
      context.title +
      '」。' +
      (context.kind === 'profile' ? '可先打开档案排一张盘，再用对应的行星或宫位验证问题。' : context.summary)
  return (
    lead +
    fact +
    (prior ? '\n上一次你问了「' + prior.question.slice(0, 45) + '」。可以对照两次问题共有的一条线索。' : '') +
    '\n下一步，可以挑出一件今天能够观察或核对的事。'
  )
}
