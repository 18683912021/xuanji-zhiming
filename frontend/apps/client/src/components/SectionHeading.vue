<script setup lang="ts">
import NavLink from './NavLink.vue'
import type { Destination } from '../shared/navigation'

defineProps<{ title: string; to?: Destination; action?: string }>()
defineOptions({ options: { virtualHost: true } })
</script>

<template>
  <view class="section-heading">
    <text class="section-title">{{ title }}</text>
    <NavLink v-if="to" class="link" :to="to"
      >{{ action || '查看全部' }} <text aria-hidden="true">›</text></NavLink
    >
    <slot />
  </view>
</template>
