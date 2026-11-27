<script setup lang="ts">
defineProps<{ label: string; modelValue: string; mode?: 'date' | 'time'; start?: string; end?: string }>()
defineOptions({ options: { virtualHost: true } })

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
function change(event: { detail: { value: string } }) {
  emit('update:modelValue', event.detail.value)
}
</script>
<template>
  <view>
    <text class="field-label">{{ label }}</text>
    <picker
      :mode="mode || 'date'"
      :value="modelValue"
      :start="mode === 'time' ? undefined : start || '1900-01-01'"
      :end="end || (mode === 'time' ? undefined : '2099-12-31')"
      @change="change"
    >
      <view class="select-field">{{ modelValue || '请选择' }} <text class="muted">⌄</text></view>
    </picker>
  </view>
</template>
