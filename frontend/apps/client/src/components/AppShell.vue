<script lang="ts">
// Switching main sections relaunches the page and creates a new header.
let previousHeaderTab: number | undefined
</script>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import NavLink from './NavLink.vue'
import { account } from '../features/account/state'
import { back, destination, type Section } from '../shared/navigation'

const props = withDefaults(defineProps<{
  section: Section
  title?: string
  subtitle?: string
  detail?: boolean
  entering?: boolean
}>(), { entering: true })
const menuOpen = ref(false)
watch(() => props.entering, (entering) => {
  if (!entering) menuOpen.value = false
})
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
  statusPadding = Math.max(0, capsule.top - (56 - capsule.height) / 2) + 'px'
  capsulePadding = capsule.width + 12 + 'px'
  if (uni.getWindowInfo().windowWidth - capsule.width < 270) {
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
const activeTabIndex = computed(() => tabs.findIndex((item) => item.section === active.value))
const startingTabIndex = previousHeaderTab ?? activeTabIndex.value
onMounted(() => { previousHeaderTab = activeTabIndex.value })

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
  <view class="app-shell" :class="{ 'home-shell': section === 'home' }" :style="{ '--status-padding': statusPadding }">
    <view class="site-header brand-bar">
      <view class="header-inner" :style="{ paddingRight: capsulePadding }">
        <NavLink class="brand" :to="destination('home')" mode="reLaunch">
          <AppIcon name="seal" class="brand-seal" /><text class="brand-lettering">玄机知命</text>
        </NavLink>
        <view class="desktop-tabs" aria-label="主导航">
          <view class="desktop-tab-track">
            <view
              class="desktop-tab-indicator"
              :class="{ sliding: startingTabIndex !== activeTabIndex }"
              :style="{
                width: `${100 / tabs.length}%`,
                '--tab-start': `${startingTabIndex * 100}%`,
                '--tab-end': `${activeTabIndex * 100}%`,
              }"
              aria-hidden="true"
            />
            <NavLink
              v-for="item in tabs"
              :key="item.section"
              class="desktop-tab"
              :class="{ active: item.section === active }"
              :aria-current="item.section === active ? 'page' : undefined"
              :to="destination(item.section)"
              mode="reLaunch"
            >
              {{ item.title }}
            </NavLink>
          </view>
        </view>
        <view class="header-actions">
          <NavLink
            class="header-login btn bar-control"
            :to="destination(account.state.value ? 'account' : 'login')"
          >
            {{ account.state.value ? '我的' : '登录' }}
          </NavLink>
          <button
            class="header-menu bar-control"
            :class="{ expanded: menuOpen }"
            :aria-label="menuOpen ? '收起菜单' : '展开菜单'"
            :aria-expanded="menuOpen"
            @tap="menuOpen = !menuOpen"
          >
            <AppIcon name="menu" />
          </button>
        </view>
      </view>
      <view class="header-drawer" :class="{ open: menuOpen }" :aria-hidden="!menuOpen" @tap="menuOpen = false">
        <NavLink
          v-for="item in tabs"
          :key="item.section"
          class="drawer-link"
          :class="{ active: item.section === active }"
          :aria-current="item.section === active ? 'page' : undefined"
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
    <view :class="{ 'page-arrival': entering && section !== 'home' }">
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
