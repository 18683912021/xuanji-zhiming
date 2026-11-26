<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { onLoad, onHide } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { account, availableProfiles } from '../../features/account/state'
import { readings } from '../../features/divination/records'
import {
  credits,
  mockReply,
  newSession,
  officialRoles,
  privateRoles,
  profileContext,
  readingContext,
  remaining,
  reportContext,
  reports,
  reportTemplates,
  roleForReading,
  roles,
  sessions,
  updateSession,
  type Context,
  type Message,
  type Report,
  type Role,
} from '../../features/ai/state'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, displayDate, makeId } from '../../shared/storage'

const titles: Record<string, string> = {
  index: 'AI 对话',
  role: '角色详情',
  history: '历史对话',
  new: '新建对话',
  chat: '解读对话',
  custom: '自定义角色',
  'role-edit': '编辑私有角色',
  reports: '深度报告',
  preview: '报告预览',
  report: '报告详情',
  'my-reports': '我的报告',
}
const query = ref<Query>({})
const view = computed(() => (query.value.view && query.value.view in titles ? query.value.view : 'index'))
const roleId = ref('astrologer')
const sourceId = ref('')
const profileId = ref('')
const reportId = ref('')
const search = ref('')
const category = ref('全部')
const input = ref('')
const rename = ref('')
const renaming = ref(false)
const changeContext = ref(false)
const pending = ref(false)
const reportPending = ref(false)
const error = ref('')
const status = ref('')
const localCredit = computed(() => remaining.value.ai)
const role = computed(() => roles.value.find((item) => item.id === (query.value.id || roleId.value)))
const session = computed(() => sessions.state.value.find((item) => item.id === query.value.id))
const sessionRole = computed(() => roles.value.find((item) => item.id === session.value?.roleId))
const history = computed(() =>
  [...sessions.state.value]
    .sort((a, b) => b.updated.localeCompare(a.updated))
    .filter((item) => (item.title + item.roleName).includes(search.value.trim())),
)
const template = computed(
  () => reportTemplates.find((item) => item.id === query.value.id) || reportTemplates[0]!,
)
const report = computed(() => reports.state.value.find((item) => item.id === query.value.id))
const selectedContext = computed(
  () => readingContext(sourceId.value) || reportContext(reportId.value) || profileContext(profileId.value),
)
const columnSource = computed(() => [
  { value: '', label: '不关联体验' },
  ...readings.state.value.map((item) => ({
    value: item.id,
    label: item.title + ' · ' + displayDate(item.date),
  })),
])
const columnProfile = computed(() => [
  { value: '', label: '不关联档案' },
  ...availableProfiles.value.map((item) => ({ value: item.id, label: item.name })),
])
const columnReport = computed(() => [
  { value: '', label: '不关联报告' },
  ...reports.state.value.map((item) => ({ value: item.id, label: item.title })),
])
const roleOptions = computed(() => roles.value.map((item) => ({ value: item.id, label: item.name })))
const showSources = computed(() => view.value !== 'preview')
let timer: ReturnType<typeof setTimeout> | undefined
let reportTimer: ReturnType<typeof setTimeout> | undefined
let run: { sessionId: string; message: Message; history: Message[]; role?: Role } | undefined

const formName = ref('')
const formIntro = ref('')
const formSpecialty = ref(officialRoles[0]!.id)
const formQuestions = ref('')

onLoad((params) => {
  query.value = params || {}
  sourceId.value = query.value.source || ''
  profileId.value = query.value.profile || ''
  reportId.value = query.value.report || ''
  roleId.value =
    query.value.role || roleForReading(readings.state.value.find((item) => item.id === sourceId.value)?.kind)
  if (view.value === 'role-edit') {
    const item = privateRoles.state.value.find((entry) => entry.id === query.value.id)
    if (item) {
      formName.value = item.name
      formIntro.value = item.opening
      formSpecialty.value =
        officialRoles.find((entry) => entry.specialty === item.specialty)?.id || 'astrologer'
      formQuestions.value = item.questions.join('\n')
    }
  }
})
onHide(stopRun)
onUnmounted(() => {
  stopRun()
  clearTimeout(reportTimer)
})

function chooseContext(kind: 'reading' | 'profile' | 'report', value: string) {
  if (kind === 'reading') {
    sourceId.value = value
    if (value) {
      profileId.value = ''
      reportId.value = ''
    }
  } else if (kind === 'profile') {
    profileId.value = value
    if (value) {
      sourceId.value = ''
      reportId.value = ''
    }
  } else {
    reportId.value = value
    if (value) {
      sourceId.value = ''
      profileId.value = ''
    }
  }
}
function openNew() {
  const selected = roles.value.find((item) => item.id === roleId.value)
  if (!selected) return
  if (!account.state.value) {
    go(
      destination('account', 'login', {
        next: 'ai',
        nextView: 'new',
        role: roleId.value,
        source: sourceId.value,
        profile: profileId.value,
        report: reportId.value,
      }),
      'replace',
    )
    return
  }
  const item = newSession(selected, selectedContext.value)
  if (item) go(destination('ai', 'chat', { id: item.id }), 'replace')
}
function begin(question: string, retryId?: string) {
  const current = session.value
  const text = question.trim()
  if (!current || !text || pending.value) return
  if (!remaining.value.ai) {
    error.value = '今日体验次数已用完。明天可以继续。'
    return
  }
  error.value = ''
  status.value = '正在读取当前资料并整理示例解读…'
  input.value = ''
  const old = retryId && current.messages.find((item) => item.id === retryId)
  const context = old ? old.context : current.context
  const message: Message = { id: retryId || makeId(), question: text, context, status: 'stopped' }
  const messages = old
    ? current.messages.map((item) => (item.id === retryId ? message : item))
    : [...current.messages, message]
  if (
    !updateSession(current.id, {
      messages,
      ...(current.messages.length ? {} : { title: current.context?.title || text.slice(0, 26) }),
    })
  )
    return
  run = {
    sessionId: current.id,
    message,
    history: current.messages.filter((item) => item.id !== retryId),
    role: sessionRole.value,
  }
  pending.value = true
  timer = setTimeout(finishRun, 650)
}
function finishRun() {
  const current = run
  run = undefined
  pending.value = false
  if (!current) return
  const item = sessions.state.value.find((entry) => entry.id === current.sessionId)
  if (!item) return
  const answer = mockReply(current.role, current.message.question, current.message.context, current.history)
  if (
    updateSession(item.id, {
      messages: item.messages.map((message) =>
        message.id === current.message.id ? { ...message, answer, status: 'complete' } : message,
      ),
    })
  ) {
    credits.write({ ...remaining.value, ai: Math.max(0, remaining.value.ai - 1) })
    status.value = ''
  } else {
    status.value = '回复保存失败，可以重试。'
  }
}
function stopRun() {
  clearTimeout(timer)
  if (!run) return
  run = undefined
  pending.value = false
  status.value = '已停止。你可以修改问题或重试。'
}
function attachContext() {
  if (!session.value || pending.value) return
  const id = session.value.id
  const next = selectedContext.value
  confirmAction('更新关联资料', '新消息将使用选中的资料，历史回答保留原来的引用。', () => {
    if (updateSession(id, { context: next })) changeContext.value = false
  })
}
function saveRole() {
  if (!formName.value.trim() || !formIntro.value.trim()) return
  const base = officialRoles.find((item) => item.id === formSpecialty.value) || officialRoles[0]!
  const item: Role = {
    id: query.value.id || makeId(),
    name: formName.value.trim(),
    glyph: base.glyph,
    specialty: base.specialty,
    opening: formIntro.value.trim(),
    questions: formQuestions.value
      .split(/\n+/)
      .map((text) => text.trim())
      .filter(Boolean)
      .slice(0, 4),
    privateRole: true,
  }
  if (privateRoles.write([item, ...privateRoles.state.value.filter((entry) => entry.id !== item.id)]))
    go(destination('ai', 'custom'), 'replace')
}
function removeSession(itemId: string) {
  confirmAction('删除对话', '这个会话及其消息会从本机删除。', () => {
    if (sessions.write(sessions.state.value.filter((item) => item.id !== itemId)) && view.value === 'chat')
      go(destination('ai', 'history'), 'replace')
  })
}
function generateReport() {
  if (reportPending.value) return
  error.value = ''
  if (!remaining.value.reports) {
    error.value = '今日报告次数已用尽。'
    return
  }
  if (!selectedContext.value) {
    error.value = '请选择一份体验或出生档案。'
    return
  }
  const selected = template.value
  const source = selectedContext.value
  reportPending.value = true
  reportTimer = setTimeout(() => {
    reportPending.value = false
    const item: Report = {
      id: makeId(),
      template: selected.id,
      title: selected.name,
      category: selected.category,
      source,
      createdAt: dateKey(),
      sections: selected.sections.map((title, index) => ({
        title,
        content: [
          source.title + ' · ' + source.summary,
          source.evidence?.content || '根据选定资料展示章节样式。可回原始资料核查字段。',
          '给自己列一个可观察的小目标，在新的一周回看它有没有变化。',
        ][index]!,
      })),
    }
    if (reports.write([item, ...reports.state.value])) {
      credits.write({ ...remaining.value, reports: Math.max(0, remaining.value.reports - 1) })
      go(destination('ai', 'report', { id: item.id }), 'replace')
    }
  }, 500)
}
function removeReport(id: string) {
  confirmAction('删除报告', '这份报告会从本机删除。', () => {
    if (reports.write(reports.state.value.filter((item) => item.id !== id)))
      go(destination('ai', 'my-reports'), 'replace')
  })
}

function toggleRename(title: string) {
  rename.value = title
  renaming.value = !renaming.value
}

function saveTitle(id: string) {
  if (updateSession(id, { title: rename.value.trim() })) renaming.value = false
}
</script>

<template>
  <AppShell
    section="ai"
    :title="view === 'chat' ? session?.title || titles.chat : titles[view]"
    :detail="view !== 'index'"
  >
    <view class="content-width stack">
      <template v-if="view === 'index'">
        <view class="section-heading"
          ><text class="section-title">选择专业角色</text
          ><NavLink class="link" :to="destination('ai', 'history')">历史对话 ›</NavLink></view
        >
        <view class="cols-3">
          <NavLink
            v-for="item in roles"
            :key="item.id"
            class="panel stack role-card"
            :to="destination('ai', 'role', { id: item.id })"
          >
            <text class="avatar">{{ item.glyph }}</text
            ><text class="panel-head">{{ item.name }}</text
            ><text class="muted">{{ item.specialty }}</text
            ><text class="gold small">查看角色 ›</text>
          </NavLink>
        </view>
        <view class="actions"
          ><NavLink class="btn primary" :to="destination('ai', 'new')">新建对话</NavLink
          ><NavLink class="btn" :to="destination('ai', 'custom')">管理私有角色</NavLink
          ><NavLink class="btn" :to="destination('ai', 'reports')">深度报告</NavLink></view
        >
      </template>
      <view v-else-if="view === 'role'" class="panel stack">
        <template v-if="role"
          ><text class="avatar">{{ role.glyph }}</text
          ><text class="panel-head">{{ role.name }}</text
          ><text class="gold">{{ role.specialty }}</text
          ><text>{{ role.opening }}</text>
          <text v-for="question in role.questions" :key="question" class="notice">{{ question }}</text>
          <NavLink class="btn primary" :to="destination('ai', 'new', { role: role.id })"
            >新建对话</NavLink
          ></template
        >
        <text v-else class="muted">这个角色已不可用。</text>
      </view>
      <template v-else-if="view === 'history'">
        <view class="actions"
          ><NavLink class="btn primary" :to="destination('ai', 'new')">新建对话</NavLink></view
        >
        <input v-model="search" class="field" placeholder="搜索标题或角色" />
        <view class="panel stack">
          <text v-if="!history.length" class="muted">没有符合条件的对话。</text>
          <view v-for="item in history" :key="item.id" class="row">
            <NavLink :to="destination('ai', 'chat', { id: item.id })"
              ><text class="block">{{ item.title }}</text
              ><text class="muted small"
                >{{ item.roleName }} · {{ displayDate(item.updated) }} ·
                {{ item.messages.length }} 条问题</text
              ></NavLink
            >
            <button class="link" @tap="removeSession(item.id)">删除</button>
          </view>
        </view>
      </template>
      <template v-else-if="view === 'new' || view === 'preview'">
        <view class="workspace">
          <view class="panel stack">
            <SelectField v-if="view === 'new'" v-model="roleId" label="选择角色" :options="roleOptions" />
            <SelectField
              :model-value="sourceId"
              label="关联体验"
              :options="columnSource"
              @update:model-value="chooseContext('reading', $event)"
            />
            <SelectField
              :model-value="profileId"
              label="关联档案"
              :options="columnProfile"
              @update:model-value="chooseContext('profile', $event)"
            />
            <SelectField
              v-if="showSources"
              :model-value="reportId"
              label="关联报告"
              :options="columnReport"
              @update:model-value="chooseContext('report', $event)"
            />
            <text v-if="error" class="error">{{ error }}</text>
            <button v-if="view === 'new'" class="btn primary" @tap="openNew">开启独立会话</button>
            <button v-else class="btn primary" :disabled="reportPending" @tap="generateReport">
              {{ reportPending ? '正在生成…' : '生成体验报告' }}
            </button>
          </view>
          <view class="panel stack">
            <text class="panel-head">{{
              view === 'new' ? roles.find((item) => item.id === roleId)?.name : template.name
            }}</text>
            <text v-if="view === 'preview'" class="muted">{{ template.description }}</text>
            <text class="notice">{{
              selectedContext
                ? selectedContext.title + ' · ' + selectedContext.summary
                : view === 'preview'
                  ? '先选择一条体验或一份档案，再生成报告。'
                  : '可从空白对话开始，也可以带上一份资料。'
            }}</text>
            <NavLink v-if="selectedContext" class="link" :to="selectedContext.to">打开所选资料 ›</NavLink>
            <view v-if="view === 'preview'" class="stack"
              ><text v-for="section in template.sections" :key="section" class="row">{{ section }}</text
              ><text class="gold small">今日体验报告剩余 {{ remaining.reports }} 次</text></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'chat'">
        <view v-if="!session" class="panel muted"
          >找不到这份会话。<NavLink class="link" :to="destination('ai', 'history')"
            >回到历史对话 ›</NavLink
          ></view
        >
        <view v-else class="workspace chat">
          <view class="panel stack">
            <text class="panel-head">{{ session.roleName }}</text
            ><text class="muted">今日 AI 体验剩余 {{ localCredit }} 次</text>
            <NavLink v-if="session.context" class="row-link" :to="session.context.to"
              ><text>{{ session.context.title }}</text
              ><text class="gold">来源 ›</text></NavLink
            >
            <button class="btn" :disabled="pending" @tap="changeContext = !changeContext">关联资料</button>
            <view v-if="changeContext" class="stack"
              ><SelectField
                :model-value="sourceId"
                label="选择体验"
                :options="columnSource"
                @update:model-value="chooseContext('reading', $event)"
              />
              <SelectField
                :model-value="profileId"
                label="选择档案"
                :options="columnProfile"
                @update:model-value="chooseContext('profile', $event)"
              />
              <SelectField
                :model-value="reportId"
                label="选择报告"
                :options="columnReport"
                @update:model-value="chooseContext('report', $event)"
              />
              <button class="btn primary" @tap="attachContext">确认更新</button></view
            >
            <NavLink
              class="btn"
              :to="
                destination('ai', 'new', {
                  role: session.roleId,
                  source: session.context?.kind === 'reading' ? session.context.id : undefined,
                  profile: session.context?.kind === 'profile' ? session.context.id : undefined,
                  report: session.context?.kind === 'report' ? session.context.id : undefined,
                })
              "
              >开启独立会话</NavLink
            >
            <button class="link" @tap="toggleRename(session.title)">重命名</button>
            <view v-if="renaming" class="stack"
              ><input v-model="rename" class="field" maxlength="36" /><button
                class="btn"
                :disabled="!rename.trim()"
                @tap="saveTitle(session.id)"
              >
                保存标题
              </button></view
            >
            <NavLink class="link" :to="destination('ai', 'history')">历史对话 ›</NavLink>
            <button class="link" @tap="removeSession(session.id)">删除会话</button>
          </view>
          <view class="panel stack chat-main">
            <text class="notice">Mock 对话 · 示例回答根据已选资料和当前会话生成。</text>
            <text v-if="!session.messages.length" class="muted">{{ sessionRole?.opening }}</text>
            <view v-for="message in session.messages" :key="message.id" class="stack message-pair">
              <text class="bubble question">{{ message.question }}</text>
              <view v-if="message.answer" class="bubble response"
                ><text>{{ message.answer }}</text>
                <NavLink v-if="message.context" class="link block" :to="message.context.to"
                  >依据 · {{ message.context.evidence?.title || message.context.title }} ›</NavLink
                ></view
              >
              <button v-else-if="!pending" class="link" @tap="begin(message.question, message.id)">
                重试这条问题
              </button>
            </view>
            <view v-if="!session.messages.length" class="chips"
              ><button
                v-for="question in sessionRole?.questions || []"
                :key="question"
                class="chip"
                @tap="input = question"
              >
                {{ question }}
              </button></view
            >
            <text v-if="status" class="muted small">{{ status }}</text
            ><text v-if="error" class="error">{{ error }}</text>
            <textarea v-model="input" class="field area" maxlength="600" placeholder="写下想追问的内容" />
            <view class="actions"
              ><button class="btn primary" :disabled="pending || !input.trim()" @tap="begin(input)">
                发送</button
              ><button v-if="pending" class="btn" @tap="stopRun">停止生成</button></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'custom'">
        <view class="actions"
          ><NavLink class="btn primary" :to="destination('ai', 'role-edit')">创建私有角色</NavLink></view
        >
        <view class="panel stack"
          ><text v-if="!privateRoles.state.value.length" class="muted">你还没有创建角色。</text>
          <view v-for="item in privateRoles.state.value" :key="item.id" class="row">
            <NavLink :to="destination('ai', 'role', { id: item.id })"
              >{{ item.name }} · {{ item.specialty }}</NavLink
            >
            <view class="actions"
              ><NavLink class="link" :to="destination('ai', 'role-edit', { id: item.id })">编辑</NavLink>
              <button
                class="link"
                @tap="
                  confirmAction('删除角色', '历史会话仍可回看。', () =>
                    privateRoles.write(privateRoles.state.value.filter((entry) => entry.id !== item.id)),
                  )
                "
              >
                删除
              </button></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'role-edit'">
        <view class="panel stack">
          <view
            ><text class="field-label">角色名称</text
            ><input v-model="formName" class="field" maxlength="24" placeholder="例如我的星盘助理"
          /></view>
          <SelectField
            v-model="formSpecialty"
            label="擅长领域"
            :options="officialRoles.map((item) => ({ value: item.id, label: item.specialty }))"
          />
          <view
            ><text class="field-label">开场白</text
            ><textarea v-model="formIntro" class="field area" maxlength="180" />
          </view>
          <view
            ><text class="field-label">建议问题（每行一条）</text
            ><textarea v-model="formQuestions" class="field area" maxlength="240" />
          </view>
          <button class="btn primary" :disabled="!formName.trim() || !formIntro.trim()" @tap="saveRole">
            保存私有角色
          </button>
        </view>
      </template>
      <template v-else-if="view === 'reports' || view === 'my-reports'">
        <view class="section-heading"
          ><text class="section-title">{{ view === 'my-reports' ? '已生成报告' : '选择报告类型' }}</text>
          <NavLink class="link" :to="destination('ai', view === 'my-reports' ? 'reports' : 'my-reports')"
            >{{ view === 'my-reports' ? '报告目录' : '我的报告' }} ›</NavLink
          ></view
        >
        <view class="chips"
          ><button
            v-for="item in ['全部', ...reportTemplates.map((item) => item.category)]"
            :key="item"
            class="chip"
            :class="{ selected: category === item }"
            @tap="category = item"
          >
            {{ item }}
          </button></view
        >
        <view v-if="view === 'reports'" class="cols-3">
          <NavLink
            v-for="item in reportTemplates.filter(
              (item) => category === '全部' || item.category === category,
            )"
            :key="item.id"
            class="panel stack"
            :to="destination('ai', 'preview', { id: item.id, source: sourceId })"
          >
            <text class="panel-head">{{ item.name }}</text
            ><text class="muted">{{ item.description }}</text
            ><text class="gold small">查看报告样例 ›</text>
          </NavLink>
        </view>
        <view v-else class="panel stack"
          ><input v-model="search" class="field" placeholder="按名称、资料或日期筛选" />
          <NavLink
            v-for="item in reports.state.value.filter(
              (item) =>
                (category === '全部' || item.category === category) &&
                (item.title + (item.source?.title || '') + item.createdAt).includes(search),
            )"
            :key="item.id"
            class="row-link"
            :to="destination('ai', 'report', { id: item.id })"
          >
            <text>{{ item.title }}</text
            ><text class="muted">{{ item.createdAt }} ›</text></NavLink
          >
          <text v-if="!reports.state.value.length" class="muted">你还没有生成报告。</text>
        </view>
      </template>
      <template v-else-if="view === 'report'">
        <view v-if="report" class="workspace">
          <view class="panel stack"
            ><text class="panel-head">报告目录</text
            ><button
              v-for="(part, index) in report.sections"
              :key="part.title"
              class="link"
              @tap="goReportPart(index)"
            >
              {{ part.title }} ›
            </button>
            <NavLink v-if="report.source" class="link" :to="report.source.to">原始资料 ›</NavLink></view
          >
          <view class="stack"
            ><view class="panel stack"
              ><text class="panel-head">{{ report.title }}</text
              ><text class="muted">{{ report.createdAt }} · Mock 报告</text></view
            >
            <view
              v-for="(part, index) in report.sections"
              :id="'part-' + index"
              :key="part.title"
              class="panel stack"
              ><text class="panel-head">{{ part.title }}</text
              ><text>{{ part.content }}</text></view
            >
            <view class="actions"
              ><NavLink
                class="btn primary"
                :to="destination('ai', 'new', { role: 'report', report: report.id })"
                >继续追问</NavLink
              >
              <NavLink
                class="btn"
                :to="
                  destination('ai', 'preview', {
                    id: report.template,
                    source: report.source?.kind === 'reading' ? report.source.id : undefined,
                    profile: report.source?.kind === 'profile' ? report.source.id : undefined,
                  })
                "
                >重新生成</NavLink
              >
              <NavLink class="btn" :to="destination('account', 'share-preview', { report: report.id })"
                >分享摘要</NavLink
              >
              <button class="btn" @tap="removeReport(report.id)">删除报告</button></view
            >
          </view>
        </view>
        <text v-else class="panel muted">报告已删除或当前设备没有这份报告。</text>
      </template>
    </view>
  </AppShell>
</template>
<script lang="ts">
function goReportPart(index: number) {
  uni.pageScrollTo({ selector: '#part-' + index, duration: 240 })
}
</script>
<style scoped>
.role-card {
  min-height: 186px;
  background:
    radial-gradient(ellipse at 24% 18%, #63457957, #21152f00 72%), linear-gradient(140deg, #2b1c38, #1d1429);
}
.chat-main {
  min-height: 415px;
  align-content: start;
}
.message-pair {
  margin: 4px 0;
}
.bubble {
  padding: 10px 13px;
  border-radius: 11px;
  white-space: pre-wrap;
}
.question {
  background: linear-gradient(140deg, #503866, #3c2a50);
  border: 1px solid #76588e85;
  justify-self: end;
  max-width: 85%;
}
.response {
  background: linear-gradient(145deg, #241930, #1a1228);
  border: 1px solid #61466d96;
}
</style>
