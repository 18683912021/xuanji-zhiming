import { dateKey, localStore } from '../../shared/storage'

export interface Person {
  id: string
  name: string
  sign: string
  birthday: string
  bio: string
  type: string
  color: string
  reason: string
  willing: boolean
}
export const people: Person[] = [
  {
    id: 'lin',
    name: '林晚',
    sign: 'libra',
    birthday: '10-12',
    bio: '喜欢散步，记城市里的月亮和树。',
    type: 'INFP',
    color: '#563862',
    reason: '常分享月相和散步笔记，偏好安静的一对一交流。',
    willing: true,
  },
  {
    id: 'mu',
    name: '顾宁',
    sign: 'aquarius',
    birthday: '02-04',
    bio: '最近在学着认几组北天星座。',
    type: 'INTP',
    color: '#3f395e',
    reason: '也在关注星象日历，可以一起聊一条近期星象。',
    willing: true,
  },
  {
    id: 'he',
    name: '叶禾',
    sign: 'libra',
    birthday: '10-12',
    bio: '在做一本日常颜色手账。',
    type: 'ISFP',
    color: '#5b3b4e',
    reason: '愿意交流每日记录，喜欢以写作认识朋友。',
    willing: false,
  },
]
export interface SocialPost {
  id: string
  user: string
  body: string
  date: string
  likes: number
  liked: boolean
  image?: string
}
export interface SocialMessage {
  id: string
  from: 'me' | 'peer'
  body: string
  type: 'text' | 'image' | 'card'
  date: string
}
export interface Room {
  user: string
  messages: SocialMessage[]
  unread: boolean
}
export interface Notice {
  id: string
  title: string
  copy: string
  category: string
  unread: boolean
}
export interface Invite {
  id: string
  user: string
  reason: string
  first: string
  second: string
  direction: 'inbound' | 'outbound'
  status: 'pending' | 'accepted' | 'revoked' | 'declined'
}
export const connections = localStore('social-connections', {
  following: [] as string[],
  blocked: [] as string[],
  liked: [] as string[],
  skipped: [] as string[],
  matching: false,
})
export const posts = localStore<SocialPost[]>('social-posts', [
  {
    id: 'post-lin',
    user: 'lin',
    body: '晚饭后在河边看了几分钟月亮，回家把夜色画进手账。',
    date: dateKey(),
    likes: 12,
    liked: false,
  },
  {
    id: 'post-mu',
    user: 'mu',
    body: '这周想找一个能看清北斗的位置，有人在做星象记录吗？',
    date: dateKey(),
    likes: 8,
    liked: false,
  },
  {
    id: 'post-he',
    user: 'he',
    body: '今天把桌上的旧书整理好，重新留出一块地方写字。',
    date: dateKey(),
    likes: 6,
    liked: false,
  },
])
export const rooms = localStore<Room[]>('social-rooms', [
  {
    user: 'lin',
    unread: true,
    messages: [
      { id: 'hello', from: 'peer', body: '你好，我看到你也在关注今日星象。', type: 'text', date: dateKey() },
    ],
  },
])
export const notices = localStore<Notice[]>('social-notices', [
  {
    id: 'n1',
    title: '顾宁关注了你',
    copy: '可以打开对方主页了解共同话题。',
    category: '关注与互动',
    unread: true,
  },
  {
    id: 'n2',
    title: '今天可以翻开日签',
    copy: '已领取的日签会保存在今日记录中。',
    category: '活动与提醒',
    unread: false,
  },
])
export const invites = localStore<Invite[]>('social-invites', [
  {
    id: 'inv1',
    user: 'mu',
    reason: '想用示例档案看看西洋合盘布局。',
    first: 'sample-lin',
    second: 'sample-mu',
    direction: 'inbound',
    status: 'pending',
  },
])
