import { readLocal, writeLocal } from '@/shared/storage'
import type { Conversation, Experience } from './model'

const resultsKey = 'xuanji:v1:results'
const conversationsKey = 'xuanji:v1:conversations'

export function loadResults(): Experience[] {
  const results = readLocal<Experience[]>(resultsKey, [])
  return Array.isArray(results) ? results : []
}

export function loadConversations(): Conversation[] {
  const conversations = readLocal<Conversation[]>(conversationsKey, [])
  return Array.isArray(conversations) ? conversations : []
}

export function saveResults(results: Experience[]): boolean {
  return writeLocal(resultsKey, results)
}

export function saveConversations(conversations: Conversation[]): boolean {
  return writeLocal(conversationsKey, conversations)
}
