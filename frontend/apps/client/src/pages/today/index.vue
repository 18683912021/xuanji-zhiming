<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TodayPage from './TodayPage.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>()
onLoad((value) => { query.value = value || {} })
</script>

<template>
  <TodayPage v-if="query" :query="query" />
</template>
