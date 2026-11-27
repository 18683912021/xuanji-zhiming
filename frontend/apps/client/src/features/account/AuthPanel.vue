<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import NavLink from '../../components/NavLink.vue'
import AppSwitch from '../../components/AppSwitch.vue'
import { apiMessage, authenticate, authenticateWechat, authStatus, identity, live } from '../../shared/api'
import { destination, go, type Query } from '../../shared/navigation'
import AuthField from './AuthField.vue'
import AuthLayout from './AuthLayout.vue'
import { emailPattern, finishAuth, guestReading, minPasswordLength, refreshAccountData, usernamePattern } from './authFlow'
import { login } from './state'

const props = defineProps<{ mode: 'login' | 'register'; query: Query }>()
const registering = computed(() => props.mode === 'register')
const title = computed(() => registering.value ? '创建账号' : '账号登录')
const identifier = ref('')
const nickname = ref('')
const password = ref('')
const confirmation = ref('')
const pending = ref(false)
const status = ref<{ email_codes: boolean; wechat_login: boolean }>()
const error = ref('')
const carry = ref(true)
const reading = computed(() => guestReading(props.query))
const canCarry = computed(() => !registering.value && identity.value?.is_guest && reading.value)
const redirectQuery = computed(() => {
  const { reset, identifier: _identifier, ...query } = props.query
  return query
})

onMounted(async () => {
  identifier.value = props.query.identifier || ''
  if (!live) return
  try { status.value = await authStatus() } catch { /* Password sign-in can still be retried. */ }
})

async function submit(withWechat = false) {
  if (pending.value) return
  error.value = ''
  const name = identifier.value.trim()
  if (!live) {
    if (name && login(name)) finishAuth(props.query)
    return
  }
  if (!withWechat) {
    if (registering.value ? !usernamePattern.test(name) : !(usernamePattern.test(name) || emailPattern.test(name))) {
      error.value = registering.value ? '请填写符合规则的用户名。' : '请输入用户名或有效的邮箱。'
      return
    }
    if (registering.value && [...password.value].length < minPasswordLength) {
      error.value = '密码至少需要 ' + minPasswordLength + ' 个字符。'
      return
    }
    if (!password.value) { error.value = '请输入密码。'; return }
    if (registering.value && confirmation.value !== password.value) { error.value = '两次输入的密码不一致。'; return }
  }
  pending.value = true
  try {
    const selectedReading = canCarry.value && carry.value ? reading.value : undefined
    const result = withWechat
      ? await authenticateWechat(selectedReading)
      : registering.value
        ? await authenticate('register', { username: name, password: password.value, display_name: nickname.value.trim() || undefined })
        : await authenticate('login', { identifier: name, password: password.value }, selectedReading)
    password.value = ''
    confirmation.value = ''
    await refreshAccountData()
    if (withWechat && !result.account.username) {
      go(destination('security', 'credentials', {
        ...props.query, onboarding: '1', relocated: result.handoff_reading_id || undefined,
      }), 'replace')
    } else {
      finishAuth(props.query, result.handoff_reading_id)
    }
  } catch (cause) {
    error.value = apiMessage(cause)
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <AuthLayout :title="live ? title : '体验登录'"
    :description="live ? (registering ? '创建后即可用用户名登录，邮箱可稍后绑定。' : '登录后继续查看你的档案、测算和对话。') : '体验数据保存在当前设备。'">
    <form @submit="submit()">
      <view class="credential-form">
        <AuthField v-model="identifier" id="account-identifier" :label="!live ? '体验昵称' : registering ? '用户名' : '用户名或邮箱'"
          :limit="registering ? 24 : 254" :placeholder="registering ? '输入用户名' : '输入用户名或已绑定的邮箱'"
          :hint="live && registering ? '以英文字母开头，3–24 位字母、数字或下划线。' : undefined" />
        <template v-if="live">
          <AuthField v-if="registering" v-model="nickname" id="account-nickname" label="昵称（选填）"
            :limit="48" placeholder="默认使用用户名" />
          <AuthField v-model="password" id="account-password" kind="password" label="密码"
            :placeholder="registering ? '至少 ' + minPasswordLength + ' 个字符' : '输入密码'" @confirm="!registering && submit()" />
          <AuthField v-if="registering" v-model="confirmation" id="account-confirm-password"
            kind="password" label="确认密码" placeholder="再输入一次密码" @confirm="submit()" />
          <view v-else class="auth-options">
            <text v-if="query.reset === 'done'" class="auth-advice">密码已更新。</text>
            <NavLink class="auth-text-link" :to="destination('security', 'reset', redirectQuery)">忘记密码</NavLink>
          </view>
          <view v-if="canCarry" class="switch-row">
            <text>把本次游客体验带入账号</text>
            <AppSwitch label="把本次游客体验带入账号" :checked="carry" @change="carry = $event" />
          </view>
        </template>
        <text v-if="error" role="alert" class="auth-error">{{ error }}</text>
        <button class="auth-submit" form-type="submit" :disabled="pending">
          {{ pending ? '正在处理…' : !live ? '进入体验' : registering ? '注册并登录' : '登录' }}
          <text v-if="!pending" aria-hidden="true">→</text>
        </button>
        <!-- #ifdef MP-WEIXIN -->
        <button v-if="live && !registering && status?.wechat_login" class="auth-secondary" :disabled="pending"
          @tap="submit(true)">微信授权登录</button>
        <!-- #endif -->
        <view v-if="live" class="auth-options auth-footer">
          <text>{{ registering ? '已有账号？' : '还没有账号？' }}</text>
          <NavLink class="auth-text-link" mode="redirect" :to="destination(registering ? 'login' : 'register', undefined, redirectQuery)">
            {{ registering ? '直接登录' : '注册账号' }}
          </NavLink>
        </view>
      </view>
    </form>
  </AuthLayout>
</template>

<style src="./auth.css" scoped></style>
