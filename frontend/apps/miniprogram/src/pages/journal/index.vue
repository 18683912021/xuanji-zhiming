<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { journal, type JournalEntry } from '../../features/journal/storage'
const entries = ref<JournalEntry[]>([])
onShow(() => {
  entries.value = journal()
})
</script>

<template>
  <view class="sheet stack">
    <view
      ><text class="headline">私人日记</text><text class="copy">记录保存在当前设备。</text></view
    >
    <navigator class="cta" url="/pages/entry/index">新建日记</navigator>
    <navigator
      v-for="entry in entries"
      :key="entry.id"
      class="card"
      :url="'/pages/entry/index?id=' + entry.id"
    >
      <text class="heading">{{ entry.title }}</text
      ><text class="copy">{{ entry.updated }}</text>
    </navigator>
    <view v-if="!entries.length" class="card">
      <text class="heading">还没有记录</text><text class="copy">从今天的一项小观察开始。</text>
    </view>
  </view>
</template>
