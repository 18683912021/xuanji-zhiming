<script setup lang="ts">
import AiPage from '../ai/AiPage.vue'
import { usePageMotion } from '../../shared/pageMotion'

const entering = usePageMotion()
</script>

<template>
  <AiPage :entering="entering" />
</template>
