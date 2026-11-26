<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import { deal } from './tarot'
import { useExperiences } from '@/features/experiences/store'

const router = useRouter()
const experiences = useExperiences()
const question = ref('')
const spread = ref(1)
const available = ref(deal())
const selected = ref<number[]>([])
const submitted = ref(false)
const count = computed(() => selected.value.length)

function choose(index: number) {
  const current = selected.value.indexOf(index)
  if (current >= 0) selected.value.splice(current, 1)
  else if (selected.value.length < spread.value) selected.value.push(index)
}
function startNewDeck() {
  available.value = deal()
  selected.value = []
}
function reveal(automatic = false) {
  if (submitted.value) return
  const items = automatic
    ? available.value.slice(0, spread.value)
    : selected.value.map((index) => available.value[index]!)
  if (items.length !== spread.value) return
  submitted.value = true
  const positions = spread.value === 1 ? ['此刻'] : ['过去', '现在', '未来']
  const id = experiences.create({
    kind: 'tarot',
    question: question.value.trim(),
    value: { cards: items.map((card, index) => ({ ...card, position: positions[index]! })) },
  })
  void router.replace({ name: 'result', params: { id } })
}
</script>

<template>
  <article class="page-shell">
    <PageTitle title="塔罗占卜" description="选一张牌看当下，或用三张牌回顾一段经历。" />
    <div class="split">
      <section class="panel form-stack">
        <label class="form-field">
          <span>我想问</span>
          <textarea v-model="question" maxlength="160" placeholder="可以先写下你的问题" />
        </label>
        <fieldset>
          <legend>牌阵</legend>
          <div class="choice-group">
            <label class="choice"
              ><input v-model="spread" type="radio" :value="1" @change="startNewDeck" />
              单张牌</label
            >
            <label class="choice"
              ><input v-model="spread" type="radio" :value="3" @change="startNewDeck" /> 过去 · 现在
              · 未来</label
            >
          </div>
        </fieldset>
        <p class="label-help">本版使用 22 张大阿尔卡那，含正位与逆位。</p>
      </section>
      <section class="panel cards-stage">
        <h2>选择 {{ spread }} 张牌</h2>
        <p class="muted" aria-live="polite">已选 {{ count }} / {{ spread }}</p>
        <div class="tarot-deck">
          <button
            v-for="(_, index) in available"
            :key="index"
            type="button"
            class="tarot-back"
            :aria-label="`第 ${index + 1} 张牌`"
            :aria-pressed="selected.includes(index)"
            @click="choose(index)"
          >
            <span aria-hidden="true">✧</span>
            <span v-if="selected.includes(index)" class="card-order" aria-hidden="true">{{
              selected.indexOf(index) + 1
            }}</span>
          </button>
        </div>
        <div class="action-row">
          <button
            type="button"
            class="button button-gold"
            :disabled="count !== spread || submitted"
            @click="reveal()"
          >
            翻开所选牌
          </button>
          <button
            type="button"
            class="button button-outline"
            :disabled="submitted"
            @click="reveal(true)"
          >
            随机抽牌
          </button>
        </div>
      </section>
    </div>
  </article>
</template>

<style scoped src="./tarot.css"></style>
