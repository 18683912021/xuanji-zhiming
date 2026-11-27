<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import SecurityPanel from '../../features/account/SecurityPanel.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>({})
const view = computed(() => query.value.view === 'email' || query.value.view === 'reset' ? query.value.view : 'credentials')
onLoad((value) => { query.value = value || {} })
</script>

<template>
  <SecurityPanel :view="view" :query="query" />
</template>
