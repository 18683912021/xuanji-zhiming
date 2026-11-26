<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { destination, go } from '../../shared/navigation'
import { dateKey } from '../../shared/storage'
import { signById, signs } from '../catalog/zodiac'
import { answerPages, dreamTopics, houses, planets, planetThemes, sample, spreads, verses } from './content'
import { cards, deal, type DrawnCard } from './tarot'
import { castCoins, changed, hexagram, isMoving, yaoLabels, yaoNames, type Yao } from './liuyao'
import { createReading, readings } from './records'
import { liuyaoDraft as draft } from './draft'

const props = defineProps<{ view: string; spread?: string; id?: string }>()
const question = ref(props.view === 'liuyao' ? draft.state.value.question : '')
const lines = ref<Yao[]>(props.view === 'liuyao' ? draft.state.value.lines : [])
const method = ref(draft.state.value.method)
const toss = ref<number[]>([])
const spread = ref(spreads.find((item) => item.id === props.spread) || spreads[0]!)
const step = ref(1)
const deck = ref(deal())
const selected = ref<number[]>([])
const theme = ref('当下选择')
const mood = ref('平静')
const dream = ref('')
const topic = ref(dreamTopics[0]!)
const drawnDice = ref<{ planet: number; sign: string; house: number }>()
const answer = ref('')
const captured = ref(false)
const selectedCard = computed(() => Number(props.id || 0))
const cardKeyword = ref('')
const today = dateKey()
const daily = computed(() =>
  readings.state.value.find((item) => item.kind === 'daily' && item.date === today),
)
const tarotTitle = computed(() => spread.value.name)
const ready = computed(() => selected.value.length === spread.value.positions.length)
const searchableCards = computed(() =>
  cards.map(([name], id) => ({ name, id })).filter((item) => item.name.includes(cardKeyword.value.trim())),
)

if (props.view === 'liuyao')
  watch(
    [question, lines, method],
    () => {
      draft.write({ question: question.value, lines: [...lines.value], method: method.value })
    },
    { deep: true, flush: 'sync' },
  )

function showRecord(item: ReturnType<typeof createReading>) {
  if (item) {
    captured.value = true
    go(destination('account', 'result', { id: item.id }), 'replace')
  }
}

function choose(index: number) {
  if (selected.value.includes(index)) selected.value = selected.value.filter((item) => item !== index)
  else if (!ready.value) selected.value = [...selected.value, index]
}
function shuffle() {
  deck.value = deal()
  selected.value = []
}

function renderTarot(picks: DrawnCard[], title: string, kind: string) {
  const item = createReading(
    {
      kind,
      title,
      topic: question.value.trim(),
      summary: picks
        .map((pick) => cards[pick.index]![0] + ' · ' + (pick.reversed ? '逆位' : '正位'))
        .join(' / '),
      sections: picks.map((pick) => ({
        title: pick.position + ' · ' + cards[pick.index]![0],
        content: cards[pick.index]![pick.reversed ? 2 : 1],
      })),
      cards: picks,
      source: destination('divination', kind === 'daily' ? 'daily' : 'tarot', { spread: spread.value.id }),
    },
    kind === 'daily',
  )
  return item
}

function flip(random = false) {
  if (captured.value || (!ready.value && !random)) return
  const picked = random
    ? deck.value.slice(0, spread.value.positions.length)
    : selected.value.map((index) => deck.value[index]!)
  showRecord(
    renderTarot(
      picked.map((item, index) => ({ ...item, position: spread.value.positions[index]! })),
      '塔罗 · ' + tarotTitle.value,
      'tarot',
    ),
  )
}

function flipDaily() {
  if (daily.value || captured.value) return
  const item = renderTarot([{ ...deck.value[0]!, position: '今日' }], '今日塔罗', 'daily')
  if (item) captured.value = true
}

function addLine(value?: Yao) {
  if (lines.value.length >= 6) return
  const cast = value ? { value, coins: [] } : castCoins()
  toss.value = cast.coins
  lines.value = [...lines.value, cast.value]
}

function resolveHexagram() {
  if (captured.value || lines.value.length !== 6) return
  const base = hexagram(lines.value)
  const moving = lines.value.flatMap((line, index) => (isMoving(line) ? [yaoNames[index]] : [])).join('、')
  const item = createReading({
    kind: 'liuyao',
    title: '六爻 · ' + base,
    topic: question.value.trim(),
    summary: moving ? base + ' → ' + hexagram(changed(lines.value)) : base + ' · 静卦',
    lines: [...lines.value],
    sections: [
      { title: '爻序与动爻', content: moving ? '动爻为' + moving + '，由下往上读取。' : '此卦无动爻。' },
      {
        title: '纳甲与六亲示例',
        content: '示例数据：初爻子水、二爻寅木。六亲按卦宫与爻的五行关系判定，世应是观测双方的位置。',
      },
      { title: '如何回看', content: '先确认记录的爻序与起卦方式，然后对照问题当时的条件。' },
    ],
    source: destination('divination', 'liuyao'),
  })
  if (item) {
    lines.value = []
    question.value = ''
    showRecord(item)
  }
}

function drawOracle() {
  if (captured.value) return
  const value = sample(verses)
  showRecord(
    createReading({
      kind: 'oracle',
      title: '问签 · ' + value.title,
      topic: question.value.trim() || theme.value,
      summary: value.verse,
      sections: [
        { title: '签文释义', content: value.reading },
        { title: '出处', content: '玄机知命原创签文。' },
      ],
      source: destination('divination', 'oracle'),
    }),
  )
}

function rollDice() {
  if (captured.value) return
  drawnDice.value = {
    planet: Math.floor(Math.random() * planets.length),
    sign: sample(signs).id,
    house: Math.floor(Math.random() * houses.length),
  }
}
function saveDice() {
  if (!drawnDice.value || captured.value) return
  const { planet, sign, house } = drawnDice.value
  showRecord(
    createReading(
      {
        kind: 'dice',
        title: '星座骰子',
        topic: question.value.trim(),
        summary: planets[planet] + ' · ' + signById(sign).name + ' · 第' + (house + 1) + '宫',
        sections: [
          { title: '行星 · ' + planetThemes[planet], content: '把注意力放在实际影响你行动的需求。' },
          { title: '星座 · ' + signById(sign).name, content: signById(sign).relationship },
          { title: '宫位 · ' + houses[house], content: '用这个生活场景缩小问题范围，找一个适合观察的例子。' },
        ],
        source: destination('divination', 'dice'),
      },
      true,
    ),
  )
}

function openBook() {
  const options = answerPages.filter((page) => page !== answer.value)
  answer.value = sample(options)
}
function saveAnswer() {
  if (captured.value || !answer.value) return
  showRecord(
    createReading(
      {
        kind: 'book',
        title: '答案之书',
        topic: question.value.trim(),
        summary: answer.value,
        sections: [{ title: '留给自己', content: '这句话让你最先想到哪件眼下可以尝试的事？' }],
        source: destination('divination', 'book'),
      },
      true,
    ),
  )
}

function saveDream() {
  if (captured.value || !dream.value.trim()) return
  showRecord(
    createReading(
      {
        kind: 'dream',
        title: '梦境记录',
        topic: dream.value.trim(),
        summary: '醒来的感受 · ' + mood.value,
        sections: [
          { title: '象征性解读 · Mock', content: topic.value.note },
          { title: '资料出处', content: '玄机知命梦境观察示例 · ' + topic.value.name },
        ],
        source: destination('divination', 'dream'),
      },
      true,
    ),
  )
}

function selectSpread(item: (typeof spreads)[number]) {
  spread.value = item
  shuffle()
}

function selectDream(item: (typeof dreamTopics)[number]) {
  topic.value = item
  dream.value = item.text
}
</script>

<template>
  <view class="content-width stack">
    <template v-if="view === 'tarot'">
      <view class="workspace">
        <view class="panel stack">
          <text class="panel-head">问题与牌阵</text>
          <view
            ><text class="field-label">我想问（可选）</text
            ><textarea
              v-model="question"
              class="field area"
              maxlength="160"
              placeholder="最近有什么想弄清楚？"
            />
          </view>
          <button class="link" @tap="question = '我该怎样处理手头这个变化？'">使用示例问题</button>
          <view class="stack"
            ><button
              v-for="item in spreads"
              :key="item.id"
              class="btn"
              :class="{ primary: item.id === spread.id }"
              @tap="selectSpread(item)"
            >
              {{ item.name }}
            </button></view
          >
          <NavLink class="link" :to="destination('divination', 'deck')">查 78 张牌义 ›</NavLink>
        </view>
        <view class="panel stack draw-panel">
          <text class="panel-head">{{
            step === 1 ? tarotTitle : '选 ' + spread.positions.length + ' 张牌'
          }}</text>
          <text class="muted">{{ spread.guide }}</text>
          <view class="chips"
            ><text v-for="position in spread.positions" :key="position" class="chip">{{
              position
            }}</text></view
          >
          <button v-if="step === 1" class="btn primary" @tap="step = 2">开始抽牌</button>
          <template v-else>
            <view class="deck">
              <button
                v-for="(_, index) in deck"
                :key="index"
                class="playing-card"
                :class="{ picked: selected.includes(index) }"
                :aria-label="'第 ' + (index + 1) + ' 张牌'"
                @tap="choose(index)"
              >
                <text v-if="selected.includes(index)">{{ selected.indexOf(index) + 1 }}</text
                ><AppIcon v-else name="ai" />
              </button>
            </view>
            <text class="muted small">已选 {{ selected.length }} / {{ spread.positions.length }}</text>
            <view class="actions"
              ><button class="btn primary" :disabled="!ready" @tap="flip()">翻开所选牌</button
              ><button class="btn" @tap="flip(true)">随机抽牌</button
              ><button class="btn" @tap="shuffle">重新洗牌</button></view
            >
          </template>
        </view>
      </view>
    </template>
    <template v-else-if="view === 'daily'">
      <view class="panel stack draw-panel">
        <text class="gold">{{ today }}</text>
        <text class="panel-head">{{ daily ? daily.summary : '翻一张今日塔罗' }}</text>
        <text class="muted">{{
          daily ? daily.sections[0]?.content : '今天的日签生成后，会保留在这台设备上。'
        }}</text>
        <button v-if="!daily" class="playing-card single-card" @tap="flipDaily"><AppIcon name="ai" /></button>
        <view class="actions">
          <button v-if="!daily" class="btn primary" @tap="flipDaily">翻开日签</button>
          <NavLink v-if="daily" class="btn primary" :to="destination('account', 'result', { id: daily.id })"
            >查看日签</NavLink
          >
          <NavLink
            v-if="daily"
            class="btn"
            :to="destination('account', 'journal-edit', { date: today, source: daily.id })"
            >写入日记</NavLink
          >
          <NavLink class="btn" :to="destination('divination', 'tarot')">前往塔罗问事</NavLink>
          <NavLink class="btn" :to="destination('divination', 'dice')">试试星骰</NavLink>
        </view>
      </view>
    </template>
    <template v-else-if="view === 'deck'">
      <input v-model="cardKeyword" class="field" placeholder="搜索牌名" />
      <view class="cols-4">
        <NavLink
          v-for="item in searchableCards"
          :key="item.id"
          class="panel"
          :to="destination('divination', 'card', { id: String(item.id) })"
          ><text class="gold">✧ </text>{{ item.name }}</NavLink
        >
      </view>
      <text v-if="!searchableCards.length" class="muted">没有找到这张牌。</text>
    </template>
    <view v-else-if="view === 'card'" class="panel stack">
      <template v-if="cards[selectedCard]">
        <AppIcon name="tarot" class="reading-art" /><text class="panel-head gold">{{
          cards[selectedCard]?.[0]
        }}</text>
        <text>正位 · {{ cards[selectedCard]?.[1] }}</text
        ><text>逆位 · {{ cards[selectedCard]?.[2] }}</text>
        <text class="notice">牌义来源为玄机知命体验版条目。</text>
        <NavLink class="link" :to="destination('divination', 'deck')">回到牌义图鉴 ›</NavLink>
      </template>
      <text v-else class="muted">这张牌不可用。</text>
    </view>
    <template v-else-if="view === 'liuyao'">
      <view class="split">
        <view class="panel stack">
          <view
            ><text class="field-label">问事主题</text
            ><textarea
              v-model="question"
              class="field area"
              maxlength="160"
              placeholder="可以写下问题，方便稍后回看"
            />
          </view>
          <view class="chips"
            ><button class="chip" :class="{ selected: method === 'coins' }" @tap="method = 'coins'">
              三钱模拟</button
            ><button class="chip" :class="{ selected: method === 'manual' }" @tap="method = 'manual'">
              手动录爻
            </button></view
          >
          <button
            v-if="method === 'coins'"
            class="btn primary"
            :disabled="lines.length >= 6"
            @tap="addLine()"
          >
            投三枚铜钱
          </button>
          <view v-else class="chips"
            ><button
              v-for="n in [6, 7, 8, 9] as const"
              :key="n"
              class="chip"
              :disabled="lines.length >= 6"
              @tap="addLine(n)"
            >
              {{ yaoLabels[n] }}
            </button></view
          >
          <text v-if="toss.length" class="gold">最近投掷 · {{ toss.join('　') }}</text>
        </view>
        <view class="panel stack">
          <text class="panel-head">起卦进度 {{ lines.length }} / 6</text>
          <view v-for="(name, index) in yaoNames" :key="name" class="row">
            <text>{{ name }}</text
            ><text class="gold">{{
              lines[index] ? yaoLabels[lines[index]!] + (isMoving(lines[index]!) ? ' · 动爻' : '') : '待录入'
            }}</text>
          </view>
          <text class="muted small">由初爻到上爻录入，可返回继续已有草稿。</text>
          <view class="actions"
            ><button class="btn primary" :disabled="lines.length !== 6" @tap="resolveHexagram">
              核对并查看卦象
            </button>
            <button class="btn" :disabled="!lines.length" @tap="lines = lines.slice(0, -1)">
              撤销上一爻
            </button></view
          >
        </view>
      </view>
    </template>
    <template v-else-if="view === 'oracle'">
      <view class="split"
        ><view class="panel stack">
          <SelectField
            v-model="theme"
            label="处境主题"
            :options="
              ['当下选择', '人际关系', '学习工作', '自我观察'].map((value) => ({ value, label: value }))
            "
          />
          <view
            ><text class="field-label">想问的事（可选）</text
            ><textarea
              v-model="question"
              class="field area"
              maxlength="160"
              placeholder="把你关心的事写下来"
            />
          </view> </view
        ><view class="panel stack draw-panel"
          ><AppIcon name="oracle" class="reading-art" /><text class="panel-head">一签一问</text
          ><text class="muted">抽一则原创短签，看看值得追问的地方。</text
          ><button class="btn primary" @tap="drawOracle">抽一支签</button></view
        ></view
      >
    </template>
    <template v-else-if="view === 'dice' || view === 'book'">
      <view class="split"
        ><view class="panel stack">
          <text class="panel-head">留一个问题（可选）</text
          ><textarea v-model="question" class="field area" maxlength="160" placeholder="你也可以在心中默念" />
          <button v-if="view === 'dice'" class="btn primary" @tap="rollDice">
            {{ drawnDice ? '再掷一次' : '掷三颗星骰' }}
          </button>
          <button v-else class="btn primary" @tap="openBook">
            {{ answer ? '再翻一页' : '翻开答案之书' }}
          </button> </view
        ><view class="panel stack draw-panel">
          <AppIcon :name="view === 'dice' ? 'dice' : 'book'" class="reading-art" />
          <template v-if="drawnDice"
            ><text class="panel-head"
              >{{ planets[drawnDice.planet] }} · {{ signById(drawnDice.sign).name }} · 第{{
                drawnDice.house + 1
              }}宫</text
            >
            <text
              >{{ planetThemes[drawnDice.planet] }} / {{ signById(drawnDice.sign).element }}象 /
              {{ houses[drawnDice.house] }}</text
            ><button class="btn" @tap="saveDice">保存并展开解读</button></template
          >
          <template v-else-if="answer"
            ><text class="panel-head">{{ answer }}</text
            ><button class="btn" @tap="saveAnswer">保存这一页</button></template
          >
          <text v-else class="muted">结果会在这里展开。</text>
        </view></view
      >
    </template>
    <template v-else-if="view === 'dream'">
      <view class="split"
        ><view class="panel stack">
          <view
            ><text class="field-label">梦里的场景</text
            ><textarea
              v-model="dream"
              class="field area"
              maxlength="1000"
              placeholder="记下梦里的情绪、人物或几个关键画面"
            />
          </view>
          <SelectField
            v-model="mood"
            label="醒来时的感受"
            :options="['平静', '好奇', '紧张', '欣喜', '困惑'].map((value) => ({ value, label: value }))"
          />
          <button class="btn primary" :disabled="!dream.trim()" @tap="saveDream">
            保存并查看示例解读
          </button> </view
        ><view class="panel stack"
          ><SectionHeading title="常见梦境" />
          <button v-for="item in dreamTopics" :key="item.name" class="row" @tap="selectDream(item)">
            <text>{{ item.name }}</text
            ><text class="gold">使用示例 ›</text>
          </button>
        </view></view
      >
    </template>
  </view>
</template>

<style scoped>
.draw-panel {
  justify-items: center;
  text-align: center;
  min-height: 230px;
  align-content: center;
  padding-top: 28px;
  padding-bottom: 28px;
  background:
    radial-gradient(ellipse at 50% 5%, #63417261, #21152f00 74%), linear-gradient(145deg, #291a35, #1b1228);
}
.deck {
  width: 100%;
  max-width: 440px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 8px auto;
  justify-items: center;
}
.playing-card {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  width: min(100%, 93px);
  height: 133px;
  border: 1px solid #b58f5b;
  color: #ebcc8c;
  background: radial-gradient(ellipse at 54% 44%, #52345e, #20142d 73%), #20142d;
  border-radius: 7px;
  box-shadow:
    inset 0 0 0 3px #25172f,
    inset 0 0 0 4px #c59a655a,
    0 8px 16px #0b061275;
  font: 650 27px/1 var(--serif);
}
.playing-card::before {
  position: absolute;
  inset: 11px 9px;
  border-top: 1px solid #e2bd7776;
  border-bottom: 1px solid #e2bd7776;
  content: '';
  pointer-events: none;
}
.playing-card.picked {
  background: radial-gradient(ellipse at center, #5e456e, #39274a);
  border: 2px solid #edcb8f;
}
@media (max-width: 767px) {
  .playing-card:not(.single-card) {
    height: 104px;
  }
}
.single-card {
  width: 88px;
  height: 125px;
}
</style>
