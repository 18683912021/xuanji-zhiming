import { createSSRApp } from 'vue'
import App from './App.vue'
import { destination, urlFor, type Destination } from './shared/navigation'

// #ifdef H5
const oldPages: Record<string, Destination> = {
  tarot: destination('divination', 'tarot'),
  bazi: destination('charts', 'bazi'),
  liuyao: destination('divination', 'liuyao'),
  dream: destination('divination', 'dream'),
  oracle: destination('divination', 'oracle'),
  today: destination('today', 'fortune'),
  records: destination('account', 'records'),
}

function upgradeLink() {
  const url = window.location.hash.match(/^#\/([a-z]+)(?:\/([a-z0-9-]+))?(?:\?.*)?$/i)
  if (!url) return
  const [, path, id] = url
  const next =
    path === 'result' && id
      ? destination('account', 'result', { id })
      : path === 'conversation' && id
        ? destination('ai', 'chat', { id })
        : oldPages[path!]
  if (next) window.history.replaceState(window.history.state, '', '#' + urlFor(next))
}
// #endif

export function createApp() {
  // #ifdef H5
  upgradeLink()
  // #endif
  const app = createSSRApp(App)
  return { app }
}
