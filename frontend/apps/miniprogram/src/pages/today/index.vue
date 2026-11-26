<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { currentTerm, groups } from '../../features/calendar/terms'

const today = ref(currentTerm())
const guidance = computed(
  () =>
    groups.flatMap((group) => [...group.terms]).find(([name]) => name === today.value.title)?.[1] ||
    '记录下今天的天气、光线或身边的物候。',
)
onShow(() => {
  today.value = currentTerm()
})
</script>

<template>
  <view class="today">
    <view class="term-hero">
      <image class="sky" src="/static/sky.jpg" mode="aspectFill" aria-hidden="true" />
      <view class="hero-copy">
        <text class="gold">今日节气</text>
        <text class="headline">{{ today.title }}</text>
        <text class="copy">{{ today.date }} · {{ today.lunar }}</text>
        <navigator class="cta" url="/pages/entry/index">写下今日观察</navigator>
      </view>
    </view>
    <view class="sheet stack">
      <view class="card">
        <text class="heading">今日观察</text>
        <text class="copy">{{ guidance }}</text>
      </view>
      <navigator class="cta secondary" url="/pages/guide/index" open-type="switchTab"
        >查看节气图鉴</navigator
      >
    </view>
  </view>
</template>

<style scoped>
.term-hero {
  position: relative;
  overflow: hidden;
  min-height: 670rpx;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  text-align: center;
  padding: 35rpx 36rpx 45rpx;
  border-bottom: 1px solid var(--line);
}
.sky {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.74;
}
.hero-copy {
  z-index: 1;
  width: 100%;
  position: relative;
}
.hero-copy .headline {
  margin-top: 10rpx;
}
.hero-copy .cta {
  margin: 25rpx auto 0;
  max-width: 390rpx;
}
</style>
