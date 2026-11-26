import '@xuanji/theme/tokens.css'
import './styles/base.css'
import './styles/ui.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'

createApp(App).use(createPinia()).use(router).mount('#app')
