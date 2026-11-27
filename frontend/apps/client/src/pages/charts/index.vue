<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { Solar } from 'lunar-typescript'
import AppShell from '../../components/AppShell.vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import DateField from '../../components/DateField.vue'
import SelectField from '../../components/SelectField.vue'
import DataTable from '../../components/DataTable.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import ChartWheel from '../../features/charts/ChartWheel.vue'
import { apiMessage, live, requestId, restoreIdentity } from '../../shared/api'
import { birthInput, clockOccurrences, timezones } from '../../features/account/birth'
import { birthCities, astroDisplay } from '../../features/charts/astro'
import { availableProfiles, refreshPersonal, type BirthProfile } from '../../features/account/state'
import { birthdaySign, compatibility } from '../../features/catalog/zodiac'
import { calculateBazi, type BaziReading, type Calendar } from '../../features/charts/bazi'
import {
  astroTypes,
  astrologyKnowledge,
  baseSettings,
  chartFixture,
  cycleTypes,
  fixtureSeed,
  mansions,
  synastryTypes,
  ziweiFixture,
} from '../../features/charts/fixtures'
import { createReading, performReading, readings, removeReading, type Reading, type ReadingSection } from '../../features/divination/records'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, localStore, offsetDate, parseDate } from '../../shared/storage'

const titles: Record<string, string> = {
  bazi: '八字命盘',
  cycles: '八字流盘',
  ziwei: '紫微斗数',
  mansion: '二十八星宿',
  'match-bazi': '八字合盘',
  astro: '西洋星盘',
  'match-astro': '西洋合盘',
  match: '缘分合盘',
  history: '缘分合盘历史',
  knowledge: '星盘知识',
  settings: '排盘设置',
}
const query = ref<Query>({})
const view = computed(() => (query.value.view && Object.prototype.hasOwnProperty.call(titles, query.value.view) ? query.value.view : 'bazi'))
const settings = localStore('chart-settings', { ...baseSettings })
const edits = ref({ ...settings.state.value })
const profileOptions = computed(() =>
  availableProfiles.value.map((item) => ({ value: item.id, label: item.name + ' · ' + item.relation })),
)
const first = ref(availableProfiles.value[0]!.id)
const second = ref(availableProfiles.value[1]!.id)
const firstProfile = computed(
  () => availableProfiles.value.find((item) => item.id === first.value) || availableProfiles.value[0]!,
)
const secondProfile = computed(
  () => availableProfiles.value.find((item) => item.id === second.value) || availableProfiles.value[1]!,
)
const isPair = computed(() => ['match', 'match-bazi', 'match-astro'].includes(view.value))
const astro = computed(() => ['astro', 'match-astro'].includes(view.value))
const chartType = ref(astroTypes[0]!)
const timePoint = ref(dateKey())
const schedule = ref('流年')
const known = ref('')
const compared = ref(false)
const dual = ref(false)
const chart = ref<BaziReading>()
const error = ref('')
const calendar = ref<Calendar>('solar')
const birth = ref('')
const lunarYear = ref('')
const lunarMonth = ref('')
const lunarDay = ref('')
const lunarYears = Array.from({ length: 199 }, (_, index) => ({ value: String(1901 + index), label: (1901 + index) + ' 年' }))
const lunarMonths = Array.from({ length: 12 }, (_, index) => ({ value: String(index + 1).padStart(2, '0'), label: (index + 1) + ' 月' }))
const lunarDays = Array.from({ length: 30 }, (_, index) => ({ value: String(index + 1).padStart(2, '0'), label: (index + 1) + ' 日' }))
const enteredDate = computed(() => calendar.value === 'solar' ? birth.value :
  lunarYear.value && lunarMonth.value && lunarDay.value ? [lunarYear.value, lunarMonth.value, lunarDay.value].join('-') : '')
const time = ref('')
const occurrence = ref('')
const city = ref('')
const timezone = ref('Asia/Shanghai')
const pending = ref(false)
const onlineBazi = ref<Reading>()
const onlineNatal = ref<Reading>()
const realNatal = computed(() => live && view.value === 'astro' && chartType.value === '本命盘')
const longitude = ref('')
const latitude = ref('')
let previous: { data: string; key: string } | undefined

async function runReading(kind: 'bazi' | 'astro', payload: object) {
  if (pending.value) return
  const data = JSON.stringify([kind, payload])
  if (previous?.data !== data) previous = { data, key: requestId() }
  pending.value = true
  error.value = ''
  try {
    return await performReading(kind, payload, previous.key)
  } catch (cause) {
    error.value = apiMessage(cause)
  } finally {
    pending.value = false
  }
}
const timeUnknown = ref(false)
const leap = ref(false)
const chartSnapshot = ref('')
const place = ref('')
const mansionType = ref('值日')
const stepSize = computed(() => ({ 大运: 3650, 流年: 365, 流月: 30, 流日: 1, 流时: 0 })[schedule.value] || 1)
const hour = ref(12)

onLoad(async (value) => {
  query.value = value || {}
  if (live && query.value.id) { await restoreIdentity(); await refreshPersonal() }
  if (query.value.id && availableProfiles.value.some((item) => item.id === query.value.id))
    first.value = query.value.id
  if (query.value.second && availableProfiles.value.some((item) => item.id === query.value.second))
    second.value = query.value.second
  if (view.value === 'match-astro') chartType.value = synastryTypes[0]!
  if (view.value === 'bazi' && query.value.id) fill(firstProfile.value)
  if (view.value === 'knowledge') known.value = query.value.topic || 'planet'
})

function fill(item: BirthProfile) {
  calendar.value = 'solar'
  birth.value = item.date
  time.value = item.time
  occurrence.value = item.occurrence || ''
  city.value = item.city
  timezone.value = item.timezone
  timeUnknown.value = !item.time
  chart.value = undefined
  onlineBazi.value = undefined
  leap.value = false
}
function calculateSource(item: BirthProfile) {
  const result = calculateBazi({
    calendar: 'solar',
    date: item.date,
    time: item.time,
    leapMonth: false,
    timeUnknown: !item.time,
    lateZi: settings.state.value.lateZi,
  })
  return result.ok ? result.reading : undefined
}
async function calculate() {
  error.value = ''
  if (live) {
    if (!enteredDate.value || (!timeUnknown.value && !time.value)) {
      error.value = '请填入出生日期和时间，或勾选时辰不详。'
      return
    }
    const item = await runReading('bazi', {
      birth: birthInput(enteredDate.value, timeUnknown.value ? '' : time.value, timezone.value, calendar.value, calendar.value === 'lunar' && leap.value, occurrence.value),
      late_zi: settings.state.value.lateZi,
    })
    if (item?.bazi) {
      onlineBazi.value = item
      chart.value = item.bazi
      chartSnapshot.value = item.sections[0]?.content || ''
    }
    return
  }
  const result = calculateBazi({
    calendar: calendar.value,
    date: enteredDate.value,
    time: time.value,
    leapMonth: calendar.value === 'lunar' && leap.value,
    timeUnknown: timeUnknown.value,
    lateZi: settings.state.value.lateZi,
  })
  if (!result.ok) {
    error.value = result.error
    return
  }
  chart.value = result.reading
  chartSnapshot.value = [enteredDate.value, timeUnknown.value ? '时辰不详' : time.value, timezone.value, city.value]
    .filter(Boolean)
    .join(' · ')
}
function saveBazi() {
  if (onlineBazi.value) return go(destination('account', 'result', { id: onlineBazi.value.id }))
  if (!chart.value) return
  sendReading(
    'bazi',
    '八字命盘',
    chartSnapshot.value,
    chart.value.pillars.map((item) => item.text).join(' · '),
    [
      { title: '出生资料快照', content: chartSnapshot.value },
      { title: '计算口径', content: '当地钟表时刻；晚子时设置依排盘选项。' },
    ],
    chart.value,
  )
}
function sendReading(
  kind: string,
  title: string,
  topic: string,
  summary: string,
  sections: ReadingSection[],
  bazi?: BaziReading,
) {
  const created = createReading(
    {
      kind,
      title,
      topic,
      summary,
      sections,
      bazi,
      source: destination('charts', view.value, { id: first.value }),
    },
    true,
  )
  if (created) go(destination('account', 'result', { id: created.id }))
}

const dataTable = computed(() =>
  chart.value
    ? [
        ['干支', ...chart.value.pillars.map((item) => item.text)],
        ['五行', ...chart.value.pillars.map((item) => item.elements)],
        ['藏干', ...chart.value.pillars.map((item) => item.hidden)],
        ...(['deity', 'sound', 'void', 'stage'] as const).map((field, index) => [
          ['十神', '纳音', '空亡', '地势'][index]!,
          ...chart.value!.pillars.map((item) => item[field] || '—'),
        ]),
      ]
    : [],
)
const seed = computed(() =>
  fixtureSeed(
    [
      firstProfile.value.date,
      firstProfile.value.time,
      chartType.value,
      timePoint.value,
      place.value,
      settings.state.value.house,
      settings.state.value.zodiac,
    ].join('|'),
  ),
)
const natal = computed(() => realNatal.value ? onlineNatal.value?.natal : undefined)
const astroData = computed(() => natal.value
  ? astroDisplay(natal.value) : chartFixture(seed.value, settings.state.value.extras))

watch([firstProfile, realNatal], () => {
  onlineNatal.value = undefined
  if (!realNatal.value) return
  const knownCity = birthCities[firstProfile.value.city.replace(/市$/, '').trim()]
  longitude.value = knownCity ? String(knownCity[0]) : ''
  latitude.value = knownCity ? String(knownCity[1]) : ''
}, { immediate: true })

async function calculateNatal() {
  const person = firstProfile.value
  if (!person.time) { error.value = '本命盘需要准确的出生时刻，请先补充档案。'; return }
  if (!longitude.value.trim() || !latitude.value.trim()
    || !Number.isFinite(Number(longitude.value)) || !Number.isFinite(Number(latitude.value))) {
    error.value = '请输入出生地经纬度。'
    return
  }
  const orb = Number(settings.state.value.orb)
  if (orb < 1 || orb > 10 || !Number.isFinite(orb)) {
    error.value = '请在排盘设置中把相位容许度调整为 1–10°。'
    return
  }
  const house = { 普拉西德: 'placidus', 整宫制: 'whole_sign', 等宫制: 'equal' }[settings.state.value.house] || 'placidus'
  const input = {
    birth: birthInput(person.date, person.time, person.timezone, 'solar', false, person.occurrence),
    longitude: Number(longitude.value), latitude: Number(latitude.value), house_system: house,
    zodiac: settings.state.value.zodiac === '恒星黄道' ? 'sidereal' : 'tropical',
    extras: settings.state.value.extras, orb,
  }
  const item = await runReading('astro', input)
  if (item && realNatal.value && firstProfile.value.id === person.id) onlineNatal.value = item
}
const secondData = computed(() =>
  chartFixture(fixtureSeed(secondProfile.value.date + chartType.value), settings.state.value.extras),
)
const ziwei = computed(() =>
  ziweiFixture(fixtureSeed(firstProfile.value.date + schedule.value + timePoint.value)),
)
const compatibilityData = computed(() =>
  compatibility(birthdaySign(firstProfile.value.date), birthdaySign(secondProfile.value.date)),
)
const firstBazi = computed(() => calculateSource(firstProfile.value))
const secondBazi = computed(() => calculateSource(secondProfile.value))
const man = computed(() =>
  Solar.fromDate(
    parseDate(mansionType.value === '值日' ? timePoint.value : firstProfile.value.date),
  ).getLunar(),
)
const mansionName = computed(() => man.value.getXiu())
const secondMansion = computed(() => Solar.fromDate(parseDate(secondProfile.value.date)).getLunar().getXiu())
const matchHistory = computed(() => readings.state.value.filter((item) => item.kind.startsWith('match')))
const useText = computed(() => settings.state.value.text)

function advance(amount: number) {
  const date = view.value === 'cycles' || view.value === 'ziwei' ? amount * stepSize.value : amount
  if (schedule.value === '流时' && (view.value === 'cycles' || view.value === 'ziwei')) {
    const next = hour.value + amount
    hour.value = (next + 24) % 24
    if (next < 0 || next > 23) timePoint.value = offsetDate(timePoint.value, amount)
  } else {
    timePoint.value = offsetDate(timePoint.value, date)
  }
}
function compare() {
  if (first.value === second.value) return toast('请分别选择两个档案。')
  compared.value = true
}
function saveChart() {
  if (realNatal.value) {
    if (onlineNatal.value) go(destination('account', 'result', { id: onlineNatal.value.id }))
    return
  }
  if (isPair.value && !compared.value) return
  const topic = isPair.value
    ? firstProfile.value.name + ' × ' + secondProfile.value.name
    : firstProfile.value.name
  if (astro.value) {
    return sendReading(
      view.value,
      titles[view.value]!,
      topic,
      chartType.value + ' · ' + timePoint.value,
      astroData.value.slice(0, 5).map((item) => ({
        title: item.planet,
        content: item.sign.name + ' ' + (item.degree % 30) + '° · 第' + item.house + '宫 · ' + item.aspect,
      })),
    )
  }
  if (view.value === 'ziwei')
    return sendReading(
      'ziwei',
      '紫微斗数',
      topic,
      schedule.value + ' · ' + timePoint.value,
      ziwei.value.map((item) => ({
        title: item.label,
        content: item.star + ' · ' + item.transformation + ' · ' + item.period,
      })),
    )
  const pair = compatibilityData.value
  sendReading(view.value, titles[view.value]!, topic, '互动参考 ' + pair.score + ' 分', [
    {
      title: '相处主题',
      content:
        birthdaySign(firstProfile.value.date).relationship +
        ' ' +
        birthdaySign(secondProfile.value.date).relationship,
    },
    { title: '星宿观察', content: mansionName.value + '宿 × ' + secondMansion.value + '宿' },
    { title: '口径', content: '关系指数为 Mock 示例指标。双方出生数据保留在档案页。' },
  ])
}
function saveSettings() {
  const orb = Number(edits.value.orb)
  const [min, max] = live ? [1, 10] : [0, 20]
  if (!edits.value.orb.trim() || !Number.isFinite(orb) || orb < min || orb > max) {
    return toast('容许度请填 ' + min + '–' + max + '°。')
  }
  if (settings.write({ ...edits.value })) toast('排盘设置已保存。')
}

function jumpToToday() {
  timePoint.value = dateKey()
  hour.value = 12
}
</script>

<template>
  <AppShell section="charts" :title="titles[view]" detail>
    <view class="content-width stack">
      <template v-if="view === 'settings'">
        <view class="panel stack">
          <text class="panel-head">星盘显示与排盘口径</text>
          <view class="cols-2"
            ><SelectField
              v-model="edits.preset"
              label="预设"
              :options="['现代', '古典'].map((value) => ({ value, label: value }))"
            />
            <SelectField
              v-model="edits.zodiac"
              label="黄道制"
              :options="['回归黄道', '恒星黄道'].map((value) => ({ value, label: value }))"
            />
            <SelectField
              v-model="edits.house"
              label="宫位制"
              :options="['普拉西德', '整宫制', '等宫制'].map((value) => ({ value, label: value }))"
            />
            <view
              ><text class="field-label">相位容许度（°）</text
              ><input v-model="edits.orb" class="field" type="digit"
            /></view>
          </view>
          <view class="switch-row"
            ><text>显示小行星与虚点</text
            ><AppSwitch label="显示小行星与虚点" :checked="edits.extras" @change="edits.extras = $event"
          /></view>
          <view class="switch-row"
            ><text>显示相位文字</text
            ><AppSwitch label="显示相位文字" :checked="edits.text" @change="edits.text = $event"
          /></view>
          <view class="switch-row"
            ><text>晚子时按次日换日</text
            ><AppSwitch label="晚子时按次日换日" :checked="edits.lateZi" @change="edits.lateZi = $event"
          /></view>
          <view v-if="!live" class="switch-row"
            ><text>真太阳时参数预览</text
            ><AppSwitch label="真太阳时参数预览" :checked="edits.solar" @change="edits.solar = $event"
          /></view>
          <text class="notice">八字基础盘使用当地钟表时间。</text>
          <view class="actions"
            ><button class="btn primary" @tap="saveSettings">保存设置</button
            ><button class="btn" @tap="edits = { ...baseSettings }">恢复默认</button></view
          >
        </view>
      </template>
      <template v-else-if="view === 'knowledge'">
        <view class="workspace"
          ><view class="panel stack">
            <button
              v-for="item in astrologyKnowledge"
              :key="item.id"
              class="btn"
              :class="{ primary: known === item.id }"
              @tap="known = item.id"
            >
              {{ item.title }}
            </button> </view
          ><view
            v-for="item in astrologyKnowledge.filter((item) => item.id === known)"
            :key="item.id"
            class="panel stack"
          >
            <text class="panel-head">{{ item.title }}</text
            ><text>{{ item.body }}</text>
            <view class="actions"
              ><NavLink class="btn" :to="destination('charts', 'astro')">打开本命盘</NavLink
              ><NavLink class="btn" :to="destination('ai', 'new', { role: 'astrologer' })"
                >询问 AI 占星师</NavLink
              ></view
            >
          </view></view
        >
      </template>
      <template v-else-if="view === 'history'">
        <view class="panel stack">
          <view v-for="item in matchHistory" :key="item.id" class="row">
            <NavLink class="link" :to="destination('account', 'result', { id: item.id })"
              >{{ item.title }} · {{ item.topic }}</NavLink
            >
            <button
              class="link"
              @tap="
                confirmAction('删除合盘', '删除这条本机合盘记录。', () =>
                  removeReading(item.id).catch((cause) => toast(apiMessage(cause))),
                )
              "
            >
              删除
            </button>
          </view>
          <text v-if="!matchHistory.length" class="muted">还没有保存合盘。</text>
        </view>
      </template>
      <template v-else-if="view === 'bazi'">
        <view class="workspace">
          <view class="panel stack">
            <SectionHeading title="出生资料" :to="destination('account', 'profiles')" action="出生档案" />
            <SelectField
              v-model="first"
              label="选择出生档案"
              :options="profileOptions"
              @update:model-value="fill(firstProfile)"
            />
            <button class="link" @tap="fill(availableProfiles[0]!)">填入示例</button>
            <view class="chips"
              ><button class="chip" :class="{ selected: calendar === 'solar' }" @tap="calendar = 'solar'">
                公历</button
              ><button class="chip" :class="{ selected: calendar === 'lunar' }" @tap="calendar = 'lunar'">
                农历
              </button></view
            >
            <DateField v-if="calendar === 'solar'" v-model="birth" label="公历出生日期" start="1901-01-01" />
            <view v-else class="cols-3">
              <SelectField v-model="lunarYear" label="农历年" :options="lunarYears" />
              <SelectField v-model="lunarMonth" label="农历月" :options="lunarMonths" />
              <SelectField v-model="lunarDay" label="农历日" :options="lunarDays" />
            </view>
            <view v-if="calendar === 'lunar'" class="switch-row"
              ><text>闰月</text><AppSwitch label="闰月" :checked="leap" @change="leap = $event"
            /></view>
            <DateField v-if="!timeUnknown" v-model="time" label="出生时间" mode="time" />
            <view class="switch-row"
              ><text>时辰不详</text
              ><AppSwitch label="时辰不详" :checked="timeUnknown" @change="timeUnknown = $event"
            /></view>
            <view
              ><text class="field-label">出生城市</text
              ><input v-model="city" class="field" maxlength="36" placeholder="例如杭州"
            /></view>
            <SelectField
              v-model="timezone"
              label="时区"
              :options="
                timezones
              "
            />
            <SelectField v-if="live && !timeUnknown && time" v-model="occurrence"
              label="夏令时回拨（出生时刻出现两次时填写）" :options="clockOccurrences" />
            <NavLink class="link" :to="destination('charts', 'settings')">晚子时与进阶设置 ›</NavLink>
            <text v-if="error" class="error">{{ error }}</text
            ><button class="btn primary" :disabled="pending" @tap="calculate">开始排盘</button>
          </view>
          <view class="panel stack">
            <text class="panel-head">四柱与五行</text>
            <template v-if="chart">
              <text class="muted">{{ chartSnapshot }}</text
              ><text class="gold">日主 · {{ chart.pillars[2]?.text === '待确定' ? '待确定' : chart.pillars[2]?.text.slice(0, 1) }}</text>
              <DataTable :headings="['项目', ...chart.pillars.map((item) => item.label)]" :rows="dataTable" />
              <view class="actions"
                ><button class="btn primary" @tap="saveBazi">{{ onlineBazi ? '查看命盘记录' : '保存命盘' }}</button>
                <NavLink class="btn" :to="destination('charts', 'cycles', { id: first })">八字流盘</NavLink>
                <NavLink class="btn" :to="destination('charts', 'match-bazi', { id: first })"
                  >八字合盘</NavLink
                ></view
              >
            </template>
            <text v-else class="muted">填入出生资料后，查看年柱、月柱、日柱和时柱。时辰未知可先看三柱。</text>
          </view>
        </view>
      </template>
      <template v-else>
        <view class="workspace">
          <view class="panel stack">
            <SelectField
              v-model="first"
              :label="isPair ? '第一份出生档案' : '出生档案'"
              :options="profileOptions"
              @update:model-value="compared = false"
            />
            <SelectField
              v-if="isPair"
              v-model="second"
              label="第二份出生档案"
              :options="profileOptions"
              @update:model-value="compared = false"
            />
            <SelectField
              v-if="astro"
              v-model="chartType"
              label="盘型"
              :options="(isPair ? synastryTypes : astroTypes).map((value) => ({ value, label: value }))"
            />
            <SelectField
              v-if="['cycles', 'ziwei'].includes(view)"
              v-model="schedule"
              label="流盘周期"
              :options="
                (view === 'ziwei' ? ['大限', ...cycleTypes.slice(1)] : cycleTypes).map((value) => ({
                  value,
                  label: value,
                }))
              "
            />
            <SelectField
              v-if="view === 'mansion'"
              v-model="mansionType"
              label="星宿类型"
              :options="['值日', '本命', '关系'].map((value) => ({ value, label: value }))"
            />
            <SelectField
              v-if="view === 'mansion' && mansionType === '关系'"
              v-model="second"
              label="关系档案"
              :options="profileOptions"
            />
            <view v-if="chartType === '地点重置盘'"
              ><text class="field-label">重置地点</text
              ><input v-model="place" class="field" placeholder="输入城市"
            /></view>
            <DateField v-if="!realNatal && (!isPair || astro)" v-model="timePoint" label="查看日期" />
            <view v-if="!realNatal && (!isPair || astro)" class="actions"
              ><button class="btn" @tap="advance(-1)">‹ 上一段</button
              ><button class="btn" @tap="jumpToToday">回今天</button
              ><button class="btn" @tap="advance(1)">下一段 ›</button></view
            >
            <view v-if="astro && !isPair && !realNatal" class="switch-row"
              ><text>双盘对照</text><AppSwitch label="双盘对照" :checked="dual" @change="dual = $event"
            /></view>
            <button v-if="isPair" class="btn primary" @tap="compare">查看双方对照</button>
            <template v-if="realNatal">
              <view class="cols-2">
                <view><text class="field-label">出生地经度</text><input v-model="longitude" class="field" placeholder="东经为正" /></view>
                <view><text class="field-label">出生地纬度</text><input v-model="latitude" class="field" placeholder="北纬为正" /></view>
              </view>
              <text class="muted small">常见城市预填市中心坐标，可改为实际出生地点。</text>
              <text v-if="error" class="error">{{ error }}</text>
              <button class="btn primary" :disabled="pending" @tap="calculateNatal">{{ pending ? '正在排盘…' : '计算本命盘' }}</button>
            </template>
            <NavLink class="link" :to="destination('charts', 'settings')">排盘设置 ›</NavLink>
          </view>
          <view class="stack">
            <view v-if="isPair && !compared" class="panel muted">选定双方档案后，打开盘面与关系摘要。</view>
            <view v-else-if="realNatal && !natal" class="panel muted">选择出生档案并确认经纬度后，可计算星体、宫位和相位。</view>
            <template v-else-if="astro">
              <view class="panel stack">
                <SectionHeading
                  :title="chartType"
                  :to="destination('charts', 'knowledge')"
                  action="盘面术语"
                />
                <text class="muted small">{{ natal
                  ? '上升 ' + natal.ascendant.toFixed(2) + '° · 天顶 ' + natal.midheaven.toFixed(2) + '° · ' + settings.state.value.house
                  : '示例盘面 · ' + timePoint }}</text>
                <ChartWheel
                  :title="chartType"
                  :data="astroData"
                  :second="!realNatal && (dual || isPair) ? secondData : undefined"
                  :cusps="natal?.cusps"
                />
                <DataTable
                  :headings="['行星', '星座', '度数', '宫位', '相位', '状态']"
                  :rows="
                    astroData.map((item) => [
                      item.planet,
                      useText ? item.sign.name : item.sign.glyph,
                      (item.degree % 30).toFixed(2) + '°',
                      item.house,
                      useText ? item.aspect : '—',
                      item.retrograde ? '逆行' : '顺行',
                    ])
                  "
                />
                <view v-if="chartType === '法达盘'" class="stack"
                  ><text class="panel-head">法达周期样例</text
                  ><DataTable
                    :headings="['主星', '起始', '截止']"
                    :rows="[
                      ['太阳', '2026', '2036'],
                      ['金星', '2036', '2044'],
                      ['水星', '2044', '2057'],
                    ]"
                /></view>
                <view class="actions"
                  ><button class="btn primary" @tap="saveChart">保存盘面</button
                  ><NavLink
                    class="btn"
                    :to="destination('charts', isPair ? 'astro' : 'match-astro', { id: first })"
                    >{{ isPair ? '查看单方本命盘' : '进入合盘' }}</NavLink
                  >
                  <NavLink v-if="isPair" class="btn" :to="destination('charts', 'astro', { id: second })"
                    >查看另一方</NavLink
                  ></view
                >
              </view>
            </template>
            <view v-else-if="view === 'ziwei'" class="panel stack">
              <SectionHeading title="十二宫与四化" /><text class="muted"
                >Mock 命主 · 禄存　身主 · 天相　{{ schedule }} {{ timePoint }}</text
              >
              <view class="cols-4"
                ><view v-for="palace in ziwei" :key="palace.label" class="panel stack"
                  ><text class="gold">{{ palace.label }}</text
                  ><text>{{ palace.star }} · {{ palace.transformation }}</text
                  ><text class="muted small">{{ palace.period }}</text></view
                ></view
              >
              <button class="btn primary" @tap="saveChart">保存紫微盘</button>
            </view>
            <view v-else-if="view === 'cycles'" class="panel stack">
              <text class="panel-head"
                >{{ schedule }} · {{ timePoint }}{{ schedule === '流时' ? ' ' + hour + ' 时' : '' }}</text
              >
              <text class="muted">原局与观察周期并列。流盘条目为演示数据。</text>
              <DataTable
                :headings="['项目', '年柱', '月柱', '日柱', '时柱']"
                :rows="[
                  ['原局', ...(firstBazi?.pillars.map((item) => item.text) || ['—', '—', '—', '—'])],
                  ['周期参考', '丙午', '辛亥', '乙未', '甲申'],
                ]"
              />
              <NavLink
                class="btn primary"
                :to="destination('today', 'personal', { id: first, date: timePoint })"
                >查看个人运势</NavLink
              >
            </view>
            <view v-else-if="view === 'mansion'" class="panel stack">
              <text class="panel-head gold"
                >{{ mansionName }}宿{{ mansionType === '关系' ? ' × ' + secondMansion + '宿' : '' }}</text
              >
              <text class="muted"
                >{{ mansionType }}星宿 · {{ mansionType === '值日' ? timePoint : firstProfile.name }}</text
              >
              <view v-for="group in mansions" :key="group[0]" class="row"
                ><text>{{ group[0] }}</text
                ><text class="gold">{{ group[1] }}</text></view
              >
              <NavLink class="link" :to="destination('charts', 'match', { id: first })"
                >前往缘分合盘 ›</NavLink
              >
            </view>
            <view v-else-if="isPair" class="panel stack">
              <SectionHeading
                :title="firstProfile.name + ' × ' + secondProfile.name"
                :to="destination('charts', 'history')"
                action="合盘历史"
              />
              <DataTable
                v-if="view === 'match-bazi'"
                :headings="['档案', '年柱', '月柱', '日柱', '时柱']"
                :rows="[
                  [
                    firstProfile.name,
                    ...(firstBazi?.pillars.map((item) => item.text + ' ' + item.elements) || ['—']),
                  ],
                  [
                    secondProfile.name,
                    ...(secondBazi?.pillars.map((item) => item.text + ' ' + item.elements) || ['—']),
                  ],
                ]"
              />
              <text class="gold"
                >互动 {{ compatibilityData.score }} · 交流 {{ compatibilityData.ease }} · 节奏
                {{ compatibilityData.rhythm }}</text
              >
              <text
                >{{ birthdaySign(firstProfile.date).relationship }}
                {{ birthdaySign(secondProfile.date).relationship }}</text
              >
              <view class="actions"
                ><button class="btn primary" @tap="saveChart">保存合盘</button
                ><NavLink class="btn" :to="destination('charts', 'bazi', { id: first })"
                  >查看第一方命盘</NavLink
                ><NavLink class="btn" :to="destination('charts', 'bazi', { id: second })"
                  >查看第二方命盘</NavLink
                ></view
              >
            </view>
          </view>
        </view>
      </template>
    </view>
  </AppShell>
</template>
