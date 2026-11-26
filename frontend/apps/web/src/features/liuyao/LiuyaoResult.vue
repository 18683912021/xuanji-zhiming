<script setup lang="ts">
import { computed } from 'vue'
import YaoLines from './YaoLines.vue'
import { changed, hexagram, isMoving, type Yao } from './liuyao'

const props = defineProps<{ lines: Yao[] }>()
const hasMoving = computed(() => props.lines.some(isMoving))
const originalName = computed(() => hexagram(props.lines))
const changedLines = computed(() => changed(props.lines))
const changedName = computed(() => hexagram(changedLines.value))
</script>

<template>
  <div class="split">
    <section class="panel">
      <h2>本卦 · {{ originalName }}</h2>
      <YaoLines :lines="lines" show-moving />
    </section>
    <section class="panel" v-if="hasMoving">
      <h2>变卦 · {{ changedName }}</h2>
      <YaoLines :lines="changedLines" />
    </section>
  </div>
  <p class="notice">
    {{
      hasMoving
        ? '老阴变阳、老阳变阴。描边标出了本卦的动爻。'
        : '本次六爻均为少阴或少阳，没有动爻。'
    }}
  </p>
</template>
