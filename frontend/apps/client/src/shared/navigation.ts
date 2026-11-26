export type Section =
  | 'home'
  | 'explore'
  | 'today'
  | 'ai'
  | 'account'
  | 'charts'
  | 'divination'
  | 'social'
  | 'commerce'
export type Query = Record<string, string | undefined>

export interface Destination {
  section: Section
  view?: string
  query?: Query
}

export function destination(section: Section, view?: string, query?: Query): Destination {
  return { section, view, query }
}

export function urlFor(target: Destination) {
  const entries = Object.entries({ ...target.query, view: target.view })
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value!))
  return '/pages/' + target.section + '/index' + (entries.length ? '?' + entries.join('&') : '')
}

export function go(target: Destination, mode: 'push' | 'replace' | 'root' = 'push') {
  const url = urlFor(target)
  if (mode === 'root') return uni.reLaunch({ url })
  if (mode === 'replace' || getCurrentPages().length >= 9) return uni.redirectTo({ url })
  return uni.navigateTo({ url })
}

export function back(fallback: Destination) {
  if (getCurrentPages().length > 1) return uni.navigateBack()
  return go(fallback, 'root')
}

export function toast(title: string) {
  uni.showToast({ title, icon: 'none' })
}

export function confirmAction(title: string, content: string, accept: () => void) {
  uni.showModal({
    title,
    content,
    confirmColor: '#60427e',
    success: (result) => {
      if (result.confirm) accept()
    },
  })
}
