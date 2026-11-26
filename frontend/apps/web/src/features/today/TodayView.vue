<script setup lang="ts">
import { computed, ref } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'

const zodiac = [
  ['白羊座', '3.21 – 4.19', '火象', '把很想开始的事拆成一个能在今天完成的步骤。'],
  ['金牛座', '4.20 – 5.20', '土象', '留意今天有哪些稳定的安排值得保留。'],
  ['双子座', '5.21 – 6.21', '风象', '把最感兴趣的新线索写下来，再选一条查证。'],
  ['巨蟹座', '6.22 – 7.22', '水象', '给自己留一点能从忙碌中恢复的时间。'],
  ['狮子座', '7.23 – 8.22', '火象', '分享一项你做得不错的事，也听听别人的观察。'],
  ['处女座', '8.23 – 9.22', '土象', '整理一个经常卡住的步骤，从最小的细节开始。'],
  ['天秤座', '9.23 – 10.23', '风象', '遇到两种偏好时，先问自己最想保留哪一点。'],
  ['天蝎座', '10.24 – 11.22', '水象', '选一件在意的事深入理解，给其余任务留到下一次。'],
  ['射手座', '11.23 – 12.21', '火象', '尝试一次小范围的新体验，记下实际感受到的变化。'],
  ['摩羯座', '12.22 – 1.19', '土象', '回看一个长期目标，给本周的进度设一个可衡量的标记。'],
  ['水瓶座', '1.20 – 2.18', '风象', '选一个熟悉的问题，用另一种方式把它讲给自己听。'],
  ['双鱼座', '2.19 – 3.20', '水象', '给自己的感受起个名字，再观察它和当下情况有什么联系。'],
] as const
const current = ref(0)
const cycle = ref<'today' | 'week' | 'month'>('today')
const sign = computed(() => zodiac[current.value]!)
const period = computed(() => {
  const now = new Date()
  const short = new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' })
  if (cycle.value === 'today') return short.format(now)
  if (cycle.value === 'month')
    return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long' }).format(now)
  const first = new Date(now)
  first.setDate(now.getDate() - ((now.getDay() + 6) % 7))
  const last = new Date(first)
  last.setDate(first.getDate() + 6)
  return `${short.format(first)} – ${short.format(last)}`
})
const reflection = {
  today: '记下今天的一项观察，晚上可以回来对照当时的想法。',
  week: '选一个主题贯穿本周，在周末回顾最清楚的一处变化。',
  month: '先定下这个月想观察的方向，每周留一条简短记录。',
}
</script>
<template>
  <article class="page-shell">
    <PageTitle title="星座运势" description="选择一个星座，阅读按周期组织的编辑观察主题。" />
    <div class="split">
      <section class="panel">
        <h2>十二星座</h2>
        <div class="choice-group">
          <button
            v-for="(item, index) in zodiac"
            :key="item[0]"
            type="button"
            class="button"
            :class="current === index ? 'button-gold' : 'button-outline'"
            :aria-pressed="current === index"
            @click="current = index"
          >
            {{ item[0] }}
          </button>
        </div>
      </section>
      <section class="panel stack" aria-live="polite">
        <div>
          <h2>{{ sign[0] }}</h2>
          <p class="muted">{{ sign[1] }} · {{ sign[2] }}</p>
        </div>
        <fieldset>
          <legend>查看周期</legend>
          <div class="choice-group">
            <label class="choice"><input v-model="cycle" type="radio" value="today" /> 今日</label>
            <label class="choice"><input v-model="cycle" type="radio" value="week" /> 本周</label>
            <label class="choice"><input v-model="cycle" type="radio" value="month" /> 本月</label>
          </div>
        </fieldset>
        <div>
          <span class="status-label">{{ period }}</span>
          <p>{{ sign[3] }}</p>
        </div>
        <p class="notice">{{ reflection[cycle] }}</p>
      </section>
    </div>
  </article>
</template>
