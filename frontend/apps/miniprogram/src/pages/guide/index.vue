<script setup lang="ts">
import { computed, ref } from 'vue'
import { groups } from '../../features/calendar/terms'
const active = ref(0)
const group = computed(() => groups[active.value]!)
</script>

<template>
  <view class="sheet stack">
    <text class="headline">节气图鉴</text>
    <view class="season-tabs">
      <button
        v-for="(item, index) in groups"
        :key="item.season"
        class="cta"
        :class="{ secondary: index !== active }"
        @tap="active = index"
      >
        {{ item.season }}
      </button>
    </view>
    <view v-for="[name, description] in group.terms" :key="name" class="card">
      <text class="heading gold">{{ name }}</text>
      <text class="copy">{{ description }}</text>
    </view>
  </view>
</template>
<style scoped>
.season-tabs {
  display: flex;
  gap: 10rpx;
}
.season-tabs .cta {
  flex: 1;
}
</style>
