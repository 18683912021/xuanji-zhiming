<script setup lang="ts">
import { computed, onBeforeMount, ref, toRef } from 'vue'
import AppShell from '../../components/AppShell.vue'
import NavLink from '../../components/NavLink.vue'
import ToolCard from '../../components/ToolCard.vue'
import SelectField from '../../components/SelectField.vue'
import DateField from '../../components/DateField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { tools, toolGroups } from '../../features/catalog/tools'
import { birthdaySign, compatibility, signById, signs } from '../../features/catalog/zodiac'
import { favorites, toggleFavorite } from '../../features/account/state'
import { destination, go, type Query } from '../../shared/navigation'

const props = withDefaults(defineProps<{ query?: Query; entering?: boolean }>(), { query: () => ({}), entering: true })
const query = toRef(props, 'query')
const search = ref('')
const group = ref('全部')
const element = ref('全部')
const birth = ref('')
const first = ref('aries')
const second = ref('libra')
const ranking = ref(false)
const compared = ref(false)

onBeforeMount(() => {
  first.value = query.value.id || 'aries'
  if (query.value.view === 'relationships') group.value = '星座与关系'
  if (query.value.view === 'divination') group.value = '占卜'
})
const view = computed(() => query.value.view && Object.prototype.hasOwnProperty.call(titles, query.value.view) ? query.value.view : 'index')
const titles: Record<string, string> = {
  index: '探索',
  relationships: '关系工具',
  divination: '占卜工具',
  zodiac: '十二星座图鉴',
  sign: '星座详情',
  compatibility: '星座配对与排行',
  topic: '专题预览',
}
const selected = computed(() => signById(query.value.id))
const signOptions = signs.map(({ id, name }) => ({ value: id, label: name }))
const list = computed(() =>
  tools.filter(
    (tool) =>
      (group.value === '全部' || tool.group === group.value) &&
      (tool.title + tool.description + (tool.keywords || '')).includes(search.value.trim()),
  ),
)
const filteredSigns = computed(() =>
  signs.filter(
    (sign) =>
      (element.value === '全部' || element.value === sign.element) && sign.name.includes(search.value.trim()),
  ),
)
const pair = computed(() => compatibility(signById(first.value), signById(second.value)))
const ranked = computed(() =>
  signs
    .map((sign) => ({ sign, score: compatibility(signById(first.value), sign).score }))
    .sort((a, b) => b.score - a.score),
)
const favoriteId = computed(() => 'zodiac-' + selected.value.id)
function saveSign() {
  toggleFavorite({
    id: favoriteId.value,
    title: selected.value.name + '图鉴',
    to: destination('explore', 'sign', { id: selected.value.id }),
  })
}

function showPair(id?: string) {
  if (id) second.value = id
  compared.value = true
  ranking.value = false
}
</script>

<template>
  <AppShell
    section="explore"
    :entering="entering"
    :title="view === 'sign' ? selected.name : titles[view] || titles.index"
    :detail="view !== 'index'"
  >
    <view class="content-width stack">
      <template v-if="['index', 'relationships', 'divination'].includes(view)">
        <view class="panel stack">
          <input
            v-model="search"
            class="field"
            placeholder="搜索工具，例如本命盘或塔罗"
            aria-label="搜索工具"
          />
          <view class="chips"
            ><button
              v-for="item in toolGroups"
              :key="item"
              class="chip"
              :class="{ selected: group === item }"
              @tap="group = item"
            >
              {{ item }}
            </button></view
          >
        </view>
        <view v-if="list.length" class="cols-3"
          ><ToolCard v-for="tool in list" :key="tool.title" v-bind="tool"
        /></view>
        <view v-else class="panel muted">没找到相应的工具，试试更短的名称。</view>
        <view class="panel stack"
          ><SectionHeading title="专题体验" /><view class="actions">
            <NavLink class="btn" :to="destination('explore', 'topic', { id: 'tarot' })"
              >过去·现在·未来</NavLink
            >
            <NavLink class="btn" :to="destination('explore', 'topic', { id: 'dice' })"
              >用三颗骰子拆解问题</NavLink
            >
          </view></view
        >
      </template>
      <template v-else-if="view === 'zodiac'">
        <view class="panel stack">
          <view class="cols-2"
            ><input v-model="search" class="field" placeholder="搜索星座" aria-label="搜索星座" />
            <DateField
              v-model="birth"
              label="按生日定位"
              @update:model-value="go(destination('explore', 'sign', { id: birthdaySign($event).id }))"
          /></view>
          <view class="chips"
            ><button
              v-for="item in ['全部', '火', '土', '风', '水']"
              :key="item"
              class="chip"
              :class="{ selected: element === item }"
              @tap="element = item"
            >
              {{ item === '全部' ? item : item + '象' }}
            </button></view
          >
        </view>
        <view class="cols-4"
          ><ToolCard
            v-for="sign in filteredSigns"
            :key="sign.id"
            :title="sign.name"
            :description="sign.range + ' · ' + sign.element + '象'"
            :glyph="sign.glyph"
            :to="destination('explore', 'sign', { id: sign.id })"
        /></view>
        <text v-if="!filteredSigns.length" class="muted">没有符合条件的星座。</text>
      </template>
      <template v-else-if="view === 'sign'">
        <view class="split">
          <view class="panel stack"
            ><text class="sign-glyph">{{ selected.glyph }}</text
            ><text class="panel-head">{{ selected.name }} · {{ selected.range }}</text>
            <view class="row"
              ><text>元素与属性</text><text>{{ selected.element }}象 · {{ selected.quality }}</text></view
            >
            <view class="row"
              ><text>守护星</text><text>{{ selected.planet }}</text></view
            >
            <view class="row"
              ><text>象征宫位</text><text>{{ selected.house }}</text></view
            >
            <SelectField
              label="切换星座"
              :model-value="selected.id"
              :options="signOptions"
              @update:model-value="go(destination('explore', 'sign', { id: $event }), 'replace')"
            />
          </view>
          <view class="panel stack"
            ><text class="panel-head">性格与相处主题</text><text>{{ selected.prompt }}</text
            ><text>{{ selected.relationship }}</text>
            <text class="notice">日期属于通用分段，临界日期可用准确出生时间核对。</text>
            <view class="actions"
              ><button class="btn" @tap="saveSign">
                {{ favorites.state.value.some((item) => item.id === favoriteId) ? '取消收藏' : '收藏图鉴' }}
              </button>
              <NavLink class="btn primary" :to="destination('today', 'fortune', { sign: selected.id })"
                >查看运势</NavLink
              >
              <NavLink class="btn" :to="destination('explore', 'compatibility', { id: selected.id })"
                >开始配对</NavLink
              ></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'compatibility'">
        <view class="split"
          ><view class="panel stack"
            ><SelectField v-model="first" label="第一个星座" :options="signOptions" /><SelectField
              v-model="second"
              label="第二个星座"
              :options="signOptions"
            />
            <view class="actions"
              ><button
                class="btn primary"
                @tap="showPair()"
              >
                查看配对</button
              ><button class="btn" @tap="ranking = true">查看排行</button></view
            ></view
          >
          <view v-if="ranking" class="panel stack"
            ><text class="panel-head">{{ signById(first).name }}配对排行</text>
            <button
              v-for="item in ranked"
              :key="item.sign.id"
              class="row"
              @tap="showPair(item.sign.id)"
            >
              <text>{{ item.sign.name }}</text
              ><text class="gold">{{ item.score }} 分 ›</text>
            </button>
          </view>
          <view v-else class="panel stack"
            ><text class="panel-head">{{
              compared ? signById(first).name + ' × ' + signById(second).name : '选择两个星座'
            }}</text>
            <template v-if="compared"
              ><text class="match-score">{{ pair.score }} 分</text
              ><text>交流 {{ pair.ease }} · 节奏 {{ pair.rhythm }} · 空间 {{ pair.space }}</text>
              <text>{{ signById(first).relationship }} {{ signById(second).relationship }}</text
              ><text class="notice">体验分来自示例的元素与宫位关系，用于演示版面。</text></template
            >
            <text v-else class="muted">查看相处维度、沟通建议和对应排行。</text>
          </view>
        </view>
      </template>
      <template v-else-if="view === 'topic'">
        <view class="panel stack"
          ><text class="panel-head">{{ query.id === 'dice' ? '行星、星座与宫位' : '过去、现在与未来' }}</text>
          <text class="muted">{{
            query.id === 'dice'
              ? '用三颗星骰把一件事拆成动力、表达方式和生活场景。'
              : '用三张牌分别回顾既有条件、眼前感受和可尝试的下一步。'
          }}</text>
          <view class="cols-3"
            ><view
              v-for="part in query.id === 'dice'
                ? ['行星', '星座', '宫位']
                : ['过去 · 隐者', '现在 · 节制', '未来 · 星星']"
              :key="part"
              class="panel"
              >{{ part }}</view
            ></view
          >
          <view class="actions"
            ><NavLink
              class="btn primary"
              :to="destination('divination', query.id === 'dice' ? 'dice' : 'tarot', { spread: 'timeline' })"
              >开始体验</NavLink
            ></view
          >
        </view>
      </template>
    </view>
  </AppShell>
</template>
<style scoped>
.sign-glyph {
  color: var(--gold);
  font-size: 68px;
}
.match-score {
  color: var(--gold);
  font-size: 36px;
  font-weight: 700;
}
</style>
