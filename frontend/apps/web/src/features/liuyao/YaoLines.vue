<script setup lang="ts">
import { computed } from 'vue'
import { isMoving, isYin, yaoLabels, yaoNames } from '@/features/liuyao/liuyao'
import type { Yao } from '@/features/liuyao/liuyao'
const props = defineProps<{ lines: readonly (Yao | undefined)[]; showMoving?: boolean }>()
const rows = computed(() =>
  [...yaoNames].map((name, i) => ({ name, value: props.lines[i] })).reverse(),
)
</script>

<template>
  <div class="yao-rows">
    <div v-for="{ name, value } in rows" :key="name" class="yao-row">
      <span>{{ name }}</span>
      <span
        class="yao-line"
        :class="{
          yin: value && isYin(value),
          moving: value && showMoving && isMoving(value),
          pending: !value,
        }"
        aria-hidden="true"
      ></span>
      <span class="muted">{{ value ? yaoLabels[value] : '未起' }}</span>
    </div>
  </div>
</template>

<style scoped>
.yao-rows {
  display: grid;
  gap: 10px;
}
.yao-row {
  display: grid;
  gap: 11px;
  grid-template-columns: minmax(45px, 0.6fr) minmax(50px, 1.3fr) minmax(58px, 1fr);
  align-items: center;
}
.yao-line {
  display: block;
  height: 6px;
  border-radius: 2px;
  background: var(--gold);
}
.yao-line.yin {
  background: linear-gradient(90deg, var(--gold) 42%, transparent 42% 58%, var(--gold) 58%);
}
.yao-line.moving {
  outline: 1px solid var(--mist);
  outline-offset: 3px;
}
.yao-line.pending {
  opacity: 0.2;
}
</style>
