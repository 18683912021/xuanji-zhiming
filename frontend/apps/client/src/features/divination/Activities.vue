<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { account, updateAccount } from '../account/state'
import { confirmAction, destination, go, toast } from '../../shared/navigation'
import { dateKey, localStore, makeId, offsetDate } from '../../shared/storage'
import { createReading } from './records'

const props = defineProps<{ view: string }>()
type Wish = {
  id: string
  body: string
  light: string
  star: string
  isPublic: boolean
  own: boolean
  likes: number
  date: string
  liked?: boolean
}
const today = dateKey()
const wishes = localStore<Wish[]>('wishes', [
  {
    id: 'wish-river',
    body: '希望今年能完成一本关于城市植物的手账。',
    light: '星雾紫',
    star: '月亮',
    isPublic: true,
    own: false,
    likes: 18,
    date: today,
  },
  {
    id: 'wish-light',
    body: '愿下次遇到变化时，也能给自己一点耐心。',
    light: '玄夜金',
    star: '金星',
    isPublic: true,
    own: false,
    likes: 7,
    date: today,
  },
])
const box = ref('愿望墙')
const body = ref('')
const star = ref('月亮')
const light = ref('星雾紫')
const isPublic = ref(false)
const wishesVisible = computed(() =>
  wishes.state.value.filter((item) => (box.value === '我的愿望' ? item.own : item.isPublic)),
)
const stats = computed(() =>
  wishes.state.value.reduce(
    (sum, item) => ({
      today: sum.today + (item.date === today ? item.likes : 0),
      week: sum.week + (item.date >= offsetDate(today, -6) ? item.likes : 0),
    }),
    { today: 0, week: 0 },
  ),
)
function saveWish() {
  if (body.value.trim().length < 4) return toast('至少写四个字。')
  const item = {
    id: makeId(),
    body: body.value.trim(),
    star: star.value,
    light: light.value,
    own: true,
    isPublic: isPublic.value,
    likes: 0,
    date: today,
  }
  if (wishes.write([item, ...wishes.state.value])) {
    body.value = ''
    isPublic.value = false
    box.value = '我的愿望'
  }
}
function updateWish(id: string, change: Partial<Wish>) {
  wishes.write(wishes.state.value.map((item) => (item.id === id ? { ...item, ...change } : item)))
}
function removeWish(item: Wish) {
  confirmAction(
    item.own ? '删除愿望' : '举报愿望',
    item.own ? '这条愿望会从本机删除。' : '提交举报，并从当前预览中隐藏这条愿望。',
    () => {
      wishes.write(wishes.state.value.filter((wish) => wish.id !== item.id))
      if (!item.own) toast('举报已记录到 Mock 环境。')
    },
  )
}

const pairs = [
  {
    left: 'E',
    right: 'I',
    title: '精力来源',
    questions: [
      ['长时间独处之后，我常想找人交流。', '结束密集交流后，我需要一段独处。'],
      ['和陌生人活动时，我容易先开口。', '我喜欢先观察周围再开口。'],
      ['想法与人讨论后，我会理解得更清楚。', '写下想法后，我更能确定自己的想法。'],
      ['休息时我偏向约人一起活动。', '休息时我偏向自己安排时间。'],
      ['遇到意外我会先找人聊聊。', '遇到意外我倾向静下来整理。'],
      ['多人对话常让我有精神。', '深入的一对一交流更适合我。'],
      ['我通常边说边完善自己的观点。', '我通常想好再表达观点。'],
    ],
  },
  {
    left: 'S',
    right: 'N',
    title: '信息偏好',
    questions: [
      ['我更注意事实与细节。', '我更注意联系与可能性。'],
      ['我喜欢先试一套成熟方法。', '我喜欢先比较新的方法。'],
      ['我常记得事物的实际样子。', '我常记得它给我的联想。'],
      ['明确的例子更能唤起我的兴趣。', '尚未解决的想法更能唤起我的兴趣。'],
      ['规划时我先盘点已有资源。', '规划时我先描绘可能的方向。'],
      ['我先弄清事情如何运转。', '我先想它将来还能怎么用。'],
      ['我倾向把问题拆成具体步骤。', '我倾向从整体模式理解问题。'],
    ],
  },
  {
    left: 'T',
    right: 'F',
    title: '判断依据',
    questions: [
      ['做决定时我先比较规则与证据。', '做决定时我先想受影响的人。'],
      ['我先检查理由是否一致。', '我先听对方的感受。'],
      ['给反馈时我优先指出实质问题。', '给反馈时我优先考虑对方如何接收。'],
      ['团队意见分歧时我先列不同方案。', '团队意见分歧时我先确认各人的诉求。'],
      ['我重视在相似场景下一致的标准。', '我重视照顾各人具体的处境。'],
      ['艰难决定中我先核对推理。', '艰难决定中我先核对自己珍视的事。'],
      ['意见不合时我习惯讨论论据。', '意见不合时我习惯先确认共同点。'],
    ],
  },
  {
    left: 'J',
    right: 'P',
    title: '行动节奏',
    questions: [
      ['我喜欢早点排完时间表。', '我喜欢给日程留出随机选择。'],
      ['确认计划后我更放松。', '保留几个可选方案时我更放松。'],
      ['我习惯把任务提前完成。', '我常在信息充分后集中完成。'],
      ['旅行时我预先安排主要路线。', '旅行时我到了再选路线。'],
      ['改变计划时我更关心如何善后。', '改变计划时我更关心新机会。'],
      ['有清楚的截止点对我有帮助。', '可以调整目标对我有帮助。'],
      ['我喜欢逐项结束正在做的事。', '我喜欢在几个主题之间切换。'],
    ],
  },
]
const questions = pairs.flatMap((pair) => pair.questions)
const test = localStore<{ answers: number[]; current: number; finished: boolean }>('mbti', {
  answers: [],
  current: 0,
  finished: false,
})
const testing = ref(test.state.value.answers.length > 0)
const result = computed(() =>
  pairs.map((pair, index) => ({
    ...pair,
    score: test.state.value.answers.slice(index * 7, index * 7 + 7).filter((item) => item === 0).length,
  })),
)
const type = computed(() => result.value.map((pair) => (pair.score >= 4 ? pair.left : pair.right)).join(''))
const allTypes = [
  'ISTJ',
  'ISFJ',
  'INFJ',
  'INTJ',
  'ISTP',
  'ISFP',
  'INFP',
  'INTP',
  'ESTP',
  'ESFP',
  'ENFP',
  'ENTP',
  'ESTJ',
  'ESFJ',
  'ENFJ',
  'ENTJ',
]
const showTypes = ref(false)
const selectedType = ref('')

function choose(value: number) {
  const { current, answers } = test.state.value
  const next = [...answers]
  next[current] = value
  test.write({ answers: next, current: Math.min(current + 1, 27), finished: current === 27 })
}
function restart() {
  if (test.write({ answers: [], current: 0, finished: false })) testing.value = true
}
function saveTest() {
  if (!test.state.value.finished) return
  const existing = type.value
  const item = createReading(
    {
      kind: 'mbti',
      title: 'MBTI · ' + existing,
      topic: '28 题偏好体验',
      summary: '本次表达偏好 · ' + existing,
      sections: result.value.map((axis) => ({
        title: axis.title,
        content: axis.left + ' ' + axis.score + ' / ' + axis.right + ' ' + (7 - axis.score),
      })),
      source: destination('divination', 'mbti'),
    },
    true,
  )
  if (item) go(destination('account', 'result', { id: item.id }))
}

const imagePath = ref('')
const sampleShown = ref(false)
const taking = ref(false)
const pictureInfo = ref('')
const timer = ref<ReturnType<typeof setTimeout>>()
onUnmounted(() => clearTimeout(timer.value))
const isHand = computed(() => props.view === 'palm')
function pickImage(source: 'album' | 'camera') {
  uni.chooseImage({
    count: 1,
    sourceType: [source],
    sizeType: ['compressed'],
    success: ({ tempFilePaths, tempFiles }) => {
      const file = Array.isArray(tempFiles) ? tempFiles[0] : undefined
      const path = Array.isArray(tempFilePaths) ? tempFilePaths[0] : tempFilePaths
      if (!path || (file?.size ?? 0) > 10 * 1024 * 1024) return toast('请选择 10 MB 以内的图片。')
      uni.getImageInfo({
        src: path,
        success: (info) => {
          imagePath.value = path
          pictureInfo.value =
            info.width >= 300 && info.height >= 300
              ? '画面可以进入示例流程。'
              : '建议选用清晰度至少为 300×300 的图片。'
          sampleShown.value = false
        },
        fail: () => toast('无法读取这张图片。'),
      })
    },
    fail: (error) => {
      if (!error.errMsg.includes('cancel')) toast('可改用相册或查看示例。')
    },
  })
}
function showSample() {
  if (taking.value) return
  taking.value = true
  timer.value = setTimeout(() => {
    taking.value = false
    sampleShown.value = true
  }, 320)
}
function saveImageReading() {
  const title = isHand.value ? '手相' : '面相'
  const item = createReading(
    {
      kind: props.view,
      title: title + '文化解读',
      topic: '传统文化条目',
      summary: isHand.value ? '掌纹、手型与线条的传统术语' : '面部轮廓与区域的传统术语',
      sections: [
        {
          title: '示例说明',
          content: isHand.value
            ? '文化词条示例：感情线用于描述掌上部可见纹路的形态。'
            : '文化词条示例：传统面相把额、眉、鼻等位置作为条目的组织方式。',
        },
      ],
      source: destination('divination', props.view),
    },
    true,
  )
  if (item) {
    imagePath.value = ''
    go(destination('account', 'result', { id: item.id }))
  }
}
</script>

<template>
  <view class="content-width stack">
    <template v-if="view === 'wishes'">
      <view class="split">
        <view class="panel stack">
          <text class="panel-head">写一个愿望</text>
          <textarea
            v-model="body"
            class="field area"
            maxlength="100"
            placeholder="写下一个想认真对待的愿望"
          />
          <view class="cols-2"
            ><SelectField
              v-model="star"
              label="星体"
              :options="['月亮', '金星', '木星', '织女星'].map((value) => ({ value, label: value }))" />
            <SelectField
              v-model="light"
              label="展示色"
              :options="['星雾紫', '玄夜金', '紫微光'].map((value) => ({ value, label: value }))"
          /></view>
          <view class="switch-row"
            ><text>公开到愿望墙</text
            ><AppSwitch label="公开到愿望墙" :checked="isPublic" @change="isPublic = $event"
          /></view>
          <view class="actions"
            ><button class="btn primary" :disabled="body.trim().length < 4" @tap="saveWish">保存愿望</button
            ><NavLink class="link" :to="destination('today', 'calendar')">查看星象时段 ›</NavLink></view
          >
        </view>
        <view class="panel stack"
          ><SectionHeading title="愿望回应" /><text class="muted"
            >今天接好运 {{ stats.today }} 次 · 本周 {{ stats.week }} 次</text
          >
          <view class="chips"
            ><button
              v-for="name in ['愿望墙', '我的愿望']"
              :key="name"
              class="chip"
              :class="{ selected: box === name }"
              @tap="box = name"
            >
              {{ name }}
            </button></view
          >
          <view v-for="item in wishesVisible" :key="item.id" class="panel stack">
            <text>{{ item.body }}</text
            ><text class="muted small"
              >{{ item.star }} · {{ item.light }} · {{ item.isPublic ? '公开' : '私有' }}</text
            >
            <view class="actions"
              ><button
                v-if="item.isPublic"
                class="btn"
                :disabled="item.liked"
                @tap="updateWish(item.id, { likes: item.likes + 1, liked: true })"
              >
                {{ item.liked ? '已接好运' : '接好运' }} {{ item.likes }}
              </button>
              <button
                v-if="item.own && item.isPublic"
                class="link"
                @tap="updateWish(item.id, { isPublic: false })"
              >
                撤回公开
              </button>
              <button class="link" @tap="removeWish(item)">{{ item.own ? '删除' : '举报' }}</button></view
            >
          </view>
          <text v-if="!wishesVisible.length" class="muted">这里还没有愿望。</text>
        </view>
      </view>
    </template>
    <template v-else-if="view === 'mbti'">
      <view v-if="!testing" class="panel stack"
        ><text class="panel-head">28 道行为偏好题</text
        ><text class="muted">选出更符合你平常习惯的一项。测试结果用于自我观察。</text
        ><button class="btn primary" @tap="restart">开始测试</button></view
      >
      <view v-else-if="!test.state.value.finished" class="panel stack">
        <text class="gold">第 {{ test.state.value.current + 1 }} / {{ questions.length }} 题</text
        ><text class="panel-head">哪一种情况更像你？</text>
        <button
          v-for="(option, index) in questions[test.state.value.current]"
          :key="option"
          class="btn"
          :class="{ primary: test.state.value.answers[test.state.value.current] === index }"
          @tap="choose(index)"
        >
          {{ option }}
        </button>
        <button
          class="link"
          :disabled="test.state.value.current === 0"
          @tap="test.write({ ...test.state.value, current: test.state.value.current - 1 })"
        >
          ‹ 上一题
        </button>
      </view>
      <view v-else class="panel stack">
        <text class="panel-head gold">{{ type }} · 本次偏好结果</text>
        <view v-for="axis in result" :key="axis.title" class="row"
          ><text>{{ axis.title }}</text
          ><text>{{ axis.left }} {{ axis.score }} · {{ axis.right }} {{ 7 - axis.score }}</text></view
        >
        <view class="actions"
          ><button class="btn primary" @tap="saveTest">保存报告</button
          ><button class="btn" @tap="restart">重新测试</button
          ><button class="btn" @tap="showTypes = !showTypes">16 型图鉴</button>
          <button
            v-if="account.state.value"
            class="btn"
            @tap="updateAccount({ mbti: type, publicMbti: true }) && toast('已写入公开资料')"
          >
            写入公开资料
          </button></view
        >
        <view v-if="showTypes" class="stack"
          ><view class="chips"
            ><button
              v-for="entry in allTypes"
              :key="entry"
              class="chip"
              :class="{ selected: entry === selectedType }"
              @tap="selectedType = entry"
            >
              {{ entry }}
            </button></view
          >
          <text v-if="selectedType" class="muted"
            >{{ selectedType }} ·
            {{ pairs.map((axis, i) => axis.title + ' ' + selectedType[i]).join(' / ') }}</text
          ></view
        >
      </view>
    </template>
    <template v-else>
      <view class="split"
        ><view class="panel stack">
          <text class="panel-head">{{ isHand ? '选择手掌照片' : '选择面部照片' }}</text>
          <text class="notice">当前照片只用于本机预览，不上传、不持久保存。解读使用固定文化条目。</text>
          <text class="muted">光线充足时正对镜头，画面清晰即可。也可以直接查看示例。</text>
          <image v-if="imagePath" class="image-preview" :src="imagePath" mode="aspectFit" />
          <text v-if="pictureInfo && imagePath" class="small">{{ pictureInfo }}</text>
          <view class="actions"
            ><button class="btn" @tap="pickImage('album')">从相册选图</button
            ><button class="btn" @tap="pickImage('camera')">拍照</button
            ><button v-if="imagePath" class="link" @tap="imagePath = ''">移除原图</button></view
          > </view
        ><view class="panel stack"
          ><text class="panel-head">文化解读</text>
          <button class="btn primary" :disabled="taking" @tap="showSample">
            {{ taking ? '正在准备条目…' : '查看示例解读' }}
          </button>
          <template v-if="sampleShown"
            ><text>{{
              isHand
                ? '示例：从掌上部的线条，认识感情线这一传统术语。'
                : '示例：按额、眉、鼻划分位置，了解不同区域的传统称谓。'
            }}</text>
            <button class="btn" @tap="saveImageReading">保存这份示例</button></template
          >
        </view></view
      >
    </template>
  </view>
</template>
