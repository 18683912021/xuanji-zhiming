<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AuthPanel from '../../features/account/AuthPanel.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>({})
onLoad((value) => { query.value = value || {} })
</script>

<template>
  <AuthPanel mode="login" :query="query" />
</template>
