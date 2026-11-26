<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import YaoLines from './YaoLines.vue'
import { castCoins, yaoLabels, yaoNames } from './liuyao'
import type { Yao } from './liuyao'
import { clearDraft, loadDraft, saveDraft } from './draft'
import { useExperiences } from '@/features/experiences/store'

const router = useRouter()
const experiences = useExperiences()
const draft = loadDraft()
const question = ref(draft.question)
const mode = ref(draft.mode)
const lines = ref(draft.lines)
const manual = ref(draft.manual)
const coins = ref<number[]>([])
const done = ref(false)

watch(
  [question, lines, mode, manual],
  () => {
    if (done.value) return
    saveDraft({
      question: question.value,
      lines: lines.value,
      mode: mode.value,
      manual: manual.value,
    })
  },
  { deep: true },
)

function cast() {
  if (lines.value.length === 6) return
  const result = castCoins()
  coins.value = result.coins
  lines.value.push(result.value)
}
function resetCast() {
  lines.value = []
  coins.value = []
}
function submit() {
  const selected =
    mode.value === 'cast' ? lines.value : manual.value.filter((n): n is Yao => n !== '')
  if (selected.length !== 6 || done.value) return
  done.value = true
  const id = experiences.create({
    kind: 'liuyao',
    question: question.value.trim(),
    value: { lines: [...selected] },
  })
  clearDraft()
  void router.replace({ name: 'result', params: { id } })
}
</script>

<template>
  <article class="page-shell">
    <PageTitle title="六爻问事" description="按初爻至上爻投掷或录入，查看本卦与变卦。" />
    <div class="split">
      <section class="panel form-stack">
        <label class="form-field"
          ><span>我想问</span
          ><textarea v-model="question" maxlength="160" placeholder="写下一件具体的事" />
        </label>
        <fieldset>
          <legend>起卦方式</legend>
          <div class="choice-group">
            <label class="choice"
              ><input v-model="mode" type="radio" value="cast" /> 三钱起卦</label
            >
            <label class="choice"
              ><input v-model="mode" type="radio" value="manual" /> 手动录入</label
            >
          </div>
        </fieldset>
        <div v-if="mode === 'manual'" class="form-cols">
          <div v-for="(name, index) in yaoNames" :key="name" class="form-field">
            <label :for="'manual-yao-' + index">{{ name }}</label>
            <select :id="'manual-yao-' + index" v-model="manual[index]">
              <option value="">请选择</option>
              <option v-for="n in [6, 7, 8, 9] as const" :key="n" :value="n">
                {{ yaoLabels[n] }}
              </option>
            </select>
          </div>
        </div>
      </section>
      <section class="panel stack">
        <h2>{{ mode === 'cast' ? '本次起卦' : '核对录入' }}</h2>
        <YaoLines
          :lines="mode === 'cast' ? lines : manual.map((n) => n || undefined)"
          show-moving
        />
        <p v-if="mode === 'cast' && coins.length" class="muted" aria-live="polite">
          本次三钱：{{ coins.map((coin) => (coin === 3 ? '正' : '反')).join(' · ') }}
        </p>
        <div class="action-row" v-if="mode === 'cast'">
          <button v-if="lines.length < 6" type="button" class="button button-gold" @click="cast">
            投掷{{ yaoNames[lines.length] }}
          </button>
          <button v-else type="button" class="button button-gold" @click="submit">查看卦象</button>
          <button
            v-if="lines.length"
            type="button"
            class="button button-outline"
            @click="resetCast"
          >
            重新起卦
          </button>
        </div>
        <div class="action-row" v-else>
          <button
            type="button"
            class="button button-gold"
            :disabled="manual.includes('')"
            @click="submit"
          >
            查看卦象
          </button>
        </div>
      </section>
    </div>
  </article>
</template>
