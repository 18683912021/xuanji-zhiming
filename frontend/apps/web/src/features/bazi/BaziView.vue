<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import { useExperiences } from '@/features/experiences/store'
import { calculateBazi, type Calendar } from './chart'

const router = useRouter()
const experiences = useExperiences()
const mode = ref<Calendar>('solar')
const solardate = ref('')
const lunardate = ref('')
const time = ref('')
const city = ref('')
const leap = ref(false)
const unknown = ref(false)
const lateZi = ref(false)
const error = ref('')
const submitted = ref(false)

function generate() {
  if (submitted.value) return
  error.value = ''
  const chart = calculateBazi({
    calendar: mode.value,
    date: mode.value === 'solar' ? solardate.value : lunardate.value,
    time: time.value,
    leapMonth: leap.value,
    timeUnknown: unknown.value,
    lateZi: lateZi.value,
  })
  if (!chart.ok) {
    error.value = chart.error
    return
  }

  submitted.value = true
  const birthTime = unknown.value
    ? '时辰不详，前三柱以输入日期正午为参考'
    : `出生时刻 ${time.value}`
  const id = experiences.create({
    kind: 'bazi',
    question: [city.value.trim(), birthTime].filter(Boolean).join(' · '),
    value: chart.reading,
  })
  void router.replace({ name: 'result', params: { id } })
}
</script>

<template>
  <article class="page-shell narrow">
    <PageTitle title="八字命盘" description="输入出生日期与当地时刻，查看四柱、五行和藏干。" />
    <form class="panel form-stack" @submit.prevent="generate">
      <fieldset>
        <legend>出生历法</legend>
        <div class="choice-group">
          <label class="choice"><input v-model="mode" type="radio" value="solar" /> 公历</label>
          <label class="choice"><input v-model="mode" type="radio" value="lunar" /> 农历</label>
          <label v-if="mode === 'lunar'" class="choice"
            ><input v-model="leap" type="checkbox" /> 闰月</label
          >
        </div>
      </fieldset>
      <div class="form-cols">
        <label v-if="mode === 'solar'" class="form-field">
          <span>公历出生日期</span
          ><input v-model="solardate" type="date" min="1900-01-01" max="2099-12-31" required />
        </label>
        <label v-else class="form-field">
          <span>农历出生日期</span
          ><input
            v-model="lunardate"
            placeholder="例如 1990-05-14"
            inputmode="text"
            maxlength="10"
            required
          />
        </label>
        <label class="form-field">
          <span>出生时间</span
          ><input v-model="time" type="time" :disabled="unknown" :required="!unknown" />
        </label>
      </div>
      <div class="choice-group">
        <label class="choice"><input v-model="unknown" type="checkbox" /> 时辰不详</label>
        <label class="choice"
          ><input v-model="lateZi" type="checkbox" :disabled="unknown" /> 晚子时按次日换日</label
        >
      </div>
      <label class="form-field">
        <span>出生城市（可选）</span
        ><input v-model="city" maxlength="36" placeholder="例如杭州，用于标记这份命盘" />
      </label>
      <p class="label-help">
        按输入的当地钟表时刻排盘。时辰不详时仅显示三柱，节气临界日需补充准确时间。
      </p>
      <p v-if="error" class="field-error" role="alert">{{ error }}</p>
      <div class="action-row">
        <button class="button button-gold" :disabled="submitted">开始排盘</button>
      </div>
    </form>
  </article>
</template>
