<script setup lang="ts">
import { computed } from 'vue'
import { go, miniTabUrl, urlFor, type Destination } from '../shared/navigation'
defineOptions({ options: { virtualHost: true } })

const props = defineProps<{ to: Destination; mode?: 'navigate' | 'redirect' | 'reLaunch' }>()
const url = computed(() => urlFor(props.to))
const mode = computed(() => props.mode || (getCurrentPages().length >= 9 ? 'redirect' : 'navigate'))

// #ifdef H5
function follow(event: MouseEvent) {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  const action = mode.value
  void go(props.to, action === 'reLaunch' ? 'root' : action === 'redirect' ? 'replace' : 'push')
}
// #endif

// #ifndef H5
const tab = computed(() => miniTabUrl(props.to, props.mode === 'reLaunch'))
// #endif
</script>

<template>
  <!-- #ifdef H5 -->
  <a class="nav-link" :href="'#' + url" @click="follow"><slot /></a>
  <!-- #endif -->
  <!-- #ifndef H5 -->
  <navigator :url="tab || url" :open-type="tab ? 'switchTab' : mode" hover-class="pressed"><slot /></navigator>
  <!-- #endif -->
</template>
