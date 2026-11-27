<script setup lang="ts">
import AppIcon from '../../components/AppIcon.vue'
import NavLink from '../../components/NavLink.vue'
import { destination } from '../../shared/navigation'

defineProps<{ title: string; description?: string }>()
let headerTop = '0px'
let headerReserve = '0px'
// #ifdef MP-WEIXIN
const capsule = uni.getMenuButtonBoundingClientRect()
if (capsule.top > 0) {
  headerTop = Math.max(0, capsule.top - (56 - capsule.height) / 2) + 'px'
  headerReserve = capsule.width + 12 + 'px'
  if (uni.getWindowInfo().windowWidth - capsule.width < 270) {
    headerTop = capsule.bottom + 4 + 'px'
    headerReserve = '0px'
  }
}
// #endif
</script>

<template>
  <view class="auth-shell" :style="{ '--auth-header-top': headerTop, '--auth-header-reserve': headerReserve }">
    <view class="auth-scene" aria-hidden="true">
      <image class="auth-sky auth-sky-desktop" src="/static/auth/desktop.webp" mode="aspectFill" />
      <view class="auth-tail">
        <image src="/static/auth/mobile.webp" mode="scaleToFill" />
      </view>
      <image class="auth-sky auth-sky-mobile" src="/static/auth/mobile.webp" mode="widthFix" />
    </view>
    <view class="auth-header brand-bar">
      <view class="auth-header-inner">
        <NavLink class="auth-brand" :to="destination('home')" mode="reLaunch">
          <AppIcon name="seal" class="auth-brand-seal brand-seal" />
          <text class="brand-lettering">玄机知命</text>
        </NavLink>
        <NavLink class="auth-home bar-control" :to="destination('home')" mode="reLaunch">首页 <text aria-hidden="true">↗</text></NavLink>
      </view>
    </view>
    <view class="auth-stage">
      <view class="auth-card page-arrival">
        <view class="auth-card-heading">
          <view class="auth-card-ornament" aria-hidden="true"><text>✦</text></view>
          <text class="auth-title" role="heading" aria-level="1">{{ title }}</text>
          <text v-if="description" class="auth-description">{{ description }}</text>
        </view>
        <slot />
      </view>
    </view>
  </view>
</template>

<style scoped>
.auth-shell {
  --auth-header-height: 74px;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: #f0eaf6;
  background: #100b1c;
}
.auth-scene {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  background: #100b1c;
}
.auth-sky {
  position: absolute;
  display: block;
}
.auth-sky-desktop {
  inset: 0;
  width: 100%;
  height: 100%;
}
.auth-sky-mobile, .auth-tail { display: none; }
.auth-header {
  --bar-base: linear-gradient(180deg, #2b2034eb, #171020d9 55%, #100b16e3);
  position: relative;
  z-index: 1;
  padding-top: var(--auth-header-top);
}
.auth-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(100% - 88px, 1520px);
  min-height: var(--auth-header-height);
  margin: 0 auto;
  padding-right: var(--auth-header-reserve);
}
.auth-brand {
  display: inline-flex;
  align-items: center;
  gap: 13px;
  color: #f0ca7b;
  font: 650 clamp(23px, 2.25vw, 35px) / 1 var(--serif);
  letter-spacing: .07em;
}
.app-icon.auth-brand-seal {
  width: clamp(34px, 3.4vw, 48px);
  height: clamp(34px, 3.4vw, 48px);
}
.auth-home {
  display: inline-flex;
  justify-content: center;
  gap: 10px;
  align-items: center;
  min-height: 41px;
  padding: 6px 15px;
  font: 500 15px / 1.35 var(--serif);
}
.auth-home text { color: #ebc579; }
.auth-stage {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(365px, 438px);
  align-items: center;
  min-height: calc(100vh - var(--auth-header-height) - var(--auth-header-top) - 1px);
  width: min(100% - 112px, 1360px);
  margin: 0 auto;
  padding: clamp(34px, 4.1vw, 72px) clamp(18px, 3vw, 54px) clamp(36px, 4.4vw, 78px) 0;
}
.auth-card {
  position: relative;
  grid-column: 2;
  width: 100%;
  padding: clamp(27px, 3.1vw, 43px);
  border: 1px solid #e1b37497;
  border-radius: 18px;
  background-color: transparent;
  box-shadow:
    0 20px 38px -21px #07040cee,
    0 3px 0 -1px #432a25a1,
    inset 0 1px #fce2b342,
    inset 0 0 15px #edb77512;
}
.auth-card::before {
  position: absolute;
  inset: 6px;
  border: 1px solid #e6bc792e;
  border-radius: 13px;
  pointer-events: none;
  content: '';
}
.auth-card::after {
  position: absolute;
  inset: 9px;
  border-radius: 10px;
  pointer-events: none;
  content: '';
  background:
    linear-gradient(90deg, #f4cf7c, transparent) left top / 42px 1px no-repeat,
    linear-gradient(#f4cf7c, transparent) left top / 1px 42px no-repeat,
    linear-gradient(270deg, #deb269, transparent) right bottom / 42px 1px no-repeat,
    linear-gradient(0deg, #deb269, transparent) right bottom / 1px 42px no-repeat;
}
.auth-card-heading { margin-bottom: 24px; text-align: center; }
.auth-card-ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 138px;
  margin: 0 auto 13px;
  color: #ffdb83;
  font-size: 20px;
  line-height: 1;
  text-shadow: 0 1px #93632e, 0 0 13px #ffc87382;
}
.auth-card-ornament::before,
.auth-card-ornament::after {
  height: 1px;
  flex: 1;
  content: '';
  background: linear-gradient(90deg, transparent, #d5a458 69%, #f6d799);
}
.auth-card-ornament::after { transform: scaleX(-1); }
.auth-title {
  display: block;
  color: #fff0df;
  font: 700 clamp(32px, 3.7vw, 54px) / 1.18 var(--serif);
  letter-spacing: .09em;
  text-shadow: 0 1px #bf8f60bd, 0 3px 2px #07030b, 0 4px 10px #07030be8, 0 0 22px #0b0612;
}
.auth-description {
  display: block;
  margin-top: 9px;
  color: #d5c5da;
  font-size: 13px;
  line-height: 1.55;
  text-shadow: 0 1px 5px #08040d;
}
@media (max-width: 900px) {
  .auth-shell { --auth-header-height: 56px; }
  .auth-header-inner { width: calc(100% - 34px); }
  .auth-brand { gap: 9px; }
  .auth-home { min-height: 36px; gap: 5px; padding: 5px 10px; font-size: 13px; }
  .auth-sky-desktop { display: none; }
  .auth-tail {
    position: absolute;
    display: block;
    inset: 30% 0 0;
    overflow: hidden;
    -webkit-mask-image: linear-gradient(transparent, #000 30%);
    mask-image: linear-gradient(transparent, #000 30%);
  }
  .auth-tail image {
    position: absolute;
    bottom: 0;
    width: 100%;
    height: 200%;
  }
  .auth-sky-mobile {
    display: block;
    top: 8px;
    left: 50%;
    width: clamp(320px, 100vw, 705px);
    transform: translateX(-50%);
    -webkit-mask-image: linear-gradient(#000 62%, transparent 100%);
    mask-image: linear-gradient(#000 62%, transparent 100%);
  }
  .auth-stage {
    display: block;
    width: min(100% - 32px, 452px);
    padding: clamp(168px, 54vw, 360px) 0 max(38px, env(safe-area-inset-bottom));
  }
  .auth-card { padding: clamp(20px, 6.2vw, 33px); border-radius: 15px; }
  .auth-card::before { inset: 5px; border-radius: 11px; }
  .auth-card::after { inset: 8px; border-radius: 8px; }
  .auth-card-heading { margin-bottom: 19px; }
  .auth-card-ornament { margin-bottom: 8px; }
}
</style>
