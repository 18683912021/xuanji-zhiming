<script setup lang="ts">
import { computed } from 'vue'
import { urlFor, type Destination } from '../shared/navigation'
defineOptions({ options: { virtualHost: true } })

const props = defineProps<{ to: Destination; mode?: 'navigate' | 'redirect' | 'reLaunch' }>()
const url = computed(() => urlFor(props.to))
const mode = computed(() => props.mode || (getCurrentPages().length >= 9 ? 'redirect' : 'navigate'))
</script>

<template>
  <navigator :url="url" :open-type="mode" hover-class="pressed"><slot /></navigator>
</template>
