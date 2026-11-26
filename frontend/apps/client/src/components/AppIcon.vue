<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ options: { virtualHost: true } })
const props = defineProps<{ name?: string; glyph?: string }>()
const glyphs: Record<string, string> = {
  '☯': 'bazi',
  '✧': 'tarot',
  '䷀': 'liuyao',
  籤: 'oracle',
  '♈': 'zodiac',
  '♈︎': 'zodiac',
  '☾': 'today',
  '☽': 'dream',
  '⊙': 'chart',
  '✦': 'ai',
  '⋇': 'mansion',
  '◇': 'explore',
  '◎': 'match',
  '❋': 'match',
  '♡': 'heart',
  '♧': 'heart',
  '⚄': 'dice',
  '▤': 'book',
  '☼': 'today',
  '✹': 'home',
  掌: 'hand',
  相: 'face',
  '▦': 'test',
  '▧': 'note',
  '▱': 'note',
  '⚙': 'settings',
  '☆': 'home',
}
const path = computed(() => '/static/icons/' + (props.name || glyphs[props.glyph || ''] || 'home') + '.png')
</script>

<template>
  <image class="app-icon" :src="path" mode="aspectFit" aria-hidden="true" />
</template>
