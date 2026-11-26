<script setup lang="ts">
import { computed } from 'vue'
defineOptions({ options: { virtualHost: true } })

const props = defineProps<{
  label: string
  modelValue: string
  options: { value: string; label: string }[]
  placeholder?: string
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const index = computed(() =>
  Math.max(
    0,
    props.options.findIndex((item) => item.value === props.modelValue),
  ),
)
const name = computed(() => props.options.find((item) => item.value === props.modelValue)?.label)
function change(event: { detail: { value: string | number } }) {
  const selection = props.options[Number(event.detail.value)]
  if (selection) emit('update:modelValue', selection.value)
}
</script>
<template>
  <view>
    <text class="field-label">{{ label }}</text>
    <picker :range="options" range-key="label" :value="index" @change="change">
      <view class="select-field">{{ name || placeholder || '请选择' }} <text class="muted">⌄</text></view>
    </picker>
  </view>
</template>
