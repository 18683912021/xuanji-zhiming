<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import DivinationTools from '../../features/divination/DivinationTools.vue'
import Activities from '../../features/divination/Activities.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>({})
onLoad((params) => {
  query.value = params || {}
})
const titles: Record<string, string> = {
  tarot: '塔罗占卜',
  daily: '每日塔罗',
  deck: '塔罗牌义图鉴',
  card: '塔罗牌义',
  liuyao: '六爻问事',
  oracle: '占卜问签',
  dice: '星座骰子',
  book: '答案之书',
  dream: 'AI 解梦',
  wishes: '许愿与接好运',
  mbti: 'MBTI 测试',
  palm: '手相文化解读',
  face: '面相文化解读',
}
const view = computed(() => (query.value.view && Object.prototype.hasOwnProperty.call(titles, query.value.view) ? query.value.view : 'tarot'))
</script>
<template>
  <AppShell section="divination" :title="titles[view]" detail>
    <Activities v-if="['wishes', 'mbti', 'palm', 'face'].includes(view)" :view="view" />
    <DivinationTools v-else :view="view" :spread="query.spread" :id="query.id" />
  </AppShell>
</template>
