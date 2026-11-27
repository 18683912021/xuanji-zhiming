<script setup lang="ts">
import { ref } from 'vue'
import { onHide, onLoad } from '@dcloudio/uni-app'
import AiPage from './AiPage.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>()
const page = ref<{ stopRun: () => void }>()
onLoad((value) => { query.value = value || {} })
onHide(() => page.value?.stopRun())
</script>

<template>
  <AiPage v-if="query" ref="page" :query="query" />
</template>
