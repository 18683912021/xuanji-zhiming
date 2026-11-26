import { destination, type Destination } from '../../shared/navigation'

export type Tool = {
  title: string
  description: string
  glyph: string
  to: Destination
  group: string
  keywords?: string
}

export const tools: Tool[] = [
  {
    title: '八字命盘',
    description: '排四柱，查五行与藏干',
    glyph: '☯',
    to: destination('charts', 'bazi'),
    group: '排盘',
    keywords: '生辰 四柱',
  },
  {
    title: '塔罗占卜',
    description: '选牌阵，翻开当次牌面',
    glyph: '✧',
    to: destination('divination', 'tarot'),
    group: '占卜',
  },
  {
    title: '六爻问事',
    description: '三钱起卦或手动录爻',
    glyph: '䷀',
    to: destination('divination', 'liuyao'),
    group: '占卜',
  },
  {
    title: '占卜问签',
    description: '抽一则原创签文',
    glyph: '籤',
    to: destination('divination', 'oracle'),
    group: '占卜',
  },
  {
    title: '十二星座',
    description: '查属性、守护星和象征',
    glyph: '♈',
    to: destination('explore', 'zodiac'),
    group: '星座与关系',
  },
  {
    title: '星座运势',
    description: '查看每日与近期主题',
    glyph: '☾',
    to: destination('today', 'fortune'),
    group: '星座与关系',
  },
  {
    title: '西洋星盘',
    description: '在一张盘里查看行星与宫位',
    glyph: '⊙',
    to: destination('charts', 'astro'),
    group: '排盘',
    keywords: '本命 行运',
  },
  {
    title: '紫微斗数',
    description: '查看十二宫、四化与大限',
    glyph: '✦',
    to: destination('charts', 'ziwei'),
    group: '排盘',
  },
  {
    title: '二十八星宿',
    description: '查本命、值日和星宿关系',
    glyph: '⋇',
    to: destination('charts', 'mansion'),
    group: '排盘',
  },
  {
    title: '八字流盘',
    description: '查看各时期与原局的关系',
    glyph: '☯',
    to: destination('charts', 'cycles'),
    group: '排盘',
    keywords: '大运 流年',
  },
  {
    title: '八字合盘',
    description: '对照双方四柱与五行',
    glyph: '◇',
    to: destination('charts', 'match-bazi'),
    group: '星座与关系',
  },
  {
    title: '西洋合盘',
    description: '比较盘、组合盘和关系相位',
    glyph: '◎',
    to: destination('charts', 'match-astro'),
    group: '星座与关系',
  },
  {
    title: '缘分合盘',
    description: '查看互动维度与沟通建议',
    glyph: '❋',
    to: destination('charts', 'match'),
    group: '星座与关系',
  },
  {
    title: '星座配对',
    description: '比较两个星座或查看排行',
    glyph: '♡',
    to: destination('explore', 'compatibility'),
    group: '星座与关系',
  },
  {
    title: '心动匹配',
    description: '认识有共同话题的朋友',
    glyph: '♡',
    to: destination('social', 'matching'),
    group: '星座与关系',
  },
  {
    title: '同生日匹配',
    description: '发现同一天生日的朋友',
    glyph: '♧',
    to: destination('social', 'birthday'),
    group: '星座与关系',
  },
  {
    title: '星座骰子',
    description: '掷出行星、星座与宫位',
    glyph: '⚄',
    to: destination('divination', 'dice'),
    group: '占卜',
  },
  {
    title: '答案之书',
    description: '翻一页，得到一句反思提示',
    glyph: '▤',
    to: destination('divination', 'book'),
    group: '占卜',
  },
  {
    title: '每日塔罗',
    description: '翻开今天的塔罗日签',
    glyph: '☼',
    to: destination('divination', 'daily'),
    group: '占卜',
  },
  {
    title: '许愿与接好运',
    description: '写下愿望，给彼此一点回应',
    glyph: '✹',
    to: destination('divination', 'wishes'),
    group: '轻测算',
  },
  {
    title: 'AI 解梦',
    description: '记录梦境和醒来的感受',
    glyph: '☽',
    to: destination('divination', 'dream'),
    group: '轻测算',
  },
  {
    title: '手相',
    description: '看传统手纹释义示例',
    glyph: '掌',
    to: destination('divination', 'palm'),
    group: '轻测算',
  },
  {
    title: '面相',
    description: '看传统面部文化条目',
    glyph: '相',
    to: destination('divination', 'face'),
    group: '轻测算',
  },
  {
    title: 'MBTI 测试',
    description: '28 道题，回顾四组偏好',
    glyph: '▦',
    to: destination('divination', 'mbti'),
    group: '轻测算',
  },
  {
    title: '深度报告',
    description: '从盘面和实际结果展开阅读',
    glyph: '▧',
    to: destination('ai', 'reports'),
    group: '报告',
  },
]
export const toolGroups = ['全部', '排盘', '占卜', '星座与关系', '轻测算', '报告']
