import { Solar } from 'lunar-typescript'

export const groups = [
  {
    season: '春',
    terms: [
      ['立春', '留意枝条上是否已经出现嫩芽。'],
      ['雨水', '记录雨雪形式和土壤的湿度变化。'],
      ['惊蛰', '观察土壤与植物附近的早春活动。'],
      ['春分', '比较清晨和黄昏的光线。'],
      ['清明', '观察身边树木和当季植物。'],
      ['谷雨', '记下雨后空气与叶子的变化。'],
    ],
  },
  {
    season: '夏',
    terms: [
      ['立夏', '留意白昼延长以后生活节奏的变化。'],
      ['小满', '观察谷物、叶片或果实的生长。'],
      ['芒种', '记录夏季作物和降雨。'],
      ['夏至', '观察正午与傍晚的影子。'],
      ['小暑', '留意气温和可避暑的空间。'],
      ['大暑', '记录一天里温度最高的时段。'],
    ],
  },
  {
    season: '秋',
    terms: [
      ['立秋', '试着比较清晨和傍晚的风。'],
      ['处暑', '观察暑热消退的迹象。'],
      ['白露', '看看晨间的水汽停在哪里。'],
      ['秋分', '留意日光与夜晚时间的变化。'],
      ['寒露', '记录日出前后的露水和气温。'],
      ['霜降', '观察本地昼夜温差和叶色。'],
    ],
  },
  {
    season: '冬',
    terms: [
      ['立冬', '记下近日的光线和风向变化。'],
      ['小雪', '看看晨间叶面、风和雨。'],
      ['大雪', '观察冷空气到来前后的云量。'],
      ['冬至', '记录今天的日出和入夜时间。'],
      ['小寒', '比较不同时间段的体感温度。'],
      ['大寒', '回顾这一季留下的自然观察。'],
    ],
  },
] as const

export function currentTerm() {
  const solar = Solar.fromDate(new Date())
  const lunar = solar.getLunar()
  return {
    title: lunar.getJieQi() || lunar.getPrevJieQi(true).getName(),
    date: `${solar.getYear()} 年 ${solar.getMonth()} 月 ${solar.getDay()} 日`,
    lunar: `农历 ${lunar.getMonthInChinese()}月${lunar.getDayInChinese()}`,
  }
}
