<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import { useExperiences } from '@/features/experiences/store'

const router = useRouter()
const experiences = useExperiences()
const theme = ref('当下选择')
const question = ref('')
const done = ref(false)
const oracles = [
  {
    title: '云开见月',
    verse: '云行山未动，静水自明月。',
    reading: '先区分已经知道的事与仍需验证的猜测。写下一项能在今天核实的线索。',
  },
  {
    title: '松间缓行',
    verse: '松间有微径，缓步到清泉。',
    reading: '把大问题拆成较小的行动，试着完成一个低成本、可复盘的步骤。',
  },
  {
    title: '潮退见岸',
    verse: '静候一潮落，方知岸几重。',
    reading: '情绪变化时先记下感受。等信息齐备，再为选择设一个复核时间。',
  },
  {
    title: '晨光入窗',
    verse: '不待长夜尽，微光已入窗。',
    reading: '留意已经发生的小变化。或许身边有一个可用资源，适合先去确认。',
  },
]
function draw() {
  if (done.value) return
  done.value = true
  const value = oracles[Math.floor(Math.random() * oracles.length)]!
  const id = experiences.create({
    kind: 'oracle',
    question: question.value.trim() || theme.value,
    value,
  })
  void router.replace({ name: 'result', params: { id } })
}
</script>
<template>
  <article class="page-shell narrow">
    <PageTitle title="占卜问签" description="带着一个处境，抽取一则原创签文。" />
    <form class="panel form-stack" @submit.prevent="draw">
      <label class="form-field"
        ><span>主题</span
        ><select v-model="theme">
          <option>当下选择</option>
          <option>人际关系</option>
          <option>学习工作</option>
          <option>自我观察</option>
        </select></label
      >
      <label class="form-field"
        ><span>我想问（可选）</span
        ><textarea v-model="question" maxlength="160" placeholder="把你关心的事写下来" />
      </label>
      <div class="action-row">
        <button class="button button-gold" :disabled="done">抽一支签</button>
      </div>
    </form>
  </article>
</template>
