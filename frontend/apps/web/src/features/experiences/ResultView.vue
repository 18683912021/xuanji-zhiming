<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import BaziResult from '@/features/bazi/BaziResult.vue'
import LiuyaoResult from '@/features/liuyao/LiuyaoResult.vue'
import TarotResult from '@/features/tarot/TarotResult.vue'
import { dateLabel } from '@/shared/date'
import { kindNames } from './model'
import { useExperiences } from './store'

const route = useRoute()
const router = useRouter()
const experiences = useExperiences()
const id = computed(() => String(route.params.id))
const result = computed(() => experiences.results.find((value) => value.id === id.value))
const related = computed(() =>
  experiences.conversations.filter((item) => item.experienceId === id.value),
)
const note = computed({
  get: () => result.value?.note ?? '',
  set: (value: string) => experiences.updateNote(id.value, value),
})
function ask() {
  const conversation = experiences.openConversation(id.value)
  if (conversation) void router.push({ name: 'conversation', params: { id: conversation } })
}
</script>

<template>
  <article v-if="result" class="page-shell">
    <PageTitle
      :title="kindNames[result.kind] + (result.kind === 'dream' ? '' : ' · 结果')"
      :description="result.question || dateLabel(result.createdAt)"
    />
    <div class="stack">
      <TarotResult v-if="result.kind === 'tarot'" :reading="result.value.cards" />
      <BaziResult v-else-if="result.kind === 'bazi'" :reading="result.value" />
      <LiuyaoResult v-else-if="result.kind === 'liuyao'" :lines="result.value.lines" />
      <section v-else-if="result.kind === 'oracle'" class="panel stack">
        <h2>{{ result.value.title }}</h2>
        <p class="gold">{{ result.value.verse }}</p>
        <p>{{ result.value.reading }}</p>
        <p class="status-label">来源 · 玄机知命原创签文</p>
      </section>
      <section v-else class="panel stack">
        <h2>醒来时的感受</h2>
        <p>{{ result.value.mood }}</p>
        <p class="notice">梦境记录可以回看或整理成问题。AI 解读将在服务接入后可用。</p>
      </section>
      <section class="panel form-stack">
        <label class="form-field"
          ><span>我的笔记</span>
          <textarea v-model="note" maxlength="600" placeholder="记录现在的想法，方便之后回看" />
        </label>
        <div class="action-row">
          <button class="button button-gold" type="button" @click="ask">
            {{ result.kind === 'dream' ? '整理我的问题' : '开启解读对话' }}
          </button>
          <button
            class="button button-outline"
            type="button"
            :disabled="result.saved"
            @click="experiences.save(id)"
          >
            {{ result.saved ? '已保存到本机' : '保存本次体验' }}
          </button>
          <RouterLink class="button button-outline" :to="{ name: result.kind }"
            >再体验一次</RouterLink
          >
        </div>
        <p v-if="experiences.storageNotice" class="field-error" role="status">
          {{ experiences.storageNotice }}
        </p>
        <div v-if="related.length" class="choice-group" aria-label="已关联会话">
          <RouterLink
            v-for="(chat, index) in related"
            :key="chat.id"
            class="button button-outline"
            :to="`/conversation/${chat.id}`"
            >回看对话 {{ related.length - index }}</RouterLink
          >
        </div>
      </section>
    </div>
  </article>
  <article v-else class="page-shell narrow">
    <PageTitle title="找不到这条结果" description="这条结果可能已删除，或保存在其他设备。" />
    <RouterLink class="button button-gold" to="/records">查看本机记录</RouterLink>
  </article>
</template>
