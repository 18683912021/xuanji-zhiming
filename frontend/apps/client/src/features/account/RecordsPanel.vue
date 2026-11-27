<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import DataTable from '../../components/DataTable.vue'
import DateField from '../../components/DateField.vue'
import SelectField from '../../components/SelectField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import {
  account,
  createShare,
  deleteJournal,
  refreshPersonal,
  storeJournal,
  favorites,
  journal,
  shares,
  toggleFavorite,
  availableProfiles,
  type JournalEntry,
  type SharedItem,
} from './state'
import { sessions, reports, roleForReading } from '../ai/state'
import { api, apiMessage, live, restoreIdentity } from '../../shared/api'
import { fetchReading, readings, refreshReadings, removeReading, updateReading } from '../divination/records'
import { cards } from '../divination/tarot'
import { isYin, isMoving, yaoLabels } from '../divination/liuyao'
import { events } from '../calendar/events'
import { confirmAction, destination, go, toast, urlFor, type Query } from '../../shared/navigation'
import { dateKey, displayDate, makeId, parseDate } from '../../shared/storage'

const props = defineProps<{ view: string; query: Query }>()
const search = ref('')
const selectedKind = ref('全部')
const savedOnly = ref(false)
const record = computed(() => readings.state.value.find((item) => item.id === props.query.id))
const report = computed(() => reports.state.value.find((item) => item.id === props.query.report))
const note = ref(record.value?.note || '')
const noteStatus = ref('')
const actionPending = ref(false)
watch(() => record.value?.id, () => { note.value = record.value?.note || '' })
const favoriteId = computed(() => 'reading-' + (record.value?.id || ''))
const isFavorite = computed(() => favorites.state.value.some((item) => item.id === favoriteId.value))
const recordOptions = computed(() => ['全部', ...new Set(readings.state.value.map((item) => item.kind))])
const labels: Record<string, string> = {
  tarot: '塔罗',
  daily: '日签',
  bazi: '八字',
  liuyao: '六爻',
  oracle: '问签',
  dream: '梦境',
  dice: '星骰',
  book: '答案之书',
  mbti: 'MBTI',
  ziwei: '紫微',
  astro: '星盘',
}
const matching = computed(() =>
  readings.state.value.filter(
    (item) =>
      (!savedOnly.value || item.saved) &&
      (selectedKind.value === '全部' || selectedKind.value === item.kind) &&
      (item.title + item.topic + item.date).includes(search.value.trim()),
  ),
)
const associated = computed(() =>
  sessions.state.value.filter((item) => item.context?.id === record.value?.id),
)
const recordReports = computed(() =>
  reports.state.value.filter((item) => item.source?.id === record.value?.id),
)
const currentEntry = computed(
  () =>
    journal.state.value.find((item) => item.id === props.query.id) ||
    (!props.query.id && !props.query.source
      ? journal.state.value.find((item) => item.date === props.query.date)
      : undefined),
)
const journalTitle = ref(currentEntry.value ? currentEntry.value.title : '')
const journalContent = ref(currentEntry.value ? currentEntry.value.content : '')
const journalDate = ref(currentEntry.value ? currentEntry.value.date : props.query.date || dateKey())
const linkedRecord = computed(() =>
  readings.state.value.find(
    (item) => item.id === (props.query.source || (currentEntry.value && currentEntry.value.sourceId)),
  ),
)
const currentEvent = events.state.value.find((item) => item.id === props.query.id)
const eventTitle = ref(currentEvent?.title || '')
const eventDate = ref(currentEvent?.date || props.query.date || dateKey())
const repeat = ref(currentEvent?.repeat || '单次')
const reminder = ref(currentEvent?.reminder || false)
const birthday = ref(currentEvent?.birthday || false)
const profileId = ref('')
const isEvent = computed(() => props.query.kind === 'event')
const ownedShare = computed(() => shares.state.value.find((item) => item.id === props.query.id))
const fetchedShare = ref<SharedItem>()
const shareError = ref('')
const shareTarget = computed(() => fetchedShare.value || ownedShare.value)

interface ApiShare { id: string; title: string; summary: string; created_at: string; expires_at: string }
function fromShare(value: ApiShare): SharedItem {
  return { id: value.id, title: value.title, summary: value.summary, createdAt: value.created_at, expiresAt: value.expires_at, online: true }
}

onMounted(async () => {
  if (!live) return
  await restoreIdentity()
  if (props.view === 'share' && props.query.id && /^[a-f0-9-]{36}$/i.test(props.query.id)) {
    try {
      fetchedShare.value = fromShare(await api<ApiShare>('/shares/' + props.query.id))
    } catch (cause) {
      shareError.value = apiMessage(cause)
    }
  } else if (props.query.id && (props.view === 'result' || props.view === 'share-preview')) {
    await fetchReading(props.query.id).catch((cause) => { noteStatus.value = apiMessage(cause) })
  } else if (props.view === 'records') {
    void refreshReadings().catch((cause) => { noteStatus.value = apiMessage(cause) })
  } else if (props.view.startsWith('journal')) {
    await refreshPersonal()
    if (currentEntry.value && !journalContent.value) {
      journalTitle.value = currentEntry.value.title
      journalContent.value = currentEntry.value.content
      journalDate.value = currentEntry.value.date
    }
  }
})
const shareTitle = computed(
  () => report.value?.title || (isEvent.value ? '生日祝福' : record.value?.title?.split(' · ')[0]) || '',
)
const canShare = computed(() => Boolean(report.value || record.value || (isEvent.value && currentEvent)))
const shareSummary = computed(() =>
  isEvent.value
    ? '愿新的日子有值得期待的发现。'
    : report.value
      ? '一份' + report.value.category + '主题报告，共 ' + report.value.sections.length + ' 个章节。'
      : record.value?.cards
        ? record.value.cards
            .map((card) => cards[card.index]?.[0])
            .filter(Boolean)
            .join('、')
        : record.value?.lines
          ? record.value.summary
          : record.value?.kind === 'oracle' ? record.value.summary : '本次完成了' + shareTitle.value + '体验。',
)
function options(values: string[]) {
  return values.map((value) => ({ value, label: value }))
}

function promptLogin(view: string) {
  go(destination('login', undefined, { nextView: view, id: props.query.id, source: props.query.source }))
}
async function saveReading() {
  if (!record.value || actionPending.value) return
  if (record.value.online && !account.state.value) return promptLogin('result')
  actionPending.value = true
  try {
    await updateReading(record.value.id, { saved: true })
    toast('结果已保存。')
  } catch (cause) {
    toast(apiMessage(cause))
  } finally {
    actionPending.value = false
  }
}
async function saveNote() {
  if (!record.value || actionPending.value) return
  if (record.value.online && !account.state.value) return promptLogin('result')
  actionPending.value = true
  try {
    await updateReading(record.value.id, { note: note.value.trim(), saved: true })
    noteStatus.value = '笔记已保存。'
  } catch (cause) {
    noteStatus.value = apiMessage(cause)
  } finally {
    actionPending.value = false
  }
}
function favoriteReading() {
  if (record.value)
    toggleFavorite({
      id: favoriteId.value,
      title: record.value.title,
      to: destination('account', 'result', { id: record.value.id }),
    })
}
function deleteReading() {
  const id = record.value?.id
  if (!id) return
  confirmAction('删除体验', '删除当前结果及笔记。', async () => {
    try {
      if (await removeReading(id)) go(destination('account', 'records'), 'replace')
    } catch (cause) {
      toast(apiMessage(cause))
    }
  })
}
async function saveJournal() {
  if (!journalContent.value.trim() || actionPending.value) return
  if (live && !account.state.value) return promptLogin('journal-edit')
  const entry: JournalEntry = {
    id: currentEntry.value?.id || makeId(),
    title: journalTitle.value.trim() || journalContent.value.trim().slice(0, 18),
    content: journalContent.value.trim(),
    updated: dateKey(),
    date: live && currentEntry.value ? currentEntry.value.date : journalDate.value,
    sourceId: linkedRecord.value?.id,
  }
  actionPending.value = true
  try {
    const saved = await storeJournal(entry, Boolean(linkedRecord.value?.online))
    go(destination('account', 'journal-entry', { id: saved.id }), 'replace')
  } catch (cause) {
    toast(apiMessage(cause))
  } finally {
    actionPending.value = false
  }
}
function removeJournal() {
  const entry = currentEntry.value
  if (!entry) return
  confirmAction('删除日记', '删除这条私人日记。', async () => {
    try {
      await deleteJournal(entry)
      go(destination('account', 'journal'), 'replace')
    } catch (cause) {
      toast(apiMessage(cause))
    }
  })
}
function fromBirth(id: string) {
  const selected = availableProfiles.value.find((item) => item.id === id)
  if (!selected) return
  birthday.value = true
  repeat.value = '每年'
  eventTitle.value = selected.name + '的生日'
  const today = dateKey()
  const thisYear = today.slice(0, 4) + selected.date.slice(4)
  eventDate.value =
    thisYear < today ? String(Number(today.slice(0, 4)) + 1) + selected.date.slice(4) : thisYear
  if (dateKey(parseDate(eventDate.value)) !== eventDate.value)
    eventDate.value = eventDate.value.slice(0, 8) + '28'
}
function saveEvent() {
  if (!eventTitle.value.trim()) return
  const item = {
    id: currentEvent?.id || makeId(),
    title: eventTitle.value.trim(),
    date: eventDate.value,
    repeat: repeat.value,
    reminder: reminder.value,
    birthday: birthday.value,
  }
  if (events.write([item, ...events.state.value.filter((event) => event.id !== item.id)]))
    go(destination('account', 'events'), 'replace')
}
function removeEvent() {
  if (!currentEvent) return
  confirmAction('删除日期', '从本机日历移除这个事件。', () => {
    if (events.write(events.state.value.filter((item) => item.id !== currentEvent.id)))
      go(destination('account', 'events'), 'replace')
  })
}
function daysUntil(date: string) {
  return Math.round((parseDate(date).getTime() - parseDate(dateKey()).getTime()) / 86400000)
}
async function publishShare() {
  if (!canShare.value || actionPending.value) return
  if (record.value?.online && !account.state.value) return promptLogin('share-preview')
  actionPending.value = true
  try {
    let id
    if (record.value?.online) {
      const item = fromShare(await api<ApiShare>('/shares', { method: 'POST', body: { reading_id: record.value.id } }))
      shares.write([item, ...shares.state.value])
      id = item.id
    } else id = createShare(shareTitle.value, shareSummary.value)
    if (id) go(destination('account', 'share', { id }))
  } catch (cause) {
    toast(apiMessage(cause))
  } finally {
    actionPending.value = false
  }
}
function revokeShare() {
  const item = ownedShare.value
  if (!item) return
  confirmAction('撤回分享', '撤回后，原链接失效。', async () => {
    try {
      if (item.online) await api('/shares/' + item.id, { method: 'DELETE' })
      shares.write(shares.state.value.filter((value) => value.id !== item.id))
      fetchedShare.value = undefined
      shareError.value = '分享已撤回。'
    } catch (cause) {
      toast(apiMessage(cause))
    }
  })
}
function copyShare() {
  if (!shareTarget.value) return
  const path = urlFor(destination('account', 'share', { id: shareTarget.value.id }))
  let value = path
  // #ifdef H5
  value = window.location.origin + window.location.pathname + '#' + path
  // #endif
  uni.setClipboardData({ data: value })
}
</script>

<template>
  <view class="content-width stack">
    <template v-if="view === 'records'">
      <view class="panel stack"
        ><input v-model="search" class="field" placeholder="搜索类型、问题或日期" />
        <view class="chips"
          ><button
            v-for="kind in recordOptions"
            :key="kind"
            class="chip"
            :class="{ selected: selectedKind === kind }"
            @tap="selectedKind = kind"
          >
            {{ labels[kind] || kind }}
          </button>
          <button class="chip" :class="{ selected: savedOnly }" @tap="savedOnly = !savedOnly">
            仅已保存
          </button></view
        >
      </view>
      <view class="panel"
        ><NavLink
          v-for="item in matching"
          :key="item.id"
          class="row-link"
          :to="destination('account', 'result', { id: item.id })"
        >
          <view
            ><text class="block">{{ item.title }}</text
            ><text class="muted small"
              >{{ displayDate(item.date) }} · {{ item.saved ? '已保存' : '最近体验' }}</text
            ></view
          ><text class="gold">›</text> </NavLink
        ><text v-if="!matching.length" class="muted">暂无符合条件的记录。</text></view
      >
    </template>
    <template v-else-if="view === 'result'">
      <view v-if="record" class="split">
        <view class="panel stack">
          <text class="panel-head">{{ record.title }}</text
          ><text class="muted small">{{ displayDate(record.date) }} · {{ record.version }}</text>
          <text class="gold">{{ record.summary }}</text
          ><text v-if="record.topic" class="notice">{{ record.topic }}</text>
          <view v-if="record.cards" class="cols-3">
            <NavLink
              v-for="card in record.cards"
              :key="card.position"
              class="result-card"
              :to="destination('divination', 'card', { id: String(card.index) })"
            >
              <AppIcon name="tarot" class="reading-card-art" /><text class="block">{{
                cards[card.index]?.[0]
              }}</text
              ><text class="muted small">{{ card.position }} · {{ card.reversed ? '逆位' : '正位' }}</text>
            </NavLink>
          </view>
          <view v-if="record.lines" class="hexagram"
            ><view v-for="(line, index) in [...record.lines].reverse()" :key="index" class="line-wrap">
              <view class="yao-line" :class="{ yin: isYin(line) }"></view
              ><text class="muted small">{{ yaoLabels[line] }}{{ isMoving(line) ? ' · 动' : '' }}</text>
            </view></view
          >
          <DataTable
            v-if="record.bazi"
            :headings="['四柱', '干支', '五行', '藏干', '十神', '纳音', '空亡', '地势']"
            :rows="
              record.bazi.pillars.map((item) => [
                item.label,
                item.text,
                item.elements,
                item.hidden,
                item.deity || '—',
                item.sound || '—',
                item.void || '—',
                item.stage || '—',
              ])
            "
          />
          <view v-for="part in record.sections" :key="part.title" class="stack"
            ><text class="panel-head">{{ part.title }}</text
            ><text>{{ part.content }}</text></view
          >
          <view class="actions">
            <button class="btn primary" :disabled="record.saved" @tap="saveReading">
              {{ record.saved ? '已保存' : '保存结果' }}
            </button>
            <button class="btn" @tap="favoriteReading">{{ isFavorite ? '取消收藏' : '收藏结果' }}</button>
            <NavLink
              class="btn"
              :to="destination('ai', 'new', { source: record.id, role: roleForReading(record.kind) })"
              >向 AI 追问</NavLink
            >
            <NavLink class="btn" :to="destination('ai', 'reports', { source: record.id })">生成报告</NavLink>
            <NavLink v-if="record.source" class="btn" :to="record.source">返回工具</NavLink>
            <NavLink class="btn" :to="destination('account', 'share-preview', { id: record.id })"
              >分享预览</NavLink
            >
          </view>
        </view>
        <view class="panel stack">
          <text class="panel-head">私人笔记</text
          ><textarea v-model="note" class="field area" maxlength="1000" placeholder="回看时想记住什么？" />
          <text v-if="noteStatus" class="gold small">{{ noteStatus }}</text>
          <view class="actions"
            ><button class="btn primary" @tap="saveNote">保存笔记</button
            ><NavLink class="btn" :to="destination('account', 'journal-edit', { source: record.id })"
              >关联日记</NavLink
            ></view
          >
          <SectionHeading title="关联会话与报告" />
          <NavLink
            v-for="item in associated"
            :key="item.id"
            class="row-link"
            :to="destination('ai', 'chat', { id: item.id })"
            ><text>{{ item.title }}</text
            ><text class="gold">对话 ›</text></NavLink
          >
          <NavLink
            v-for="item in recordReports"
            :key="item.id"
            class="row-link"
            :to="destination('ai', 'report', { id: item.id })"
            ><text>{{ item.title }}</text
            ><text class="gold">报告 ›</text></NavLink
          >
          <text v-if="!associated.length && !recordReports.length" class="muted small"
            >本次体验还没有报告或会话。</text
          >
          <button class="link" @tap="deleteReading">删除本次体验</button>
        </view>
      </view>
      <text v-else class="panel muted">这份体验已删除，或当前设备没有这份结果。</text>
    </template>
    <template v-else-if="view === 'favorites'">
      <view class="panel stack"
        ><text v-if="!favorites.state.value.length" class="muted">你还没有收藏。</text>
        <view v-for="item in favorites.state.value" :key="item.id" class="row"
          ><NavLink :to="item.to">{{ item.title }} ›</NavLink
          ><button class="link" @tap="toggleFavorite(item)">取消收藏</button></view
        >
      </view>
    </template>
    <template v-else-if="view === 'journal'">
      <view class="actions"
        ><NavLink class="btn primary" :to="destination('account', 'journal-edit', { date: dateKey() })"
          >写今天的日记</NavLink
        ></view
      >
      <input v-model="search" class="field" placeholder="搜索日记标题或日期" />
      <view class="panel stack"
        ><NavLink
          v-for="item in journal.state.value.filter((item) =>
            (item.title + item.date + item.content).includes(search.trim()),
          )"
          :key="item.id"
          class="row-link"
          :to="destination('account', 'journal-entry', { id: item.id })"
        >
          <text>{{ item.title }}</text
          ><text class="muted">{{ item.date }} ›</text></NavLink
        >
        <text v-if="!journal.state.value.length" class="muted">还没有写下任何日记。日记默认私有。</text>
      </view>
    </template>
    <template v-else-if="view === 'journal-entry'">
      <view v-if="currentEntry" class="panel stack">
        <text class="panel-head">{{ currentEntry.title }}</text
        ><text class="muted">{{ currentEntry.date }} · 私人记录</text
        ><text class="journal-body">{{ currentEntry.content }}</text>
        <NavLink
          v-if="linkedRecord"
          class="link"
          :to="destination('account', 'result', { id: linkedRecord.id })"
          >关联体验 · {{ linkedRecord.title }} ›</NavLink
        >
        <view class="actions"
          ><NavLink class="btn primary" :to="destination('account', 'journal-edit', { id: currentEntry.id })"
            >编辑日记</NavLink
          ><button class="btn" @tap="removeJournal">删除</button></view
        >
      </view>
      <text v-else class="panel muted">这条日记已不存在。</text>
    </template>
    <template v-else-if="view === 'journal-edit'">
      <view class="panel stack">
        <text v-if="live && currentEntry" class="muted">{{ displayDate(currentEntry.date) }}</text><DateField v-else v-model="journalDate" label="日期" /><view
          ><text class="field-label">标题</text
          ><input v-model="journalTitle" class="field" maxlength="40" placeholder="给记录起个名字"
        /></view>
        <view
          ><text class="field-label">日记正文</text
          ><textarea
            v-model="journalContent"
            class="field area"
            maxlength="1800"
            placeholder="今天，你观察到了什么？"
          />
        </view>
        <text v-if="linkedRecord" class="notice">关联体验 · {{ linkedRecord.title }}</text>
        <button class="btn primary" :disabled="!journalContent.trim()" @tap="saveJournal">保存日记</button>
      </view>
    </template>
    <template v-else-if="view === 'events'">
      <view class="actions"
        ><NavLink class="btn primary" :to="destination('account', 'event-edit')">添加特别日期</NavLink
        ><NavLink class="btn" :to="destination('today', 'calendar')">星象日历</NavLink></view
      >
      <view class="panel stack">
        <NavLink
          v-for="item in events.state.value"
          :key="item.id"
          class="row-link"
          :to="destination('account', 'event-edit', { id: item.id })"
          ><view
            ><text class="block">{{ item.title }}</text
            ><text class="muted small">{{ item.date }} · {{ item.repeat }}</text></view
          >
          <text class="gold">{{
            daysUntil(item.date) === 0
              ? '今天'
              : daysUntil(item.date) > 0
                ? '还有 ' + daysUntil(item.date) + ' 天'
                : '已过去 ' + Math.abs(daysUntil(item.date)) + ' 天'
          }}</text></NavLink
        >
        <text v-if="!events.state.value.length" class="muted"
          >还没有事件，可以从手动日期或出生档案建立。</text
        >
      </view>
    </template>
    <template v-else-if="view === 'event-edit'">
      <view class="panel stack">
        <SelectField
          v-model="profileId"
          label="从档案添加生日"
          :options="availableProfiles.map((item) => ({ value: item.id, label: item.name }))"
          @update:model-value="fromBirth"
        />
        <view
          ><text class="field-label">事件名称</text
          ><input v-model="eventTitle" class="field" maxlength="44" placeholder="例如第一次观星"
        /></view>
        <DateField v-model="eventDate" label="目标日期" /><SelectField
          v-model="repeat"
          label="重复方式"
          :options="options(['单次', '每周', '每月', '每年'])"
        />
        <view class="switch-row"
          ><text>生日事件</text><AppSwitch label="生日事件" :checked="birthday" @change="birthday = $event"
        /></view>
        <view class="switch-row"
          ><text>记录提醒意愿（Mock）</text
          ><AppSwitch label="记录提醒意愿（Mock）" :checked="reminder" @change="reminder = $event"
        /></view>
        <view class="actions"
          ><button class="btn primary" :disabled="!eventTitle.trim()" @tap="saveEvent">保存事件</button>
          <NavLink
            v-if="currentEvent?.birthday"
            class="btn"
            :to="destination('account', 'share-preview', { id: currentEvent.id, kind: 'event' })"
            >预览生日祝福</NavLink
          >
          <button v-if="currentEvent" class="btn" @tap="removeEvent">删除事件</button></view
        >
      </view>
    </template>
    <template v-else-if="view === 'share-preview'">
      <view v-if="canShare" class="panel stack">
        <text class="panel-head gold">{{ shareTitle }}</text
        ><text>{{ shareSummary }}</text>
        <text class="notice">仅分享上面的摘要。出生资料、原问题、照片和会话都不会进入分享。</text>
        <button class="btn primary" @tap="publishShare">{{ record?.online ? '确认并生成分享链接' : '生成本机预览' }}</button>
        <NavLink class="link" :to="destination('account', 'shares')">管理已有分享 ›</NavLink> </view
      ><text v-else class="panel muted">找不到用于分享的资料。</text>
    </template>
    <template v-else-if="view === 'shares'">
      <view class="panel stack"
        ><text v-if="!shares.state.value.length" class="muted">暂无分享记录。</text>
        <NavLink
          v-for="item in shares.state.value"
          :key="item.id"
          class="row-link"
          :to="destination('account', 'share', { id: item.id })"
          >{{ item.title }} · {{ item.createdAt }} ›</NavLink
        >
      </view>
    </template>
    <template v-else-if="view === 'share'">
      <view v-if="shareTarget" class="panel stack"
        ><text class="panel-head gold">{{ shareTarget.title }}</text
        ><text>{{ shareTarget.summary }}</text>
        <text class="muted small">{{ shareTarget.online ? '分享有效至 ' + displayDate(shareTarget.expiresAt || '') : '本机分享预览' }}</text>
        <view class="actions"
          ><button v-if="shareTarget.online" class="btn primary" @tap="copyShare">复制分享入口</button>
          <button v-if="ownedShare" class="btn" @tap="revokeShare">撤回分享</button></view
        >
      </view>
      <view v-else class="panel stack"
        ><text class="muted">{{ shareError || '这份摘要当前不可用。' }}</text
        ><NavLink class="btn" :to="destination('home')">回到首页</NavLink></view
      >
    </template>
  </view>
</template>
<style scoped>
.result-card {
  border: 1px solid #8d7154;
  border-radius: 8px;
  text-align: center;
  background: linear-gradient(160deg, #392747, #1c1429);
  padding: 8px 5px;
}
.card-glyph {
  display: block;
  color: var(--gold);
  font-size: 26px;
}
.hexagram {
  display: grid;
  gap: 6px;
  width: 220px;
  max-width: 100%;
  margin: 0 auto;
}
.line-wrap {
  display: grid;
  grid-template-columns: 1fr 76px;
  gap: 15px;
  align-items: center;
}
.yao-line {
  height: 6px;
  background: #d6b66c;
  border-radius: 3px;
}
.yao-line.yin {
  background: linear-gradient(to right, #d6b66c 44%, transparent 44%, transparent 56%, #d6b66c 56%);
}
.journal-body {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
