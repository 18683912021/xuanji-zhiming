<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import NavLink from './NavLink.vue'
import { account } from '../features/account/state'
import { back, destination, type Section } from '../shared/navigation'

const props = defineProps<{ section: Section; title?: string; subtitle?: string; detail?: boolean }>()
const menuOpen = ref(false)
const tabs = [
  { section: 'home', title: '首页', icon: 'home' },
  { section: 'explore', title: '探索', icon: 'explore' },
  { section: 'today', title: '今日', icon: 'today' },
  { section: 'ai', title: 'AI 对话', icon: 'ai' },
  { section: 'account', title: '我的', icon: 'user' },
] as const
let statusPadding = '0px'
let capsulePadding = '0px'
// #ifdef MP-WEIXIN
const capsule = uni.getMenuButtonBoundingClientRect()
if (capsule.top > 0) {
  statusPadding = Math.max(0, capsule.top - (52 - capsule.height) / 2) + 'px'
  capsulePadding = capsule.width + 12 + 'px'
  if (uni.getWindowInfo().windowWidth < 360) {
    statusPadding = capsule.bottom + 4 + 'px'
    capsulePadding = '0px'
  }
}
// #endif
const fallback: Partial<Record<Section, Section>> = {
  charts: 'explore',
  divination: 'explore',
  social: 'account',
  commerce: 'account',
}
const active = computed(() => fallback[props.section] || props.section)
const sectionArtwork: Record<Section, string> = {
  home: 'home',
  explore: 'explore',
  today: 'today',
  ai: 'ai',
  account: 'user',
  charts: 'chart',
  divination: 'tarot',
  social: 'match',
  commerce: 'seal',
}
</script>

<template>
  <view class="app-shell">
    <view class="site-header" :style="{ paddingTop: statusPadding }">
      <view class="header-inner" :style="{ paddingRight: capsulePadding }">
        <NavLink class="brand" :to="destination('home')" mode="reLaunch">
          <AppIcon name="seal" class="brand-seal" /><text>玄机知命</text>
        </NavLink>
        <view class="desktop-tabs" aria-label="主导航">
          <NavLink
            v-for="item in tabs"
            :key="item.section"
            class="desktop-tab"
            :class="{ active: item.section === active }"
            :to="destination(item.section)"
            mode="reLaunch"
          >
            {{ item.title }}
          </NavLink>
        </view>
        <view class="header-actions">
          <NavLink
            class="header-login btn"
            :to="destination('account', account.state.value ? undefined : 'login')"
          >
            {{ account.state.value ? '我的' : '登录' }}
          </NavLink>
          <button
            class="header-menu"
            :aria-label="menuOpen ? '收起菜单' : '展开菜单'"
            :aria-expanded="menuOpen"
            @tap="menuOpen = !menuOpen"
          >
            <AppIcon name="menu" />
          </button>
        </view>
      </view>
      <view v-if="menuOpen" class="header-drawer">
        <NavLink
          v-for="item in tabs"
          :key="item.section"
          class="drawer-link"
          :to="destination(item.section)"
          mode="reLaunch"
        >
          <AppIcon :name="item.icon" /> <text>{{ item.title }}</text>
        </NavLink>
        <NavLink class="drawer-link" :to="destination('social', 'messages')"
          ><AppIcon name="message" /><text>消息</text></NavLink
        >
      </view>
    </view>
    <view v-if="title" class="page-heading content-width">
      <view class="heading-text">
        <button v-if="detail" class="back-link" @tap="back(destination(fallback[section] || section))">
          ‹ 返回
        </button>
        <text class="page-title">{{ title }}</text>
        <text v-if="subtitle" class="muted heading-copy">{{ subtitle }}</text>
      </view>
      <AppIcon :name="sectionArtwork[section]" class="page-ornament" />
    </view>
    <slot />
    <view class="site-footer content-width">
      <text>玄机知命</text>
      <NavLink class="link" :to="destination('account', 'settings')">设置与隐私</NavLink>
    </view>
    <view class="mobile-tabs" aria-label="主导航">
      <NavLink
        v-for="item in tabs"
        :key="item.section"
        class="mobile-tab"
        :class="{ active: item.section === section || item.section === fallback[section] }"
        :to="destination(item.section)"
        mode="reLaunch"
      >
        <AppIcon :name="item.icon" class="tab-icon" /><text>{{ item.title }}</text>
      </NavLink>
    </view>
  </view>
</template>
