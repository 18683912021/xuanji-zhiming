<script setup lang="ts">
defineOptions({ options: { virtualHost: true } })
const props = defineProps<{ checked: boolean; label: string }>()
const emit = defineEmits<{ change: [checked: boolean] }>()
</script>

<template>
  <button
    class="app-switch"
    role="switch"
    :aria-label="label"
    :aria-checked="checked"
    @tap="emit('change', !props.checked)"
  >
    <view class="switch-track" :class="{ 'is-checked': checked }">
      <view class="switch-thumb"></view>
    </view>
  </button>
</template>

<style scoped>
.app-switch {
  width: 49px;
  min-height: 44px;
  margin: 0;
  flex: 0 0 49px;
  align-self: center;
  display: grid;
  place-items: center;
  background: transparent;
}
.switch-track {
  width: 44px;
  height: 24px;
  padding: 3px;
  border: 1px solid #8a6f96;
  border-radius: 12px;
  background: #20142e;
}
.switch-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #b8a5c8;
}
.switch-track.is-checked {
  border-color: #d5b079;
  background: #504036;
}
.is-checked .switch-thumb {
  transform: translateX(18px);
  background: var(--gold-gradient);
}
</style>
