<script setup lang="ts">
import { ref } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import { kindNames } from './model'
import { useExperiences } from './store'
import { dateLabel } from '@/shared/date'

const experiences = useExperiences()
const pending = ref('')

function confirmRemoval(id: string) {
  experiences.remove(id)
  pending.value = ''
}
</script>
<template>
  <article class="page-shell narrow">
    <PageTitle title="体验记录" description="回看保存于此浏览器的结果、笔记和对话。" />
    <p v-if="experiences.storageNotice" role="status" class="field-error">
      {{ experiences.storageNotice }}
    </p>
    <div v-if="experiences.saved.length" class="stack">
      <section v-for="item in experiences.saved" :key="item.id" class="panel">
        <div class="record-row">
          <div>
            <RouterLink :to="{ name: 'result', params: { id: item.id } }">
              <h2>{{ item.question || kindNames[item.kind] }}</h2>
            </RouterLink>
            <p class="muted">{{ kindNames[item.kind] }} · {{ dateLabel(item.createdAt) }}</p>
          </div>
          <button
            class="button button-outline"
            type="button"
            v-if="pending !== item.id"
            @click="pending = item.id"
          >
            删除
          </button>
        </div>
        <div v-if="pending === item.id" class="form-stack">
          <p class="field-error">删除本条记录及关联对话？</p>
          <div class="action-row">
            <button
              class="button button-gold"
              type="button"
              @click="confirmRemoval(item.id)"
            >
              确认删除
            </button>
            <button class="button button-outline" type="button" @click="pending = ''">取消</button>
          </div>
        </div>
      </section>
    </div>
    <section v-else class="panel">
      <h2>还没有保存的体验</h2>
      <p class="muted">抽一张塔罗，保存后可以在这里找到它。</p>
      <div class="action-row">
        <RouterLink class="button button-gold" to="/tarot">去抽塔罗</RouterLink>
      </div>
    </section>
  </article>
</template>

<style scoped>
.record-row {
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
}
.record-row > div:first-child {
  min-width: 0;
}
.record-row a:hover {
  color: var(--gold);
}
</style>
