<script setup lang="ts">
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <div class="page-intro">
    <RouterLink class="breadcrumb" to="/">返回首页</RouterLink>
    <h1>{{ title }}</h1>
    <p v-if="description" class="muted">{{ description }}</p>
  </div>
</template>
