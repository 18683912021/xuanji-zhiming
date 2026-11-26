import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '@/features/home/HomeView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/tarot',
      name: 'tarot',
      component: () => import('@/features/tarot/TarotView.vue'),
      meta: { title: '塔罗占卜' },
    },
    {
      path: '/bazi',
      name: 'bazi',
      component: () => import('@/features/bazi/BaziView.vue'),
      meta: { title: '八字命盘' },
    },
    {
      path: '/liuyao',
      name: 'liuyao',
      component: () => import('@/features/liuyao/LiuyaoView.vue'),
      meta: { title: '六爻问事' },
    },
    {
      path: '/dream',
      name: 'dream',
      component: () => import('@/features/dream/DreamView.vue'),
      meta: { title: 'AI 解梦' },
    },
    {
      path: '/oracle',
      name: 'oracle',
      component: () => import('@/features/oracle/OracleView.vue'),
      meta: { title: '占卜问签' },
    },
    {
      path: '/today',
      name: 'today',
      component: () => import('@/features/today/TodayView.vue'),
      meta: { title: '星座运势' },
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('@/features/experiences/RecordsView.vue'),
      meta: { title: '体验记录' },
    },
    {
      path: '/result/:id',
      name: 'result',
      component: () => import('@/features/experiences/ResultView.vue'),
      meta: { title: '体验结果' },
    },
    {
      path: '/conversation/:id',
      name: 'conversation',
      component: () => import('@/features/experiences/ConversationView.vue'),
      meta: { title: '解读对话' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'missing',
      component: () => import('@/shared/pages/MissingView.vue'),
      meta: { title: '页面未找到' },
    },
  ],
})

router.afterEach((route) => {
  document.title = route.meta.title ? `${route.meta.title} · 玄机知命` : '玄机知命'
})
