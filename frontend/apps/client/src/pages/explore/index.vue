<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import ExplorePage from './ExplorePage.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>()
onLoad((value) => { query.value = value || {} })
</script>

<template>
  <ExplorePage v-if="query" :query="query" />
</template>
