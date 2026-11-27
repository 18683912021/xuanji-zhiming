<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import DateField from '../../components/DateField.vue'
import SelectField from '../../components/SelectField.vue'
import ToolCard from '../../components/ToolCard.vue'
import { account, clearDemoAccount, deleteBirthProfile, feedback, logoutAccount, preferences, profiles, saveBirthProfile, updateAccount, type BirthProfile } from './state'
import { apiMessage, authStatus, bindWechat, identity as signedIdentity, live } from '../../shared/api'
import { clockOccurrences, timezones } from './birth'
import { remaining } from '../ai/state'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, makeId } from '../../shared/storage'

const props = defineProps<{ view: string; query: Query }>()
const profilePending = ref(false)
const wechatReady = ref(false)
const bindingWechat = ref(false)
watch(() => props.view, async (view) => {
  if (!live || view !== 'settings') return
  try {
    const status = await authStatus()
    wechatReady.value = status.wechat_login
  } catch {
    wechatReady.value = false
  }
}, { immediate: true })
function linkWechat() {
  if (bindingWechat.value) return
  confirmAction('绑定微信账号', '确认将当前微信绑定到此账号。绑定后可在小程序用微信登录。', async () => {
    if (bindingWechat.value) return
    bindingWechat.value = true
    try {
      await bindWechat()
      toast('微信账号已绑定。')
    } catch (cause) {
      toast(apiMessage(cause))
    } finally {
      bindingWechat.value = false
    }
  })
}
const edit = ref(account.state.value ? { ...account.state.value } : null)
watch(() => account.state.value, (value) => {
  if (!value) edit.value = null
  else if (!edit.value) edit.value = { ...value }
})
const entry = computed(() => profiles.state.value.find((item) => item.id === props.query.id))
const profile = ref<BirthProfile>(
  entry.value
    ? { ...entry.value }
    : {
        id: '',
        name: '',
        relation: '本人',
        gender: '暂不填写',
        date: '',
        time: '',
        city: '',
        timezone: 'Asia/Shanghai',
        occurrence: '',
        currentCity: '',
      },
)
const error = ref('')
watch(entry, (value) => {
  if (value && profile.value.id !== value.id) profile.value = { ...value }
})
const subject = ref('使用反馈')
const feedbackText = ref('')
const menu = [
  ['出生档案', '管理自己与他人的出生资料', '☯', destination('account', 'profiles')],
  ['体验记录', '查看测算、笔记和来源', '▤', destination('account', 'records')],
  ['我的收藏', '回看图鉴、日期与运势', '☆', destination('account', 'favorites')],
  ['深度报告', '查看已生成的报告', '▧', destination('ai', 'my-reports')],
  ['私人日记', '按日期写下观察', '▱', destination('account', 'journal')],
  ['历史对话', '新建、续聊和管理会话', '✧', destination('ai', 'history')],
  ['特别日期', '生日、提醒和倒数', '☼', destination('account', 'events')],
  ['消息中心', '私聊、邀请及通知', '◎', destination('social', 'messages')],
  ['体验权益', '免费额度、星币与任务', '◇', destination('commerce')],
  ['设置与隐私', '账号和通知管理', '⚙', destination('account', 'settings')],
] as const

function options(values: string[]) {
  return values.map((value) => ({ value, label: value }))
}
async function saveProfile() {
  error.value = ''
  if (live && !account.state.value) {
    go(destination('login', undefined, { nextView: 'profile-edit', id: props.query.id }), 'replace')
    return
  }
  if (!profile.value.name.trim() || !profile.value.date) {
    error.value = '请填写档案名称与出生日期。'
    return
  }
  if (profilePending.value) return
  profilePending.value = true
  try {
    const item = await saveBirthProfile({ ...profile.value, name: profile.value.name.trim() })
    go(destination('account', 'profile', { id: item.id }), 'replace')
  } catch (cause) {
    error.value = apiMessage(cause)
  } finally {
    profilePending.value = false
  }
}
function removeProfile() {
  const id = entry.value?.id
  if (!id) return
  confirmAction('删除出生档案', '已经保存的测算仍可查看当时的结果。', async () => {
    try {
      await deleteBirthProfile(id)
      go(destination('account', 'profiles'), 'replace')
    } catch (cause) {
      toast(apiMessage(cause))
    }
  })
}
async function logout() {
  try {
    const current = account.state.value
    if (!live && current) uni.setStorageSync('xuanji:client:last-account', current)
    await logoutAccount()
    go(destination('account'), 'replace')
  } catch (cause) {
    toast(apiMessage(cause))
  }
}
function deactivate() {
  confirmAction('注销体验账号', '移除本机体验登录信息。', () => {
    clearDemoAccount()
    go(destination('account'), 'replace')
  })
}
async function saveAccount() {
  if (edit.value && await updateAccount(edit.value)) toast('已保存个人资料。')
}
function sendFeedback() {
  if (!feedbackText.value.trim()) return
  if (
    feedback.write([
      { id: makeId(), category: subject.value, text: feedbackText.value.trim(), createdAt: dateKey() },
      ...feedback.state.value,
    ])
  ) {
    feedbackText.value = ''
    toast('反馈已保存到 Mock 环境。')
  }
}
</script>

<template>
  <view class="content-width stack">
    <template v-if="view === 'index'">
      <view class="split">
        <view class="panel stack"
          ><text class="avatar">{{ account.state.value?.nickname.slice(0, 1) || '玄' }}</text>
          <text class="panel-head">{{ account.state.value?.nickname || '你好，观星人' }}</text>
          <text class="muted">{{
            account.state.value
              ? account.state.value.bio || '在这里管理你的体验资料。'
              : '浏览公开内容，登录后可使用 AI 和保存档案。'
          }}</text>
          <view class="actions"
            ><NavLink v-if="!account.state.value" class="btn primary" :to="destination('login')"
              >{{ live ? '登录或注册' : '体验登录' }}</NavLink
            >
            <NavLink v-else class="btn primary" :to="destination('account', 'public-edit')"
              >编辑个人资料</NavLink
            >
            <NavLink
              v-if="account.state.value"
              class="btn"
              :to="destination('social', 'person', { id: 'self' })"
              >查看公开主页</NavLink
            >
            <NavLink class="btn" :to="destination('account', 'records')">体验记录</NavLink></view
          >
        </view>
        <view class="panel stack"
          ><text class="panel-head">今日体验权益</text
          ><view class="row"
            ><text>AI 追问</text><text class="gold">{{ remaining.ai }} 次</text></view
          >
          <view class="row"
            ><text>深度报告</text><text class="gold">{{ remaining.reports }} 次</text></view
          ><NavLink class="link" :to="destination('commerce')">权益详情 ›</NavLink></view
        >
      </view>
      <view class="cols-3"
        ><ToolCard
          v-for="[title, description, glyph, to] in menu"
          :key="title"
          :title="title"
          :description="description"
          :glyph="glyph"
          :to="to"
      /></view>
    </template>
    <template v-else-if="view === 'public-edit'">
      <view v-if="edit" class="panel stack account-form">
        <text class="avatar">{{ edit.nickname.slice(0, 1) || '玄' }}</text>
        <view
          ><text class="field-label">昵称</text><input v-model="edit.nickname" class="field" maxlength="16"
        /></view>
        <view
          ><text class="field-label">签名</text
          ><textarea v-model="edit.bio" class="field area" maxlength="100" />
        </view>
        <DateField v-model="edit.birth" label="生日" :end="dateKey()" />
        <SelectField
          v-model="edit.theme"
          label="主页主题"
          :options="options(['紫宸夜', '星雾紫', '玄夜金'])"
        />
        <view class="switch-row"
          ><text>公开生日月日</text
          ><AppSwitch
            label="公开生日月日"
            :checked="edit.publicBirthday"
            @change="edit.publicBirthday = $event"
        /></view>
        <view class="switch-row"
          ><text>公开星座</text
          ><AppSwitch label="公开星座" :checked="edit.publicSign" @change="edit.publicSign = $event"
        /></view>
        <view class="switch-row"
          ><text>公开 MBTI {{ edit.mbti }}</text
          ><AppSwitch label="公开 MBTI" :checked="edit.publicMbti" @change="edit.publicMbti = $event"
        /></view>
        <button
          class="btn primary"
          :disabled="!edit.nickname.trim()"
          @tap="saveAccount"
        >
          保存个人资料
        </button>
      </view>
      <NavLink v-else class="btn primary" :to="destination('login', undefined, { nextView: 'public-edit' })"
        >先登录账号</NavLink
      >
    </template>
    <template v-else-if="view === 'profiles'">
      <view class="actions"
        ><NavLink class="btn primary" :to="destination('account', 'profile-edit')"
          >新增出生档案</NavLink
        ></view
      >
      <view class="panel stack">
        <text v-if="!profiles.state.value.length" class="muted"
          >还没有自己的档案。也可以先用排盘页的示例试一遍。</text
        >
        <NavLink
          v-for="item in profiles.state.value"
          :key="item.id"
          class="row-link"
          :to="destination('account', 'profile', { id: item.id })"
        >
          <view
            ><text class="block">{{ item.name }}</text
            ><text class="muted small">{{ item.relation }} · {{ item.city || '地点待补充' }}</text></view
          ><text class="gold">查看 ›</text>
        </NavLink>
      </view>
    </template>
    <template v-else-if="view === 'profile'">
      <view v-if="entry" class="panel stack">
        <text class="avatar">{{ entry.name.slice(0, 1) }}</text
        ><text class="panel-head">{{ entry.name }} · {{ entry.relation }}</text>
        <text>出生日期 {{ entry.date }} · {{ entry.time || '时辰不详' }}</text
        ><text class="muted">{{ entry.city || '出生城市未填写' }} · {{ entry.timezone }}</text>
        <view class="actions">
          <NavLink class="btn primary" :to="destination('charts', 'bazi', { id: entry.id })">排八字</NavLink>
          <NavLink class="btn" :to="destination('charts', 'astro', { id: entry.id })">查看星盘</NavLink>
          <NavLink class="btn" :to="destination('charts', 'match', { id: entry.id })">进入合盘</NavLink>
          <NavLink class="btn" :to="destination('account', 'profile-edit', { id: entry.id })">编辑</NavLink
          ><button class="btn" @tap="removeProfile">删除</button>
        </view>
      </view>
      <text v-else class="panel muted">这份档案已不可用。</text>
    </template>
    <template v-else-if="view === 'profile-edit'">
      <view class="panel stack account-form">
        <view
          ><text class="field-label">档案名称</text
          ><input v-model="profile.name" class="field" maxlength="24" placeholder="例如自己、家人昵称"
        /></view>
        <view class="cols-2"
          ><SelectField
            v-model="profile.relation"
            label="关系"
            :options="options(['本人', '伴侣', '家人', '朋友', '其他'])" />
          <SelectField
            v-model="profile.gender"
            label="性别（可选）"
            :options="options(['暂不填写', '女', '男', '其他'])"
        /></view>
        <view class="cols-2"
          ><DateField v-model="profile.date" label="出生日期" start="1901-01-01" :end="dateKey()" /><DateField
            v-model="profile.time"
            label="出生时刻（可选）"
            mode="time"
        /></view>
        <SelectField v-if="live && profile.time" :model-value="profile.occurrence || ''"
          label="夏令时回拨（出生时刻出现两次时填写）" :options="clockOccurrences"
          @update:model-value="profile.occurrence = $event" />
        <view class="cols-2"
          ><view
            ><text class="field-label">出生城市</text
            ><input v-model="profile.city" class="field" maxlength="36" /></view
          ><SelectField
            v-model="profile.timezone"
            label="时区"
            :options="timezones"
        /></view>
        <view
          ><text class="field-label">现居城市（可选）</text
          ><input v-model="profile.currentCity" class="field" maxlength="36"
        /></view>
        <text v-if="error" class="error">{{ error }}</text
        ><button class="btn primary" :disabled="profilePending" @tap="saveProfile">保存出生档案</button>
      </view>
    </template>
    <template v-else-if="view === 'settings'">
      <view class="split">
        <view class="panel stack">
          <text class="panel-head">偏好与通知</text>
          <view class="switch-row"
            ><text>事件提醒</text
            ><AppSwitch
              label="事件提醒"
              :checked="preferences.state.value.reminders"
              @change="preferences.write({ ...preferences.state.value, reminders: $event })"
          /></view>
          <view class="switch-row"
            ><text>互动消息提醒</text
            ><AppSwitch
              label="互动消息提醒"
              :checked="preferences.state.value.messages"
              @change="preferences.write({ ...preferences.state.value, messages: $event })"
          /></view>
          <view class="switch-row"
            ><text>减少滚动动画</text
            ><AppSwitch
              label="减少滚动动画"
              :checked="preferences.state.value.reducedMotion"
              @change="preferences.write({ ...preferences.state.value, reducedMotion: $event })"
          /></view>
          <NavLink class="link" :to="destination('social', 'blocks')">已拉黑的用户 ›</NavLink>
        </view>
        <view class="panel stack">
          <text class="panel-head">账号与隐私</text
          ><text v-if="!live" class="notice">体验数据保存在当前设备。</text>
          <text v-if="account.state.value">当前账号 · {{ account.state.value.nickname }}</text>
          <template v-if="live && account.state.value">
            <text class="muted">{{ signedIdentity?.username ? '用户名 · ' + signedIdentity.username : '用户名 · 未设置' }}</text>
            <text v-if="signedIdentity?.is_admin" class="gold">账号角色 · 管理员</text>
            <text class="muted">{{ signedIdentity?.email ? '邮箱 · ' + signedIdentity.email : '邮箱 · 未绑定' }}</text>
            <text class="muted">{{ signedIdentity?.wechat_linked ? '微信 · 已绑定' : '微信 · 未绑定' }}</text>
            <NavLink class="link" :to="destination('security', 'credentials')">
              {{ signedIdentity?.username ? '更新密码 ›' : '设置跨端登录账号 ›' }}
            </NavLink>
            <NavLink v-if="signedIdentity?.password_set && !signedIdentity.email"
              class="link" :to="destination('security', 'email')">绑定邮箱 ›</NavLink>
            <!-- #ifdef MP-WEIXIN -->
            <button v-if="wechatReady && !signedIdentity?.wechat_linked" class="btn" :disabled="bindingWechat"
              @tap="linkWechat">绑定微信</button>
            <!-- #endif -->
          </template>
          <NavLink v-if="!account.state.value" class="link" :to="destination('login')">登录 ›</NavLink>
          <NavLink class="link" :to="destination('account', 'support')">联系客服与使用反馈 ›</NavLink>
          <view v-if="account.state.value" class="actions"
            ><button class="btn" @tap="logout">退出登录</button
            ><button v-if="!live" class="btn" @tap="deactivate">注销体验账号</button></view
          >
        </view>
      </view>
    </template>
    <template v-else-if="view === 'support'">
      <view class="split"
        ><view class="panel stack">
          <text class="panel-head">提交反馈</text
          ><SelectField
            v-model="subject"
            label="反馈类型"
            :options="options(['使用反馈', '资料问题', '内容纠错', '隐私请求'])"
          />
          <textarea
            v-model="feedbackText"
            class="field area"
            maxlength="600"
            placeholder="描述你遇到的情况"
          /><button class="btn primary" :disabled="!feedbackText.trim()" @tap="sendFeedback">
            保存反馈
          </button> </view
        ><view class="panel stack"
          ><text class="panel-head">我的反馈</text>
          <view v-for="item in feedback.state.value" :key="item.id" class="stack"
            ><text class="gold">{{ item.category }} · {{ item.createdAt }}</text
            ><text>{{ item.text }}</text
            ><text class="muted small">本机已记录</text></view
          >
          <text v-if="!feedback.state.value.length" class="muted">还没有反馈。</text></view
        ></view
      >
    </template>
  </view>
</template>
<style scoped>
.account-form {
  max-width: 680px;
}
</style>
