<script setup lang="ts">
import { computed, ref } from 'vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import DateField from '../../components/DateField.vue'
import SelectField from '../../components/SelectField.vue'
import ToolCard from '../../components/ToolCard.vue'
import { account, feedback, login, preferences, profiles, updateAccount, type BirthProfile } from './state'
import { remaining } from '../ai/state'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, makeId } from '../../shared/storage'

const props = defineProps<{ view: string; query: Query }>()
const identity = ref('观星人')
const method = ref('体验账号')
const loggingIn = ref(false)
const edit = ref(account.state.value ? { ...account.state.value } : null)
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
        timezone: 'UTC+08:00',
        currentCity: '',
      },
)
const error = ref('')
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
function signIn() {
  if (loggingIn.value || !identity.value.trim()) return
  loggingIn.value = true
  const demoIdentity = method.value === '微信体验' ? '微信体验用户' : identity.value.trim()
  if (!login(demoIdentity)) {
    loggingIn.value = false
    return
  }
  const { next, nextView, id, role, source, profile, report } = props.query
  if (next === 'ai')
    go(destination('ai', nextView || 'new', { id, role, source, profile, report }), 'replace')
  else go(destination('account', nextView || undefined, { id }), 'replace')
}
function saveProfile() {
  error.value = ''
  if (!profile.value.name.trim() || !profile.value.date) {
    error.value = '请填写档案名称与出生日期。'
    return
  }
  const item: BirthProfile = {
    ...profile.value,
    name: profile.value.name.trim(),
    id: profile.value.id || makeId(),
  }
  if (profiles.write([item, ...profiles.state.value.filter((value) => value.id !== item.id)]))
    go(destination('account', 'profile', { id: item.id }), 'replace')
}
function removeProfile() {
  if (!entry.value) return
  const id = entry.value.id
  confirmAction('删除出生档案', '删除本机档案。已经保存的测算仍可查看当时的结果。', () => {
    if (profiles.write(profiles.state.value.filter((item) => item.id !== id)))
      go(destination('account', 'profiles'), 'replace')
  })
}
function logout() {
  const current = account.state.value
  if (current) uni.setStorageSync('xuanji:client:last-account', current)
  if (account.write(null)) go(destination('account'), 'replace')
}
function deactivate() {
  confirmAction('注销 Mock 账号', '移除本机登录信息。私人记录可在各自的详情页删除。', () => {
    uni.removeStorageSync('xuanji:client:last-account')
    if (account.write(null)) go(destination('account'), 'replace')
  })
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
              ? account.state.value.bio || '在这里管理本机体验资料。'
              : '浏览公开内容，或用体验账号试用 AI 与个人资料。'
          }}</text>
          <view class="actions"
            ><NavLink v-if="!account.state.value" class="btn primary" :to="destination('account', 'login')"
              >体验登录</NavLink
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
            <NavLink class="btn" :to="destination('account', 'records')">本机记录</NavLink></view
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
    <template v-else-if="view === 'login'">
      <view class="panel stack account-form">
        <text class="panel-head">进入玄机知命</text
        ><text class="notice">使用 Mock 账号继续。这里无需真实密码或短信验证码，数据保存在当前设备。</text>
        <SelectField
          v-model="method"
          label="登录方式"
          :options="options(['体验账号', '邮箱体验', '手机体验', '微信体验'])"
        />
        <view v-if="method !== '微信体验'"
          ><text class="field-label">{{ method === '体验账号' ? '体验昵称' : '演示账号' }}</text
          ><input v-model="identity" class="field" maxlength="40" placeholder="例如观星人"
        /></view>
        <button
          class="btn primary"
          :disabled="loggingIn || (method !== '微信体验' && !identity.trim())"
          @tap="signIn"
        >
          登录体验
        </button>
      </view>
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
          @tap="updateAccount(edit) && toast('已保存个人资料。')"
        >
          保存个人资料
        </button>
      </view>
      <NavLink v-else class="btn primary" :to="destination('account', 'login', { nextView: 'public-edit' })"
        >先用体验账号登录</NavLink
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
          ><DateField v-model="profile.date" label="出生日期" :end="dateKey()" /><DateField
            v-model="profile.time"
            label="出生时刻（可选）"
            mode="time"
        /></view>
        <view class="cols-2"
          ><view
            ><text class="field-label">出生城市</text
            ><input v-model="profile.city" class="field" maxlength="36" /></view
          ><SelectField
            v-model="profile.timezone"
            label="时区"
            :options="options(['UTC+08:00', 'UTC+00:00', 'UTC+09:00', 'UTC-05:00'])"
        /></view>
        <view
          ><text class="field-label">现居城市（可选）</text
          ><input v-model="profile.currentCity" class="field" maxlength="36"
        /></view>
        <text v-if="error" class="error">{{ error }}</text
        ><button class="btn primary" @tap="saveProfile">保存出生档案</button>
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
          ><text class="notice">体验版 v0.1。数据保存在当前设备，换端后会使用各自的本机记录。</text>
          <text v-if="account.state.value">当前账号 · {{ account.state.value.nickname }}</text>
          <NavLink class="link" :to="destination('account', 'login')">Mock 账号登录或切换 ›</NavLink>
          <NavLink class="link" :to="destination('account', 'support')">联系客服与使用反馈 ›</NavLink>
          <view v-if="account.state.value" class="actions"
            ><button class="btn" @tap="logout">退出登录</button
            ><button class="btn" @tap="deactivate">注销体验账号</button></view
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
