import { Solar } from 'lunar-typescript'
import { dateKey, offsetDate, parseDate } from '../../shared/storage'

export function calendarDay(date: string) {
  const solar = Solar.fromDate(parseDate(date))
  const lunar = solar.getLunar()
  const phase = ['新月', '娥眉月', '上弦月', '盈凸月', '满月', '亏凸月', '下弦月', '残月'][
    Math.floor(((lunar.getDay() - 1) * 8) / 30)
  ]!
  return {
    lunar: lunar.getMonthInChinese() + '月' + lunar.getDayInChinese(),
    term: lunar.getJieQi(),
    season: lunar.getJieQi() || lunar.getPrevJieQi(true).getName(),
    moon: phase,
    yi: lunar.getDayYi().slice(0, 8),
    ji: lunar.getDayJi().slice(0, 8),
    zodiac: lunar.getDayShengXiao(),
    holiday: solar.getFestivals().join('、'),
    weekday: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][parseDate(date).getDay()]!,
  }
}

export function monthDays(value: string) {
  const date = parseDate(value)
  const year = date.getFullYear()
  const month = date.getMonth()
  const first = new Date(year, month, 1, 12)
  const delta = (first.getDay() + 6) % 7
  const size = new Date(year, month + 1, 0).getDate()
  const firstKey = dateKey(first)
  return Array.from({ length: Math.ceil((size + delta) / 7) * 7 }, (_, index) => {
    const day = offsetDate(firstKey, index - delta)
    const lunar = calendarDay(day)
    return {
      day,
      number: Number(day.slice(-2)),
      current: day.slice(0, 7) === value.slice(0, 7),
      term: lunar.term,
      description: lunar.term || lunar.holiday || lunar.lunar.slice(-2),
    }
  })
}

export function monthOffset(date: string, amount: number) {
  const current = parseDate(date)
  return dateKey(new Date(current.getFullYear(), current.getMonth() + amount, 1, 12))
}
