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
export type Page = Section | 'login' | 'register' | 'security'
export type Query = Record<string, string | undefined>

export interface Destination {
  section: Page
  view?: string
  query?: Query
}

export function destination(section: Page, view?: string, query?: Query): Destination {
  return { section, view, query }
}

export function urlFor(target: Destination) {
  const entries = Object.entries({ ...target.query, view: target.view })
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value!))
  return '/pages/' + target.section + '/index' + (entries.length ? '?' + entries.join('&') : '')
}

type NavigationMode = 'push' | 'replace' | 'root'

// #ifdef MP-WEIXIN
const miniTabPaths: Partial<Record<Page, string>> = {
  home: '/pages/home/index',
  explore: '/pages/tabs/explore',
  today: '/pages/tabs/today',
  ai: '/pages/tabs/ai',
  account: '/pages/tabs/account',
}
// #endif

export function miniTabUrl(target: Destination, root: boolean): string | undefined {
  // #ifdef MP-WEIXIN
  if (target.section === 'home') return miniTabPaths.home
  if (root && target.view === undefined && Object.values(target.query || {}).every((value) => value === undefined)) {
    return miniTabPaths[target.section]
  }
  // #endif
}

function openPage(url: string, mode: NavigationMode) {
  if (mode === 'root') return uni.reLaunch({ url })
  if (mode === 'replace' || getCurrentPages().length >= 9) return uni.redirectTo({ url })
  return uni.navigateTo({ url })
}

// #ifdef H5
const loadedPages = new Map<string, Promise<void>>()
const decodedBackgrounds = new Map<string, Promise<void>>()
let navigationSequence = 0

function preloadPage(path: string) {
  let loading = loadedPages.get(path)
  if (!loading) {
    loading = new Promise<void>((resolve, reject) => {
      uni.preloadPage({ url: path, success: () => resolve(), fail: reject })
    }).catch(() => { loadedPages.delete(path) })
    loadedPages.set(path, loading)
  }
  return loading
}

function preloadBackground(section: Page) {
  let url: string
  if (section === 'home') {
    url = matchMedia('(max-width: 767px)').matches ? '/static/hero-mobile-v02.webp' : '/static/hero-desktop.webp'
  } else if (section === 'login' || section === 'register' || section === 'security') {
    url = matchMedia('(max-width: 900px)').matches ? '/static/auth/mobile.webp' : '/static/auth/desktop.webp'
  } else {
    return
  }
  let loading = decodedBackgrounds.get(url)
  if (!loading) {
    const image = new Image()
    const decoded = new Promise<void>((resolve, reject) => {
      image.onload = () => resolve()
      image.onerror = () => reject()
      image.src = url
    }).then(() => image.decode?.())
    loading = decoded.catch(() => { decodedBackgrounds.delete(url) })
    decodedBackgrounds.set(url, loading)
  }
  return loading
}

function isCurrentPage(url: string) {
  const current = new URL(location.hash.slice(1) || '/', location.origin)
  const next = new URL(url, location.origin)
  const currentPath = current.pathname === '/' ? '/pages/home/index' : current.pathname
  if (next.pathname !== currentPath) return false
  current.searchParams.sort()
  next.searchParams.sort()
  return current.searchParams.toString() === next.searchParams.toString()
}

async function goWeb(target: Destination, url: string, mode: NavigationMode) {
  const sequence = ++navigationSequence
  if (isCurrentPage(url)) return

  const from = location.hash
  // Uni registers the entry page as / and accepts /pages/home/index as a navigation alias.
  const preloadPath = target.section === 'home' ? '/' : url.split('?', 1)[0]!
  await Promise.all([preloadPage(preloadPath), preloadBackground(target.section)])
  // Keep the current page mounted during cold loads. A newer navigation owns the next screen.
  if (sequence === navigationSequence && location.hash === from) return openPage(url, mode)
}
// #endif

export function go(target: Destination, mode: NavigationMode = 'push') {
  // #ifdef MP-WEIXIN
  const tab = miniTabUrl(target, mode === 'root')
  if (tab) return uni.switchTab({ url: tab })
  // #endif
  const url = urlFor(target)
  // #ifdef H5
  return goWeb(target, url, mode)
  // #endif
  // #ifndef H5
  return openPage(url, mode)
  // #endif
}

export function back(fallback: Destination) {
  // #ifdef H5
  navigationSequence++
  // #endif
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
