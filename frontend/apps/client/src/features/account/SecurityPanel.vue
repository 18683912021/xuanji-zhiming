<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import NavLink from '../../components/NavLink.vue'
import { apiMessage, authStatus, bindEmail, identity, live, resetPassword, restoreIdentity, sendEmailCode, updateCredentials, type EmailPurpose } from '../../shared/api'
import { destination, go, toast, type Query } from '../../shared/navigation'
import AuthField from './AuthField.vue'
import AuthLayout from './AuthLayout.vue'
import { emailPattern, finishAuth, minPasswordLength, usernamePattern } from './authFlow'

const props = defineProps<{ view: 'credentials' | 'email' | 'reset'; query: Query }>()
const dataReady = ref(false)
const status = ref<{ email_codes: boolean; wechat_login: boolean }>()
const member = computed(() => identity.value && !identity.value.is_guest ? identity.value : null)
const setting = computed(() => props.view === 'credentials')
const binding = computed(() => props.view === 'email')
const recovering = computed(() => props.view === 'reset')
const onboarding = computed(() => props.query.onboarding === '1' && setting.value)
const needsUsername = computed(() => setting.value && !member.value?.username)
const needsNewPassword = computed(() => recovering.value || (setting.value && (!member.value?.password_set || !needsUsername.value)))
const wechatProof = ref(false)
const canWechatVerify = computed(() => {
  // #ifdef MP-WEIXIN
  return setting.value && Boolean(status.value?.wechat_login && member.value?.wechat_linked)
  // #endif
  // #ifndef MP-WEIXIN
  return false
  // #endif
})
const withWechat = computed(() => setting.value && (!member.value?.password_set || wechatProof.value))
const needsCurrentPassword = computed(() => binding.value || (setting.value && !withWechat.value))
const title = computed(() => recovering.value ? '找回密码' : binding.value ? '绑定邮箱' : needsUsername.value ? '设置登录账号' : '更新密码')
const description = computed(() => {
  if (recovering.value) return '通过已绑定的邮箱验证身份。微信用户也可在小程序的账号设置中通过微信验证更新密码。'
  if (binding.value) return '绑定后可用此邮箱登录，也可通过它重设密码。'
  if (needsUsername.value) return '设置用户名和密码，即可在 PC、H5 和小程序登录同一账号。'
  return '更新密码后，其他设备需重新登录。'
})
const email = ref('')
const code = ref('')
const username = ref('')
const currentPassword = ref('')
const password = ref('')
const confirmation = ref('')
const pending = ref(false)
const sending = ref(false)
const error = ref('')
const notice = ref('')
const now = ref(Date.now())
const cooldowns = ref<Record<string, number>>({})
const emailKey = computed(() => email.value.trim().toLowerCase())
const countdown = computed(() => Math.max(0, Math.ceil(((cooldowns.value[emailKey.value] || 0) - now.value) / 1000)))
const validEmail = computed(() => emailPattern.test(emailKey.value))
const settingsPage = destination('account', 'settings')
const loginPage = computed(() => destination('login', undefined,
  recovering.value ? props.query : { nextView: 'settings' },
))
let timer: ReturnType<typeof setInterval> | undefined

onMounted(async () => {
  if (!live) { dataReady.value = true; return }
  await Promise.allSettled([
    restoreIdentity(),
    authStatus().then((value) => { status.value = value }).catch((cause) => { error.value = apiMessage(cause) }),
  ])
  dataReady.value = true
})
onUnmounted(() => { if (timer) clearInterval(timer) })
function tick() {
  now.value = Date.now()
  if (timer && Object.values(cooldowns.value).every((value) => value <= now.value)) {
    clearInterval(timer)
    timer = undefined
  }
}

async function requestCode() {
  if (!validEmail.value || !status.value?.email_codes || sending.value || countdown.value || pending.value) return
  error.value = ''
  notice.value = ''
  const address = emailKey.value
  const purpose: EmailPurpose = binding.value ? 'bind_email' : 'reset_password'
  sending.value = true
  try {
    const result = await sendEmailCode(address, purpose)
    tick()
    cooldowns.value[address] = now.value + result.cooldown * 1000
    timer ||= setInterval(tick, 500)
    if (address === emailKey.value) {
      notice.value = binding.value ? '验证码已发送，5 分钟内有效。' : '如果邮箱已绑定账号，你会收到有效期 5 分钟的验证码。'
    }
  } catch (cause) {
    if (address === emailKey.value) error.value = apiMessage(cause)
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (pending.value || sending.value) return
  error.value = ''
  if (needsUsername.value && !usernamePattern.test(username.value.trim())) { error.value = '请填写符合规则的用户名。'; return }
  if (needsCurrentPassword.value && !currentPassword.value) { error.value = '请输入当前密码。'; return }
  if (needsNewPassword.value) {
    if ([...password.value].length < minPasswordLength) {
      error.value = '新密码至少需要 ' + minPasswordLength + ' 个字符。'
      return
    }
    if (confirmation.value !== password.value) { error.value = '两次输入的密码不一致。'; return }
  }
  if (!setting.value) {
    if (!validEmail.value) { error.value = '请输入有效的邮箱。'; return }
    if (!/^[0-9]{6}$/.test(code.value)) { error.value = '请输入 6 位验证码。'; return }
  }
  if (withWechat.value && !canWechatVerify.value) { error.value = '请在微信小程序中完成验证。'; return }
  pending.value = true
  try {
    if (recovering.value) {
      await resetPassword(emailKey.value, code.value, password.value)
      go(destination('login', undefined, { ...props.query, identifier: emailKey.value, reset: 'done' }), 'replace')
      return
    }
    if (binding.value) {
      await bindEmail(emailKey.value, code.value, currentPassword.value)
      toast('邮箱已绑定。')
    } else {
      const newUsername = needsUsername.value
      await updateCredentials({
        username: newUsername ? username.value.trim() : undefined,
        password: needsNewPassword.value ? password.value : undefined,
        current_password: withWechat.value ? undefined : currentPassword.value,
      }, withWechat.value)
      toast(newUsername ? '登录账号已设置。' : '密码已更新。')
    }
    if (onboarding.value) finishAuth(props.query, props.query.relocated)
    else go(settingsPage, 'replace')
  } catch (cause) {
    error.value = apiMessage(cause)
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <AuthLayout :title="title" :description="description">
    <view v-if="!dataReady" class="auth-advice">正在检查账号状态…</view>
    <view v-else-if="!live || (!recovering && !member)" class="credential-form">
      <text class="auth-advice">{{ live ? '请先登录账号。' : '当前为本机体验模式。' }}</text>
      <NavLink class="auth-secondary" :to="loginPage" mode="redirect">返回登录</NavLink>
    </view>
    <view v-else-if="binding && (member?.email || !member?.password_set)" class="credential-form">
      <text class="auth-advice">{{ member?.email ? '当前账号已绑定 ' + member.email : '请先设置登录密码。' }}</text>
      <NavLink class="auth-secondary" :to="member?.email ? settingsPage : destination('security', 'credentials')" mode="redirect">
        {{ member?.email ? '返回设置' : '设置登录账号' }}
      </NavLink>
    </view>
    <view v-else-if="!setting && !status?.email_codes" class="credential-form">
      <text class="auth-advice">{{ error || '邮箱验证服务暂未启用。' }}</text>
      <text v-if="recovering" class="auth-advice">微信用户可在小程序登录后，通过微信验证重设密码。</text>
      <NavLink class="auth-secondary" :to="recovering ? loginPage : settingsPage" mode="redirect">{{ recovering ? '返回登录' : '返回设置' }}</NavLink>
    </view>
    <form v-else @submit="submit">
      <view class="credential-form">
        <AuthField v-if="needsUsername" v-model="username" id="security-username" label="用户名"
          :limit="24" placeholder="输入用户名" hint="以英文字母开头，3–24 位字母、数字或下划线。" />
        <template v-if="!setting">
          <AuthField v-model="email" id="security-email" label="邮箱" placeholder="输入邮箱" :limit="254" />
          <AuthField v-model="code" id="security-code" label="邮箱验证码" placeholder="输入 6 位验证码" kind="number" :limit="6">
            <button class="auth-code-button" :disabled="sending || pending || !validEmail || countdown > 0"
              @tap="requestCode">{{ sending ? '发送中…' : countdown ? countdown + ' 秒后重发' : '获取验证码' }}</button>
          </AuthField>
        </template>
        <AuthField v-if="needsCurrentPassword" v-model="currentPassword" id="security-current-password"
          label="当前密码" kind="password" placeholder="输入当前密码" />
        <AuthField v-if="needsNewPassword" v-model="password" id="security-new-password" label="新密码"
          kind="password" :placeholder="'至少 ' + minPasswordLength + ' 个字符'" />
        <AuthField v-if="needsNewPassword" v-model="confirmation" id="security-confirm-password" label="确认新密码"
          kind="password" placeholder="再输入一次密码" @confirm="submit" />
        <button v-if="canWechatVerify && member?.password_set" class="auth-text-link" :disabled="pending"
          @tap="wechatProof = !wechatProof">{{ wechatProof ? '改用当前密码验证' : '改用微信验证' }}</button>
        <text v-if="notice" class="auth-advice" aria-live="polite">{{ notice }}</text>
        <text v-if="error" class="auth-error" role="alert">{{ error }}</text>
        <button class="auth-submit" form-type="submit" :disabled="pending || sending">
          {{ pending ? '正在处理…' : binding ? '确认绑定' : withWechat ? '验证微信并保存' : '保存' }}
          <text v-if="!pending" aria-hidden="true">→</text>
        </button>
        <view class="auth-options auth-footer">
          <button v-if="onboarding" class="auth-text-link" :disabled="pending"
            @tap="finishAuth(query, query.relocated)">稍后设置</button>
          <NavLink v-else class="auth-text-link" :to="recovering ? loginPage : settingsPage" mode="redirect">
            {{ recovering ? '返回登录' : '返回设置' }}
          </NavLink>
        </view>
      </view>
    </form>
  </AuthLayout>
</template>

<style src="./auth.css" scoped></style>
