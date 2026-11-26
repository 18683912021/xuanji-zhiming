<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import DateField from '../../components/DateField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { availableProfiles, favorites, preferences, toggleFavorite } from '../../features/account/state'
import { calendarDay, monthDays, monthOffset } from '../../features/calendar/calendar'
import { events, happensOn } from '../../features/calendar/events'
import { groups } from '../../features/calendar/terms'
import { birthdaySign, signById, signs } from '../../features/catalog/zodiac'
import { readings } from '../../features/divination/records'
import { destination, go, type Query } from '../../shared/navigation'
import { dateKey, displayDate, offsetDate, parseDate } from '../../shared/storage'

const titles: Record<string, string> = {
  index: '今日',
  fortune: '星座运势',
  personal: '个人运势',
  calendar: '星象日历',
  star: '当日星象',
  almanac: '万年历与老黄历',
  auspicious: '择吉查询',
  terms: '二十四节气',
}
const query = ref<Query>({})
const view = computed(() => (query.value.view && query.value.view in titles ? query.value.view : 'index'))
const date = ref(dateKey())
const month = ref(dateKey())
const sign = ref(preferences.state.value.sign)
const selected = ref(availableProfiles.value[0]!.id)
const cycle = ref('今日')
const personalModes = ['日', '周', '月', '年']
const signModes = ['今日', '明日', '本周', '本月', '今年']
const basis = ref('星盘行运')
const termGroup = ref('全部')
const chosenTerm = ref('')
const start = ref(dateKey())
const end = ref(offsetDate(dateKey(), 28))
const purpose = ref('出行')
const onlyWeekend = ref(false)
const searched = ref(false)
const searchError = ref('')
const dayOptions = ref<string[]>([])
const signOptions = signs.map(({ id, name }) => ({ value: id, label: name }))
const profileOptions = computed(() =>
  availableProfiles.value.map((item) => ({ value: item.id, label: item.name })),
)
const profile = computed(
  () => availableProfiles.value.find((item) => item.id === selected.value) || availableProfiles.value[0]!,
)
const day = computed(() => calendarDay(date.value))
const effectiveDate = computed(() => (cycle.value === '明日' ? offsetDate(date.value, 1) : date.value))
const activeSign = computed(() =>
  view.value === 'personal' ? birthdaySign(profile.value.date) : signById(sign.value),
)
const grid = computed(() => monthDays(month.value))
const daily = computed(() =>
  readings.state.value.find((item) => item.kind === 'daily' && item.date === date.value),
)
const dayEvents = computed(() => events.state.value.filter((event) => happensOn(event, date.value)))
const favoriteId = computed(() => view.value + date.value + activeSign.value.id)
const isFavorite = computed(() => favorites.state.value.some((item) => item.id === favoriteId.value))
const degree = computed(
  () =>
    69 +
    ((parseDate(effectiveDate.value).getDate() + signs.indexOf(activeSign.value) * 3 + cycle.value.length) %
      26),
)
const fortune = computed(() => [
  ['综合', activeSign.value.prompt],
  ['关系', activeSign.value.relationship],
  [
    '事业与学习',
    cycle.value.includes('月') || cycle.value === '年'
      ? '先定能重复的节奏，再为下一阶段选一个目标。'
      : '试着把复杂工作拆为能在一个时间段完成的小项。',
  ],
  ['财富观察', '回顾本期内来自习惯或计划外的支出。'],
  [
    '文化栏目',
    '幸运色 ' +
      ['烟紫', '浅金', '石青', '藕粉'][degree.value % 4] +
      ' · 数字 ' +
      (degree.value % 9) +
      ' · 参考方位 ' +
      ['东', '南', '西', '北'][degree.value % 4],
  ],
])

onLoad((value) => {
  query.value = value || {}
  if (
    query.value.date &&
    /^\d{4}-\d{2}-\d{2}$/.test(query.value.date) &&
    !isNaN(parseDate(query.value.date).getTime())
  ) {
    date.value = query.value.date
    month.value = query.value.date
  }
  if (query.value.sign) sign.value = signById(query.value.sign).id
  if (query.value.id) selected.value = query.value.id
  if (view.value === 'personal') cycle.value = '日'
})

function chooseSign(value: string) {
  sign.value = value
  preferences.write({ ...preferences.state.value, sign: value, fortuneMode: 'sign' })
}
function setToday() {
  date.value = dateKey()
  month.value = date.value
}
function saveFavorite() {
  toggleFavorite({
    id: favoriteId.value,
    title: titles[view.value] + ' · ' + displayDate(date.value),
    to: destination('today', view.value, { date: date.value, sign: sign.value, id: selected.value }),
  })
}
function searchDays() {
  searched.value = true
  searchError.value = ''
  const duration = Math.round((parseDate(end.value).getTime() - parseDate(start.value).getTime()) / 86400000)
  if (duration < 0 || duration > 366 || !Number.isFinite(duration)) {
    searchError.value = '请选择正序且不超过一年的日期范围。'
    dayOptions.value = []
    return
  }
  dayOptions.value = Array.from({ length: duration + 1 }, (_, i) => offsetDate(start.value, i)).filter(
    (value) => {
      const data = calendarDay(value)
      return (
        data.yi.includes(purpose.value) && (!onlyWeekend.value || ['周六', '周日'].includes(data.weekday))
      )
    },
  )
}
</script>

<template>
  <AppShell section="today" :title="titles[view]" :detail="view !== 'index'">
    <view class="content-width stack">
      <template v-if="view === 'index'">
        <view class="split">
          <view class="panel stack">
            <text class="gold">{{ displayDate(date) }} · {{ day.weekday }} · {{ day.lunar }}</text>
            <text class="panel-head">{{ activeSign.glyph }} {{ activeSign.name }}今日观察</text
            ><text>{{ activeSign.prompt }}</text>
            <SelectField
              v-model="sign"
              label="选择星座"
              :options="signOptions"
              @update:model-value="chooseSign"
            />
            <view class="actions"
              ><NavLink class="btn primary" :to="destination('today', 'fortune', { sign })"
                >查看星座运势</NavLink
              ><NavLink class="btn" :to="destination('today', 'personal', { id: selected })"
                >个人运势</NavLink
              ></view
            >
          </view>
          <view class="panel stack"
            ><SectionHeading
              :title="day.season + ' · ' + day.moon"
              :to="destination('today', 'terms')"
              action="节气图鉴"
            />
            <text class="notice">月相为按农历日期估计的示例。</text>
            <NavLink class="row-link" :to="destination('divination', 'daily')"
              ><text>{{ daily ? daily.summary : '翻开每日塔罗' }}</text
              ><text class="gold">›</text></NavLink
            >
            <NavLink class="row-link" :to="destination('today', 'calendar')"
              ><text>浏览星象日历</text><text class="gold">›</text></NavLink
            >
            <NavLink class="row-link" :to="destination('account', 'journal-edit', { date })"
              ><text>记录今天</text><text class="gold">›</text></NavLink
            >
            <NavLink
              v-for="event in dayEvents"
              :key="event.id"
              class="row-link"
              :to="destination('account', 'event-edit', { id: event.id })"
              ><text>{{ event.title }}</text
              ><text class="gold">今天</text></NavLink
            >
          </view>
        </view>
        <view class="cols-3">
          <NavLink class="panel" :to="destination('today', 'almanac')">万年历与老黄历 ›</NavLink>
          <NavLink class="panel" :to="destination('today', 'auspicious')">传统择吉 ›</NavLink>
          <NavLink class="panel" :to="destination('account', 'events')">特别日期与生日 ›</NavLink>
        </view>
      </template>
      <template v-else-if="view === 'fortune' || view === 'personal'">
        <view class="workspace">
          <view class="panel stack">
            <SelectField
              v-if="view === 'fortune'"
              v-model="sign"
              label="星座"
              :options="signOptions"
              @update:model-value="chooseSign"
            />
            <SelectField v-else v-model="selected" label="出生档案" :options="profileOptions" />
            <SelectField
              v-if="view === 'personal'"
              v-model="basis"
              label="资料依据"
              :options="['星盘行运', '八字流盘'].map((value) => ({ value, label: value }))"
            />
            <DateField v-model="date" label="查看日期" />
            <view class="chips"
              ><button
                v-for="mode in view === 'personal' ? personalModes : signModes"
                :key="mode"
                class="chip"
                :class="{ selected: cycle === mode }"
                @tap="cycle = mode"
              >
                {{ mode }}
              </button></view
            >
          </view>
          <view class="panel stack">
            <text class="panel-head">{{
              view === 'personal' ? profile.name + ' · ' + basis : activeSign.name + ' · ' + cycle
            }}</text>
            <text class="gold">{{ displayDate(effectiveDate) }} · 示例综合 {{ degree }}</text>
            <view v-for="item in fortune" :key="item[0]" class="row"
              ><text class="gold">{{ item[0] }}</text
              ><text>{{ item[1] }}</text></view
            >
            <view class="actions"
              ><button class="btn" @tap="saveFavorite">{{ isFavorite ? '取消收藏' : '收藏运势' }}</button>
              <NavLink class="btn" :to="destination('account', 'journal-edit', { date: effectiveDate })"
                >写日记</NavLink
              >
              <NavLink
                v-if="view === 'personal'"
                class="btn"
                :to="destination('charts', basis === '八字流盘' ? 'cycles' : 'astro', { id: selected })"
                >查看源盘</NavLink
              >
              <NavLink
                v-if="view === 'personal'"
                class="btn primary"
                :to="destination('ai', 'new', { role: 'astrologer', profile: selected })"
                >问 AI 占星师</NavLink
              >
              <NavLink v-else class="btn" :to="destination('explore', 'sign', { id: sign })"
                >星座详情</NavLink
              ></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'calendar' || view === 'star' || view === 'almanac'">
        <view class="split">
          <view v-if="view !== 'star'" class="panel stack">
            <view class="section-heading"
              ><button class="btn" @tap="month = monthOffset(month, -1)">‹</button
              ><text class="panel-head">{{ month.slice(0, 7) }}</text
              ><button class="btn" @tap="month = monthOffset(month, 1)">›</button></view
            >
            <view class="calendar-grid">
              <text
                v-for="label in ['一', '二', '三', '四', '五', '六', '日']"
                :key="label"
                class="muted day-label"
                >{{ label }}</text
              >
              <button
                v-for="item in grid"
                :key="item.day"
                class="calendar-cell"
                :class="{ active: item.day === date, faint: !item.current }"
                @tap="date = item.day"
              >
                <text class="block"
                  >{{ item.number
                  }}<text v-if="events.state.value.some((event) => happensOn(event, item.day))" class="gold"
                    >·</text
                  ></text
                ><text class="day-detail">{{ item.description }}</text>
              </button>
            </view>
            <button class="link" @tap="setToday">回到今天</button>
          </view>
          <view class="panel stack">
            <text class="panel-head">{{ displayDate(date) }} · {{ day.weekday }}</text>
            <text class="gold">{{ day.lunar }} · {{ day.season }} · {{ day.moon }}</text>
            <text v-if="day.holiday">{{ day.holiday }}</text>
            <template v-if="view === 'almanac'"
              ><view class="row"
                ><text class="gold">宜</text><text>{{ day.yi.join('、') }}</text></view
              >
              <view class="row"
                ><text class="gold">忌</text><text>{{ day.ji.join('、') }}</text></view
              ><text class="muted">传统日序 · {{ day.zodiac }}日</text>
              <NavLink class="btn" :to="destination('today', 'auspicious')">打开择吉</NavLink>
            </template>
            <text v-else class="muted">{{
              day.term ? '节气交替，适合记录自然观察。' : '查看当天的农历、月相和个人事件。'
            }}</text>
            <NavLink
              v-for="event in dayEvents"
              :key="event.id"
              class="row-link"
              :to="destination('account', 'event-edit', { id: event.id })"
              >{{ event.title }}</NavLink
            >
            <view class="actions">
              <NavLink
                v-if="view === 'calendar'"
                class="btn primary"
                :to="destination('today', 'star', { date })"
                >当日星象</NavLink
              >
              <button class="btn" @tap="saveFavorite">{{ isFavorite ? '取消收藏' : '收藏日期' }}</button>
              <NavLink class="btn" :to="destination('today', 'fortune', { date, sign })">当日运势</NavLink>
              <NavLink class="btn" :to="destination('account', 'event-edit', { date })">添加事件</NavLink>
              <NavLink class="btn" :to="destination('divination', 'wishes')">去许愿</NavLink>
            </view>
          </view>
        </view>
      </template>
      <template v-else-if="view === 'auspicious'">
        <view class="split">
          <view class="panel stack">
            <SelectField
              v-model="purpose"
              label="传统事项"
              :options="
                ['出行', '开市', '嫁娶', '会亲友', '求学', '祈福'].map((value) => ({ value, label: value }))
              "
            />
            <DateField v-model="start" label="起始日期" /><DateField v-model="end" label="截止日期" />
            <view class="switch-row"
              ><text>仅查看周末</text
              ><AppSwitch label="仅查看周末" :checked="onlyWeekend" @change="onlyWeekend = $event"
            /></view>
            <button class="btn primary" @tap="searchDays">查询日期</button>
          </view>
          <view class="panel stack"
            ><text class="panel-head">查询结果</text>
            <text v-if="searchError" class="error">{{ searchError }}</text
            ><text v-else-if="!searched" class="muted">选择事项与不超过一年的日期范围。</text>
            <text v-else-if="!dayOptions.length" class="muted">没有符合条件的日期。可以扩大时间范围。</text>
            <NavLink
              v-for="value in dayOptions"
              :key="value"
              class="row-link"
              :to="destination('today', 'almanac', { date: value })"
              ><text>{{ displayDate(value) }}</text
              ><text class="gold">查看黄历 ›</text></NavLink
            >
          </view>
        </view>
      </template>
      <template v-else>
        <view class="panel stack"
          ><view class="chips"
            ><button
              v-for="season in ['全部', '春', '夏', '秋', '冬']"
              :key="season"
              class="chip"
              :class="{ selected: termGroup === season }"
              @tap="termGroup = season"
            >
              {{ season }}
            </button></view
          >
          <view
            v-for="group in groups.filter((item) => termGroup === '全部' || termGroup === item.season)"
            :key="group.season"
            class="stack"
          >
            <text class="panel-head">{{ group.season }}</text>
            <view class="cols-3"
              ><button
                v-for="[name, description] in group.terms"
                :key="name"
                class="panel term-card"
                @tap="chosenTerm = chosenTerm === name ? '' : name"
              >
                <text class="gold">{{ name }}</text
                ><text v-if="chosenTerm === name" class="muted block">{{ description }}</text>
              </button></view
            >
          </view>
        </view>
      </template>
    </view>
  </AppShell>
</template>
<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
}
.day-label {
  text-align: center;
}
.calendar-cell {
  padding: 4px 0;
  border-radius: 5px;
  min-height: 43px;
  font-size: 14px;
  background: #291c36;
}
.calendar-cell.active {
  background: #d6b66c;
  color: #221531;
}
.calendar-cell.faint {
  opacity: 0.45;
}
.day-detail {
  display: block;
  font-size: 10px;
  line-height: 1.2;
}
.term-card {
  text-align: left;
  min-height: 55px;
}
</style>
