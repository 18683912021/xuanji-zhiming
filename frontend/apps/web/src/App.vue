<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import SiteHeader from '@/layout/SiteHeader.vue'

const route = useRoute()
const main = ref<HTMLElement>()

watch(
  () => route.path,
  async () => {
    await nextTick()
    main.value?.focus({ preventScroll: true })
  },
)
</script>

<template>
  <a class="skip-link" href="#main-content" @click.prevent="main?.focus()">跳到内容</a>
  <SiteHeader />
  <main ref="main" id="main-content" tabindex="-1">
    <RouterView v-slot="{ Component }">
      <component :is="Component" :key="route.path" />
    </RouterView>
  </main>
  <footer class="footer">
    <span>玄机知命</span>
    <nav aria-label="更多工具">
      <RouterLink to="/oracle">占卜问签</RouterLink>
      <RouterLink to="/today">星座运势</RouterLink>
      <RouterLink to="/records">体验记录</RouterLink>
    </nav>
  </footer>
</template>

<style src="./layout/shell.css"></style>
