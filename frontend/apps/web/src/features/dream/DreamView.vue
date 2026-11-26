<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PageTitle from '@/shared/components/PageTitle.vue'
import { useExperiences } from '@/features/experiences/store'

const router = useRouter()
const experiences = useExperiences()
const dream = ref('')
const mood = ref('暂不标记')
const done = ref(false)
function saveDream() {
  if (!dream.value.trim() || done.value) return
  done.value = true
  const id = experiences.create({
    kind: 'dream',
    question: dream.value.trim(),
    value: { mood: mood.value },
  })
  experiences.save(id)
  void router.replace({ name: 'result', params: { id } })
}
</script>
<template>
  <article class="page-shell narrow">
    <PageTitle title="AI 解梦" description="记录梦境的场景、情绪和醒来后仍记得的细节。" />
    <form class="panel form-stack" @submit.prevent="saveDream">
      <p class="notice">梦境目前保存在本机。AI 解读将在服务接入后可用。</p>
      <label class="form-field"
        ><span>梦里的场景</span
        ><textarea
          v-model="dream"
          maxlength="1000"
          required
          placeholder="例如，我沿着一条山路走，天色慢慢变暗。"
        />
      </label>
      <label class="form-field"
        ><span>醒来时的感受</span
        ><select v-model="mood">
          <option>暂不标记</option>
          <option>平静</option>
          <option>好奇</option>
          <option>紧张</option>
          <option>欣喜</option>
          <option>困惑</option>
        </select></label
      >
      <div class="action-row">
        <button class="button button-gold" :disabled="done || !dream.trim()">保存梦境</button>
      </div>
    </form>
  </article>
</template>
