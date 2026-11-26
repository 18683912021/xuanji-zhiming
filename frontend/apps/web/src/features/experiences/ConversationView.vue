<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import { kindNames } from './model'
import { useExperiences } from './store'
import { dateLabel } from '@/shared/date'

const route = useRoute()
const router = useRouter()
const experiences = useExperiences()
const conversation = computed(() =>
  experiences.conversations.find((item) => item.id === route.params.id),
)
const result = computed(() =>
  experiences.results.find((item) => item.id === conversation.value?.experienceId),
)
const asked = ref('')
const status = ref('')

function saveQuestion() {
  if (!conversation.value || !asked.value.trim()) return
  experiences.addQuestion(conversation.value.id, asked.value)
  asked.value = ''
  status.value = '问题已存到本机。'
}
function newConversation() {
  if (!result.value) return
  const id = experiences.openConversation(result.value.id)
  if (id) void router.push({ name: 'conversation', params: { id } })
}
</script>
<template>
  <article class="page-shell narrow">
    <PageTitle title="解读对话" description="每条会话单独保存，可关联同一份体验结果。" />
    <template v-if="conversation && result">
      <div class="stack">
        <section class="panel">
          <h2>关联资料</h2>
          <RouterLink class="gold" :to="`/result/${result.id}`"
            >{{ kindNames[result.kind] }} · {{ dateLabel(result.createdAt) }}</RouterLink
          >
          <p v-if="result.question" class="muted">{{ result.question }}</p>
        </section>
        <section class="panel">
          <p class="notice">AI 服务待接入。你可以先保留问题，或打开原结果查看牌义与盘面。</p>
          <ul v-if="conversation.questions.length" class="chat-messages">
            <li
              v-for="(question, index) in conversation.questions"
              :key="index"
              class="chat-message"
            >
              <p>{{ question }}</p>
            </li>
          </ul>
          <form class="form-stack question-form" @submit.prevent="saveQuestion">
            <label class="form-field"
              ><span>想进一步了解什么？</span
              ><textarea
                v-model="asked"
                maxlength="600"
                placeholder="例如，为什么这张牌出现在现在的位置？"
              />
            </label>
            <div class="action-row">
              <button class="button button-gold" :disabled="!asked.trim()">保存问题</button>
              <button class="button button-outline" type="button" @click="newConversation">
                开启独立会话
              </button>
            </div>
            <p class="status-label" role="status">{{ experiences.storageNotice || status }}</p>
          </form>
        </section>
      </div>
    </template>
    <section class="panel" v-else>
      <p>找不到这份会话或它关联的体验。</p>
      <RouterLink class="gold" to="/records">回到体验记录</RouterLink>
    </section>
  </article>
</template>

<style scoped>
.chat-messages {
  display: grid;
  gap: 12px;
  margin: 16px 0;
  padding: 0;
  list-style: none;
}
.chat-message {
  width: fit-content;
  max-width: 95%;
  justify-self: end;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 11px 13px;
  background: var(--raised);
}
.chat-message > p {
  white-space: pre-wrap;
}
.question-form {
  margin-top: 16px;
}
</style>
