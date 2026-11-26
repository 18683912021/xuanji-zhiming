<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import AccountPanel from '../../features/account/AccountPanel.vue'
import RecordsPanel from '../../features/account/RecordsPanel.vue'
import type { Query } from '../../shared/navigation'

const query = ref<Query>({})
onLoad((value) => {
  query.value = value || {}
})
const accountPages: Record<string, string> = {
  index: '我的',
  login: '体验登录',
  'public-edit': '编辑个人资料',
  profiles: '出生档案',
  profile: '出生档案详情',
  'profile-edit': '编辑出生档案',
  settings: '设置与隐私',
  support: '客服与反馈',
}
const recordsPages: Record<string, string> = {
  records: '体验记录',
  result: '体验详情',
  favorites: '我的收藏',
  journal: '私人日记',
  'journal-entry': '日记详情',
  'journal-edit': '写日记',
  events: '特别日期与生日',
  'event-edit': '编辑特别日期',
  'share-preview': '分享预览',
  shares: '分享管理',
  share: '体验分享',
}
const view = computed(() =>
  query.value.view && (query.value.view in accountPages || query.value.view in recordsPages)
    ? query.value.view
    : 'index',
)
</script>
<template>
  <AppShell section="account" :title="accountPages[view] || recordsPages[view]" :detail="view !== 'index'">
    <AccountPanel v-if="view in accountPages" :key="view + (query.id || '')" :view="view" :query="query" />
    <RecordsPanel v-else :key="view + (query.id || '')" :view="view" :query="query" />
  </AppShell>
</template>
