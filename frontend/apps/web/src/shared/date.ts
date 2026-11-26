const dateFormat = new Intl.DateTimeFormat('zh-CN', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function dateLabel(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '日期不详' : dateFormat.format(date)
}
