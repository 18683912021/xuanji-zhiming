/// <reference types="vite/client" />

import { shallowRef, watch, type ShallowRef } from 'vue'
import { localStore, readStorage } from './storage'

export const live = import.meta.env.VITE_XUANJI_MODE !== 'mock'
const origin = (import.meta.env.VITE_XUANJI_API_ORIGIN || '').replace(/\/$/, '')
const tokenKey = 'xuanji:client:api-token'

export interface Identity {
  id: string
  display_name: string
  username: string | null
  email: string | null
  is_guest: boolean
  wechat_linked: boolean
  password_set: boolean
  is_admin: boolean
  details?: Record<string, unknown>
}
interface SessionResult {
  account: Identity
  access_token: string | null
  handoff_reading_id?: string | null
}
export const identity = shallowRef<Identity | null>(null)
let initialization: Promise<void> | undefined
let guestRequest: Promise<Identity> | undefined

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message)
  }
}

export function apiMessage(error: unknown) {
  return error instanceof ApiError ? error.message : '服务暂时不可用，请稍后再试。'
}

export function requestId(): string {
  // Unpredictability is not required for a client idempotency identifier.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (part) => {
    const n = Math.floor(Math.random() * 16)
    return (part === 'x' ? n : 8 + (n & 3)).toString(16)
  })
}

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE'
interface RequestOptions { method?: Method; body?: object; key?: string }

function endpoint(path: string) {
  // #ifdef MP-WEIXIN
  if (!origin)
    throw new ApiError(0, 'missing_origin', '请配置小程序的 HTTPS API 地址。')
  // #endif
  return origin + '/api/v1' + path
}

function headers(options: RequestOptions, stream = false) {
  const result: Record<string, string> = {
    Accept: stream ? 'text/event-stream' : 'application/json',
  }
  if (options.body) result['Content-Type'] = 'application/json'
  if (options.key) result['Idempotency-Key'] = options.key
  // #ifdef MP-WEIXIN
  const token = readStorage(tokenKey, '')
  if (token) result.Authorization = 'Bearer ' + token
  // #endif
  return result
}

function failure(status: number, body: unknown): ApiError {
  const detail = (body as { error?: { message?: string; code?: string } } | null)?.error
  return new ApiError(status, detail?.code || 'request_failed', detail?.message || '服务请求失败，请稍后再试。')
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = endpoint(path)
  // #ifdef H5
  {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 15000)
    try {
      const res = await fetch(url, {
        method: options.method || 'GET', headers: headers(options), credentials: 'include',
        body: options.body && JSON.stringify(options.body), signal: controller.signal,
      })
      if (res.status === 204) return undefined as T
      const data = await res.json().catch(() => null)
      if (!res.ok || data === null) throw failure(res.status, data)
      return data as T
    } finally {
      clearTimeout(timer)
    }
  }
  // #endif
  // #ifdef MP-WEIXIN
  return new Promise<T>((resolve, reject) => {
    uni.request({
      url, method: options.method || 'GET', data: options.body, header: headers(options),
      timeout: 15000,
      success: ({ statusCode, data }) => {
        if (statusCode >= 200 && statusCode < 300) resolve(data as T)
        else reject(failure(statusCode, data))
      },
      fail: () => reject(failure(0, null)),
    })
  })
  // #endif
}

export interface StreamHandle {
  done: Promise<void>
  abort: () => void
}
export function streamPost<T>(path: string, body: object, onEvent: (name: string, data: T) => void): StreamHandle {
  const url = endpoint(path)
  const options: RequestOptions = { method: 'POST', body }
  let buffer = ''
  let gotResult = false
  function consume(chunk: string) {
    buffer += chunk
    for (;;) {
      const boundary = /\r?\n\r?\n/.exec(buffer)
      if (!boundary) return
      const frame = buffer.slice(0, boundary.index)
      buffer = buffer.slice(boundary.index + boundary[0].length)
      const event = frame.split(/\r?\n/).find((line) => line.startsWith('event:'))?.slice(6).trim()
      const data = frame.split(/\r?\n/).filter((line) => line.startsWith('data:')).map((line) => line.slice(5).trimStart())
      if (data.length) {
        if (event === 'result') gotResult = true
        onEvent(event || 'message', JSON.parse(data.join('\n')) as T)
      }
    }
  }
  function expectResult() {
    if (!gotResult) throw new ApiError(0, 'stream_interrupted', '消息连接已中断，稍后可重试。')
  }
  // #ifdef H5
  {
    const controller = new AbortController()
    const done = (async () => {
      const response = await fetch(url, {
        method: 'POST', credentials: 'include', headers: headers(options, true),
        body: JSON.stringify(body), signal: controller.signal,
      })
      if (!response.ok) throw failure(response.status, await response.json().catch(() => null))
      const reader = response.body?.getReader()
      if (!reader) consume(await response.text())
      else {
        const decoder = new TextDecoder()
        try {
          for (;;) {
            const chunk = await reader.read()
            if (chunk.done) break
            consume(decoder.decode(chunk.value, { stream: true }))
          }
          consume(decoder.decode())
        } finally {
          reader.releaseLock()
        }
      }
      expectResult()
    })()
    return { done, abort: () => controller.abort() }
  }
  // #endif
  // #ifdef MP-WEIXIN
  type ChunkedTask = ReturnType<typeof uni.request> & {
    onChunkReceived?: (listener: (chunk: { data: ArrayBuffer }) => void) => void
  }
  let task: ChunkedTask
  let sawChunks = false
  let encodedLine = ''
  const done = new Promise<void>((resolve, reject) => {
    task = uni.request({
      url, method: 'POST', data: body, header: headers(options, true), dataType: 'text', timeout: 110000,
      enableChunked: true,
      success: ({ statusCode, data }) => {
        if (statusCode < 200 || statusCode >= 300) {
          let detail: unknown = data
          if (typeof data === 'string') {
            try { detail = JSON.parse(data) } catch { detail = null }
          }
          reject(failure(statusCode, detail))
          return
        }
        try {
          if (!sawChunks) consume(String(data))
          expectResult()
          resolve()
        } catch (error) {
          reject(error)
        }
      },
      fail: () => reject(failure(0, null)),
    })
    task.onChunkReceived?.(({ data }: { data: ArrayBuffer }) => {
      sawChunks = true
      try {
        for (const byte of new Uint8Array(data)) {
          encodedLine += '%' + byte.toString(16).padStart(2, '0')
          if (byte === 10) {
            consume(decodeURIComponent(encodedLine))
            encodedLine = ''
          }
        }
      } catch (error) {
        reject(error)
        task.abort()
      }
    })
  })
  return { done, abort: () => task.abort() }
  // #endif
}

function setIdentity(result: SessionResult) {
  // #ifdef MP-WEIXIN
  if (result.access_token) uni.setStorageSync(tokenKey, result.access_token)
  // #endif
  identity.value = result.account
  return result.account
}

function transport(): 'web' | 'bearer' {
  // #ifdef MP-WEIXIN
  return 'bearer'
  // #endif
  return 'web'
}

export function restoreIdentity() {
  if (!live) return Promise.resolve()
  initialization ||= api<Identity>('/auth/session')
    .then((user) => { identity.value = user })
    .catch((error) => {
      if (error instanceof ApiError && error.status === 401) uni.removeStorageSync(tokenKey)
    })
  return initialization
}

export async function requireVisitor() {
  await restoreIdentity()
  if (identity.value) return identity.value
  guestRequest ||= api<SessionResult>('/auth/guest', {
    method: 'POST', body: { transport: transport() },
  }).then(setIdentity).finally(() => { guestRequest = undefined })
  return guestRequest
}

export async function authenticate(
  mode: 'login' | 'register',
  fields: { identifier: string; password: string } | { username: string; password: string; display_name?: string },
  carryReading?: string,
) {
  await restoreIdentity()
  if (guestRequest) await guestRequest
  if (mode === 'register' && !identity.value) await requireVisitor()
  const result = await api<SessionResult>('/auth/' + mode, {
    method: 'POST', body: {
      ...fields, transport: transport(),
      carry_reading_id: mode !== 'register' && identity.value?.is_guest ? carryReading : undefined,
    },
  })
  setIdentity(result)
  return result
}

export type EmailPurpose = 'bind_email' | 'reset_password'

export function authStatus() {
  return api<{ email_codes: boolean; wechat_login: boolean }>('/auth/status')
}

export function sendEmailCode(email: string, purpose: EmailPurpose) {
  const path = purpose === 'bind_email' ? '/auth/email/code' : '/auth/send-code'
  return api<{ cooldown: number }>(path, { method: 'POST', body: { email } })
}

export async function resetPassword(email: string, code: string, password: string) {
  await api('/auth/reset-password', { method: 'POST', body: { email, code, password } })
  clearIdentity()
}

function wechatCode(): Promise<string> {
  // #ifdef MP-WEIXIN
  return new Promise((resolve, reject) => {
    const failed = () => reject(new Error('微信授权未完成，请重试。'))
    uni.login({ provider: 'weixin', success: ({ code }) => code ? resolve(code) : failed(), fail: failed })
  })
  // #endif
  // #ifndef MP-WEIXIN
  return Promise.reject(new Error('请在微信小程序内操作。'))
  // #endif
}

export async function authenticateWechat(carryReading?: string) {
  await restoreIdentity()
  if (guestRequest) await guestRequest
  const result = await api<SessionResult>('/auth/wechat', {
    method: 'POST', body: { code: await wechatCode(), carry_reading_id: carryReading },
  })
  setIdentity(result)
  return result
}

export async function bindWechat() {
  identity.value = await api<Identity>('/auth/wechat/bind', {
    method: 'POST', body: { code: await wechatCode() },
  })
}

export async function updateCredentials(fields: { username?: string; password?: string; current_password?: string }, withWechat = false) {
  const result = await api<SessionResult>('/auth/credentials', {
    method: 'PUT', body: { ...fields, wechat_code: withWechat ? await wechatCode() : undefined },
  })
  setIdentity(result)
}

export async function bindEmail(email: string, code: string, currentPassword: string) {
  identity.value = await api<Identity>('/auth/email/bind', {
    method: 'POST', body: { email, code, current_password: currentPassword },
  })
}

export async function signOut() {
  try {
    await api('/auth/session', { method: 'DELETE' })
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) throw error
  }
  clearIdentity()
}

export function clearIdentity() {
  uni.removeStorageSync(tokenKey)
  identity.value = null
}

export function accountStore<T>(name: string, initial: T): { state: ShallowRef<T>; write: (value: T) => boolean } {
  if (!live) return localStore(name, initial)
  const key = () => 'xuanji:client:live:' + (identity.value?.id || 'device') + ':' + name
  const state = shallowRef(readStorage(key(), initial))
  watch(() => identity.value?.id, () => { state.value = readStorage(key(), initial) }, { flush: 'sync' })
  function write(value: T) {
    try {
      uni.setStorageSync(key(), value)
      state.value = value
      return true
    } catch {
      uni.showToast({ title: '本机保存失败，请重试。', icon: 'none' })
      return false
    }
  }
  return { state, write }
}
