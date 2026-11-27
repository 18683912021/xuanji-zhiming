import { defineConfig, type Plugin } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const proxy = { '/api': 'http://127.0.0.1:8000' }

const preloadRouteComponents: Plugin = {
  name: 'xuanji:preload-route-components',
  enforce: 'post',
  transform(code, id) {
    if (!id.split('?', 1)[0]!.endsWith('/pages-json-js')) return
    // uni.preloadPage calls this record's loader. Resolve Vue's async wrapper as well as the module,
    // so redirectTo and reLaunch can mount it immediately after removing the old page.
    const resolved = code.replace(/^(\s*loader:\s*)(\w+)Loader,/gm, '$1$2.__asyncLoader,')
    if (resolved !== code) return { code: resolved, map: null }
  },
}

export default defineConfig({ plugins: [uni(), preloadRouteComponents], server: { proxy }, preview: { proxy } })
