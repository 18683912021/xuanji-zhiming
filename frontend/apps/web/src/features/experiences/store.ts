import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { Conversation, Experience, NewExperience } from './model'
import { loadConversations, loadResults, saveConversations, saveResults } from './repository'

function createId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(12)), (value) =>
    value.toString(16).padStart(2, '0'),
  ).join('')
}

export const useExperiences = defineStore('experiences', () => {
  const results = ref(loadResults())
  const conversations = ref(loadConversations())
  const resultsWriteFailed = ref(false)
  const conversationsWriteFailed = ref(false)

  const saved = computed(() => results.value.filter((item) => item.saved))
  const storageNotice = computed(() =>
    resultsWriteFailed.value || conversationsWriteFailed.value
      ? '浏览器无法保存到本机，刷新后可能丢失本次数据。'
      : '',
  )

  function commitResults(next: Experience[]) {
    results.value = next
    resultsWriteFailed.value = !saveResults(next)
  }

  function commitConversations(next: Conversation[]) {
    conversations.value = next
    conversationsWriteFailed.value = !saveConversations(next)
  }

  function create(input: NewExperience) {
    const item: Experience = {
      ...input,
      id: createId(),
      createdAt: new Date().toISOString(),
      saved: false,
      note: '',
    }
    commitResults([item, ...results.value])
    return item.id
  }

  function updateResult(id: string, fields: Partial<Pick<Experience, 'note' | 'saved'>>) {
    if (!results.value.some((item) => item.id === id)) return
    commitResults(results.value.map((item) => (item.id === id ? { ...item, ...fields } : item)))
  }

  function save(id: string) {
    updateResult(id, { saved: true })
  }

  function updateNote(id: string, note: string) {
    updateResult(id, { note, saved: true })
  }

  function remove(id: string) {
    commitConversations(conversations.value.filter((item) => item.experienceId !== id))
    commitResults(results.value.filter((item) => item.id !== id))
  }

  function openConversation(experienceId: string) {
    const result = results.value.find((item) => item.id === experienceId)
    if (!result) return
    if (!result.saved || resultsWriteFailed.value) save(experienceId)
    const item: Conversation = {
      id: createId(),
      experienceId,
      createdAt: new Date().toISOString(),
      questions: [],
    }
    commitConversations([item, ...conversations.value])
    return item.id
  }

  function addQuestion(id: string, question: string) {
    const text = question.trim()
    if (!text || !conversations.value.some((item) => item.id === id)) return
    commitConversations(
      conversations.value.map((item) =>
        item.id === id ? { ...item, questions: [...item.questions, text] } : item,
      ),
    )
  }

  return {
    results,
    saved,
    conversations,
    storageNotice,
    create,
    save,
    updateNote,
    remove,
    openConversation,
    addQuestion,
  }
})
