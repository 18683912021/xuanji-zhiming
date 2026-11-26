<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BrandSeal from './BrandSeal.vue'

const route = useRoute()
const menu = ref<HTMLDetailsElement>()
const account = ref<HTMLDialogElement>()

const primaryLinks = [
  { label: '首页', to: '/' },
  { label: '八字', to: '/bazi' },
  { label: '解梦', to: '/dream' },
  { label: '塔罗', to: '/tarot' },
  { label: '六爻', to: '/liuyao' },
]
const mobileLinks = [
  ...primaryLinks,
  { label: '占卜', to: '/oracle' },
  { label: '今日', to: '/today' },
  { label: '体验记录', to: '/records' },
]

watch(
  () => route.path,
  () => {
    if (menu.value) menu.value.open = false
    account.value?.close()
  },
)
</script>

<template>
  <header class="site-header">
    <div class="site-header-inner">
      <RouterLink class="wordmark" to="/" aria-label="玄机知命首页">
        <BrandSeal /><span>玄机知命</span>
      </RouterLink>
      <nav class="site-nav" aria-label="主导航">
        <RouterLink v-for="link in primaryLinks" :key="link.to" :to="link.to">
          {{ link.label }}
        </RouterLink>
      </nav>
      <div class="header-actions">
        <button
          type="button"
          class="button button-outline login-button"
          @click="account?.showModal()"
        >
          登录
        </button>
        <details ref="menu" class="mobile-menu">
          <summary aria-label="功能菜单"><span></span><span></span><span></span></summary>
          <nav aria-label="移动端导航">
            <RouterLink v-for="link in mobileLinks" :key="link.to" :to="link.to">
              {{ link.label }}
            </RouterLink>
          </nav>
        </details>
      </div>
    </div>
  </header>
  <dialog
    ref="account"
    class="account-dialog"
    aria-labelledby="account-title"
    @click.self="account?.close()"
  >
    <section>
      <h2 id="account-title">登录玄机知命</h2>
      <p>账号服务接入后即可登录。现在可直接体验，保存的记录存放在此浏览器。</p>
      <div class="action-row">
        <RouterLink class="button button-gold" to="/records" @click="account?.close()"
          >查看本机记录</RouterLink
        >
        <form method="dialog"><button class="button button-outline">继续体验</button></form>
      </div>
    </section>
  </dialog>
</template>
