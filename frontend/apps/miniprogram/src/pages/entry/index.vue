<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { deleteEntry, journal, storeEntry } from '../../features/journal/storage'

const id = ref('')
const title = ref('')
const content = ref('')
const busy = ref(false)
onLoad((query) => {
  if (!query?.id) return
  const entry = journal().find((item) => item.id === query.id)
  if (!entry) {
    uni.showToast({ title: '这条日记已不可用', icon: 'none' })
    uni.navigateBack()
    return
  }
  id.value = entry.id
  title.value = entry.title
  content.value = entry.content
})
function save() {
  const body = content.value.trim()
  if (busy.value || !body) return
  busy.value = true
  try {
    storeEntry({ id: id.value, title: title.value.trim() || body.slice(0, 18), content: body })
    uni.navigateBack({
      fail: () => {
        uni.switchTab({ url: '/pages/journal/index' })
      },
    })
  } catch {
    busy.value = false
    uni.showToast({ title: '保存失败，请稍后重试', icon: 'none' })
  }
}
function remove() {
  uni.showModal({
    title: '删除日记',
    content: '确认删除这条本机日记？',
    confirmColor: '#60427E',
    success(result) {
      if (!result.confirm) return
      try {
        deleteEntry(id.value)
        uni.navigateBack({
          fail: () => {
            uni.switchTab({ url: '/pages/journal/index' })
          },
        })
      } catch {
        uni.showToast({ title: '删除失败，请稍后重试', icon: 'none' })
      }
    },
  })
}
</script>
<template>
  <view class="sheet stack">
    <text class="headline">{{ id ? '编辑日记' : '写下观察' }}</text>
    <view class="card stack">
      <view
        ><text class="form-label">标题</text
        ><input
          v-model="title"
          class="field"
          maxlength="40"
          placeholder="给今天的记录起个名字"
          placeholder-class="placeholder"
      /></view>
      <view
        ><text class="form-label">日记</text
        ><textarea
          v-model="content"
          class="field area"
          maxlength="1000"
          placeholder="今天，你观察到了什么？"
          placeholder-class="placeholder"
        />
      </view>
      <button class="cta" :disabled="busy || !content.trim()" @tap="save">保存到本机</button>
      <button v-if="id" class="cta secondary" @tap="remove">删除日记</button>
    </view>
  </view>
</template>
