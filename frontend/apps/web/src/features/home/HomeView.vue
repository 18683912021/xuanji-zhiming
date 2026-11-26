<script setup lang="ts">
import { ref } from 'vue'
import MotifIcon from './MotifIcon.vue'

const directory = ref<HTMLElement>()
const features = [
  { icon: 'bazi', title: '八字命盘', description: '查看四柱与五行', to: '/bazi' },
  { icon: 'dream', title: 'AI 解梦', description: '记录梦境，探索象征', to: '/dream' },
  { icon: 'tarot', title: '塔罗占卜', description: '抽一张牌，打开思路', to: '/tarot' },
  { icon: 'liuyao', title: '六爻问事', description: '起卦并查看卦象', to: '/liuyao' },
] as const

function openRealm() {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  directory.value?.focus({ preventScroll: true })
  directory.value?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' })
}
</script>

<template>
  <div class="portal">
    <div class="portal-sky" aria-hidden="true"></div>
    <section class="hero" aria-labelledby="hero-heading">
      <h1 id="hero-heading"><span>窥天地玄机，</span><span>知人生万象</span></h1>
      <p>以东方智慧为引，借 AI 探索命理、梦境与人生可能</p>
      <button type="button" class="button button-gold realm-button" @click="openRealm">
        开启玄境 <span aria-hidden="true">→</span>
      </button>
    </section>
    <section ref="directory" tabindex="-1" class="feature-grid" aria-label="核心体验">
      <RouterLink
        v-for="item in features"
        :key="item.to"
        :to="item.to"
        class="feature-card"
        :class="'feature--' + item.icon"
      >
        <MotifIcon :name="item.icon" />
        <span class="feature-copy">
          <strong>{{ item.title }}</strong>
          <span>{{ item.description }}</span>
        </span>
      </RouterLink>
    </section>
  </div>
</template>

<style scoped src="./home.css"></style>
