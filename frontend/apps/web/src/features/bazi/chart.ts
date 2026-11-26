import { Lunar, Solar } from 'lunar-typescript'

export type Calendar = 'solar' | 'lunar'

interface BirthInput {
  calendar: Calendar
  date: string
  time: string
  leapMonth: boolean
  timeUnknown: boolean
  lateZi: boolean
}

type Pillar = {
  label: string
  text: string
  elements: string
  hidden: string
}

export type BaziReading = {
  pillars: Pillar[]
  solarDate: string
  calendar: string
  lateZi: boolean
}

type ChartResult = { ok: true; reading: BaziReading } | { ok: false; error: string }

function pillar(label: string, text: string, elements: string, hidden: string[]): Pillar {
  return { label, text, elements, hidden: hidden.join('、') }
}

export function calculateBazi(input: BirthInput): ChartResult {
  const date = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(input.date.trim())
  const time = input.timeUnknown ? [12, 0] : /^(\d{2}):(\d{2})$/.exec(input.time)?.slice(1)

  if (!date || !time) {
    return { ok: false, error: '请填入出生日期和时间。时辰不详时可勾选对应选项。' }
  }

  const year = Number(date[1])
  const month = Number(date[2])
  const day = Number(date[3])
  const hour = Number(time[0])
  const minute = Number(time[1])
  if (
    year < 1900 ||
    year > 2099 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > 31 ||
    hour > 23 ||
    minute > 59
  ) {
    return { ok: false, error: '请核对日期范围（1900–2099 年）和时间。' }
  }

  if (input.calendar === 'solar') {
    const check = new Date(Date.UTC(year, month - 1, day))
    if (check.getUTCMonth() + 1 !== month || check.getUTCDate() !== day) {
      return { ok: false, error: '这个公历月份没有该日期，请重新选择。' }
    }
  }

  try {
    const lunar =
      input.calendar === 'lunar'
        ? Lunar.fromYmdHms(year, input.leapMonth ? -month : month, day, hour, minute, 0)
        : Solar.fromYmdHms(year, month, day, hour, minute, 0).getLunar()
    const chart = lunar.getEightChar()
    chart.setSect(input.lateZi ? 1 : 2)
    const timePillar = input.timeUnknown
      ? { label: '时柱', text: '时辰不详', elements: '—', hidden: '—' }
      : pillar('时柱', chart.getTime(), chart.getTimeWuXing(), chart.getTimeHideGan())

    return {
      ok: true,
      reading: {
        pillars: [
          pillar('年柱', chart.getYear(), chart.getYearWuXing(), chart.getYearHideGan()),
          pillar('月柱', chart.getMonth(), chart.getMonthWuXing(), chart.getMonthHideGan()),
          pillar('日柱', chart.getDay(), chart.getDayWuXing(), chart.getDayHideGan()),
          timePillar,
        ],
        solarDate: lunar.getSolar().toYmd(),
        calendar: input.calendar === 'lunar' ? '农历输入' : '公历输入',
        lateZi: input.lateZi,
      },
    }
  } catch {
    return {
      ok: false,
      error:
        input.calendar === 'lunar'
          ? '无法排盘，请核对农历日期及该年是否有对应闰月。'
          : '无法排盘，请核对公历日期和出生时间。',
    }
  }
}
