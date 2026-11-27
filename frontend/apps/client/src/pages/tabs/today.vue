<script setup lang="ts">
import TodayPage from '../today/TodayPage.vue'
import { usePageMotion } from '../../shared/pageMotion'

const entering = usePageMotion()
</script>

<template>
  <TodayPage :entering="entering" />
</template>
