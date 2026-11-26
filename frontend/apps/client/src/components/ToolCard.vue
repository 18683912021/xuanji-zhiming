<script setup lang="ts">
import AppIcon from './AppIcon.vue'
import NavLink from './NavLink.vue'
import type { Destination } from '../shared/navigation'

defineOptions({ options: { virtualHost: true } })
defineProps<{ title: string; description: string; glyph: string; to: Destination; feature?: boolean }>()
</script>

<template>
  <NavLink class="tool-card" :class="{ 'feature-card': feature, 'dream-card': to.view === 'dream' }" :to="to">
    <AppIcon :glyph="glyph" class="tool-art" />
    <view class="tool-copy">
      <text class="tool-title">{{ title }}</text>
      <text class="muted">{{ description }}</text>
    </view>
  </NavLink>
</template>
