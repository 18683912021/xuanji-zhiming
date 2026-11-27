<script setup lang="ts">
import { ref } from 'vue'

withDefaults(defineProps<{
  id: string
  label: string
  modelValue: string
  placeholder?: string
  hint?: string
  kind?: 'text' | 'password' | 'number'
  limit?: number
}>(), { kind: 'text', limit: 128 })
const emit = defineEmits<{ 'update:modelValue': [value: string]; confirm: [] }>()
const revealed = ref(false)
function input(event: Event) {
  const value = (event as CustomEvent<{ value: string }>).detail?.value ?? (event.target as HTMLInputElement)?.value
  emit('update:modelValue', value || '')
}
</script>

<template>
  <view class="credential-field">
    <label class="credential-label" :for="id">{{ label }}</label>
    <view class="credential-input">
      <input
        :id="id" :value="modelValue" :aria-label="label" :placeholder="placeholder"
        :type="kind === 'number' ? 'number' : 'text'" :password="kind === 'password' && !revealed"
        :maxlength="limit" placeholder-class="credential-placeholder"
        :confirm-type="kind === 'password' ? 'go' : 'next'"
        @input="input" @confirm="$emit('confirm')"
      />
      <button v-if="kind === 'password'" class="credential-reveal"
        :aria-label="(revealed ? '隐藏' : '显示') + label" @tap="revealed = !revealed">
        {{ revealed ? '隐藏' : '显示' }}
      </button>
      <slot />
    </view>
    <text v-if="hint" class="credential-hint">{{ hint }}</text>
  </view>
</template>

<style scoped>
.credential-field { min-width: 0; }
.credential-label { display: block; margin-bottom: 5px; font-size: 13px; color: #f0e6f2; text-shadow: 0 1px 5px #08040d; }
.credential-input {
  display: flex;
  align-items: center;
  min-height: 46px;
  border: 1px solid #bda08079;
  border-radius: 7px;
  background: linear-gradient(180deg, #08051037, #160e2220 57%, #36243c25);
  box-shadow: inset 0 2px 5px #09050e9c, inset 0 -1px #edd6a327, 0 1px #07040d99;
}
.credential-input:focus-within {
  border-color: #d2ad6f;
  box-shadow: inset 0 2px 5px #09050e9c, inset 0 -1px #edd6a335, 0 0 0 2px #d6b66c2a;
}
.credential-input input {
  flex: 1;
  min-width: 0;
  min-height: 44px;
  padding: 0 11px;
  color: #f3edf7;
  font-size: 15px;
}
.credential-placeholder { color: #aca0b9; }
.credential-reveal {
  padding: 10px 12px;
  color: #d4bdd9;
  background: transparent;
  font-size: 12px;
}
.credential-hint { display: block; margin-top: 4px; font-size: 12px; color: #c1b0cd; }
</style>
