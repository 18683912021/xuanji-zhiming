<script setup lang="ts">
import ExplorePage from '../explore/ExplorePage.vue'
import { usePageMotion } from '../../shared/pageMotion'

const entering = usePageMotion()
</script>

<template>
  <ExplorePage :entering="entering" />
</template>
