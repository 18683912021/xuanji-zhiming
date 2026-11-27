<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import DateField from '../../components/DateField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { account, availableProfiles, feedback } from '../../features/account/state'
import { birthdaySign, signById, signs } from '../../features/catalog/zodiac'
import { readings } from '../../features/divination/records'
import {
  connections,
  invites,
  notices,
  people,
  posts,
  rooms,
  type Person,
  type SocialMessage,
  type SocialPost,
} from '../../features/social/state'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, makeId } from '../../shared/storage'

const titles: Record<string, string> = {
  index: '关系与社区',
  matching: '心动匹配',
  birthday: '同生日匹配',
  feed: '关注动态',
  person: '个人主页',
  publish: '发布动态',
  following: '关注与粉丝',
  messages: '消息中心',
  chat: '真人私聊',
  invite: '合盘邀请',
  blocks: '已拉黑的用户',
}
const query = ref<Query>({})
const view = computed(() => (query.value.view && Object.prototype.hasOwnProperty.call(titles, query.value.view) ? query.value.view : 'index'))
const tab = ref('私聊')
const relationTab = ref('我的关注')
const matchesFilter = ref('')
const birth = ref(account.state.value?.birth || '1996-10-12')
const body = ref('')
const image = ref('')
const sourceId = ref('')
const reason = ref('')
const ownProfile = ref(availableProfiles.value[0]!.id)
const secondProfile = ref(availableProfiles.value[1]!.id)
const input = ref('')
const own = computed(() => query.value.id === 'self')
const editPost = computed(() =>
  posts.state.value.find((item) => item.id === query.value.post && item.user === 'self'),
)
const person = computed(() => people.find((item) => item.id === query.value.id))
const personAllowed = computed(() =>
  person.value && !connections.state.value.blocked.includes(person.value.id) ? person.value : undefined,
)
const room = computed(() => rooms.state.value.find((item) => item.user === query.value.id))
const outgoing = computed(() => invites.state.value.find((item) => item.id === query.value.invite))
const profileChoices = computed(() =>
  availableProfiles.value.map((item) => ({ value: item.id, label: item.name })),
)
const visiblePeople = computed(() =>
  people.filter((item) => !connections.state.value.blocked.includes(item.id)),
)
const candidates = computed(() =>
  visiblePeople.value.filter((item) => {
    if (connections.state.value.skipped.includes(item.id)) return false
    return view.value === 'birthday'
      ? birth.value.slice(5) === item.birthday
      : !matchesFilter.value || matchesFilter.value === item.sign
  }),
)
const visiblePosts = computed(() =>
  posts.state.value.filter((item) => {
    if (connections.state.value.blocked.includes(item.user)) return false
    if (view.value === 'person') return item.user === query.value.id
    return (
      relationTab.value === '全部动态' ||
      item.user === 'self' ||
      connections.state.value.following.includes(item.user)
    )
  }),
)
const peopleOptions = [
  { value: '', label: '任意星座' },
  ...signs.map((item) => ({ value: item.id, label: item.name })),
]
const unreadMessages = computed(
  () =>
    rooms.state.value.filter((item) => item.unread && !connections.state.value.blocked.includes(item.user))
      .length,
)

onLoad((params) => {
  query.value = params || {}
  if (view.value === 'publish' && editPost.value) {
    body.value = editPost.value.body
    image.value = editPost.value.image || ''
  }
  if (view.value === 'feed') relationTab.value = '全部动态'
  if (view.value === 'chat' && room.value?.unread)
    rooms.write(
      rooms.state.value.map((item) => (item.user === query.value.id ? { ...item, unread: false } : item)),
    )
  if (outgoing.value) {
    reason.value = outgoing.value.reason
    secondProfile.value = outgoing.value.second
    ownProfile.value = outgoing.value.first
  }
})
function personName(id: string) {
  return id === 'self'
    ? account.state.value?.nickname || '观星人'
    : people.find((item) => item.id === id)?.name || '星友'
}
function toggle(key: 'following' | 'blocked' | 'liked' | 'skipped', id: string, add?: boolean) {
  const state = connections.state.value
  const next = add ?? !state[key].includes(id)
  connections.write({
    ...state,
    [key]: next ? [...new Set([...state[key], id])] : state[key].filter((item) => item !== id),
  })
}
function likePerson(item: Person) {
  toggle('liked', item.id, true)
  if (item.willing && !rooms.state.value.some((entry) => entry.user === item.id)) {
    rooms.write([{ user: item.id, messages: [], unread: false }, ...rooms.state.value])
  }
  toast(item.willing ? '双方已互相喜欢，可发消息。' : '已记录喜欢。')
}
function flag(id: string) {
  confirmAction('举报内容', '将这次举报记录到 Mock 环境。', () => {
    feedback.write([
      { id: makeId(), category: '社区举报', text: '举报目标 ' + id, createdAt: dateKey() },
      ...feedback.state.value,
    ])
    toast('举报已记录。')
  })
}
function block(id: string) {
  confirmAction('拉黑用户', '这位用户会从匹配和私聊入口隐藏。', () => {
    toggle('blocked', id, true)
    go(destination('social', 'blocks'), 'replace')
  })
}
function openChat(item: Person) {
  if (
    connections.state.value.blocked.includes(item.id) ||
    !rooms.state.value.some((entry) => entry.user === item.id)
  ) {
    return toast('双方同意后可开启私聊。')
  }
  go(destination('social', 'chat', { id: item.id }))
}
function sendMessage(type: SocialMessage['type'] = 'text', value = input.value) {
  const target = room.value
  if (!target || !personAllowed.value || !value.trim()) return
  const message: SocialMessage = { id: makeId(), from: 'me', body: value.trim(), type, date: dateKey() }
  if (
    rooms.write(
      rooms.state.value.map((item) =>
        item.user === target.user ? { ...item, messages: [...item.messages, message] } : item,
      ),
    )
  )
    input.value = ''
}
function pickImage(callback: (path: string) => void) {
  uni.chooseImage({
    count: 1,
    sourceType: ['album'],
    sizeType: ['compressed'],
    success: ({ tempFilePaths }) => {
      const path = Array.isArray(tempFilePaths) ? tempFilePaths[0] : tempFilePaths
      if (path) callback(path)
    },
  })
}
function savePost() {
  if (!body.value.trim()) return
  const next = {
    id: editPost.value?.id || makeId(),
    user: 'self',
    body: body.value.trim(),
    image: image.value || undefined,
    date: dateKey(),
    likes: editPost.value?.likes || 0,
    liked: editPost.value?.liked || false,
  }
  if (posts.write([next, ...posts.state.value.filter((item) => item.id !== next.id)]))
    go(destination('social', 'feed'), 'replace')
}
function react(post: SocialPost) {
  posts.write(
    posts.state.value.map((item) =>
      item.id === post.id ? { ...item, likes: item.likes + (item.liked ? -1 : 1), liked: !item.liked } : item,
    ),
  )
}
function deletePost(id: string) {
  confirmAction('删除动态', '这条动态会从本机删除。', () =>
    posts.write(posts.state.value.filter((item) => item.id !== id)),
  )
}
function invite() {
  if (!personAllowed.value || !reason.value.trim()) return
  if (ownProfile.value === secondProfile.value) return toast('请选两份不同的档案。')
  const item = {
    id: makeId(),
    user: personAllowed.value.id,
    reason: reason.value.trim(),
    first: ownProfile.value,
    second: secondProfile.value,
    direction: 'outbound' as const,
    status: 'pending' as const,
  }
  if (invites.write([item, ...invites.state.value]))
    go(destination('social', 'invite', { invite: item.id }), 'replace')
}
function updateInvite(status: 'accepted' | 'declined' | 'revoked') {
  const item = outgoing.value
  if (!item || connections.state.value.blocked.includes(item.user)) return
  if (status === 'accepted' && ownProfile.value === secondProfile.value) return toast('请选两份不同的档案。')
  invites.write(
    invites.state.value.map((entry) =>
      entry.id === item.id
        ? { ...entry, status, first: ownProfile.value, second: secondProfile.value }
        : entry,
    ),
  )
}
function shareCard() {
  const selected = readings.state.value.find((item) => item.id === sourceId.value)
  if (!selected) return
  confirmAction('发送结果卡', '只分享类型和结果日期。私人问题及出生资料不会发送。', () => {
    sendMessage('card', selected.title.split(' · ')[0] + ' · ' + selected.date)
    sourceId.value = ''
  })
}
</script>

<template>
  <AppShell
    section="social"
    :title="own ? personName('self') : view === 'person' && person ? person.name : titles[view]"
    :detail="view !== 'index'"
  >
    <view class="content-width stack">
      <template v-if="view === 'index'">
        <view class="cols-3">
          <NavLink class="panel" :to="destination('social', 'matching')">心动匹配 ›</NavLink
          ><NavLink class="panel" :to="destination('social', 'birthday')">同生日匹配 ›</NavLink>
          <NavLink class="panel" :to="destination('social', 'feed')">关注动态 ›</NavLink
          ><NavLink class="panel" :to="destination('social', 'messages')">消息中心 ›</NavLink>
          <NavLink class="panel" :to="destination('social', 'person', { id: 'self' })"
            >我的公开主页 ›</NavLink
          >
        </view>
      </template>
      <template v-else-if="view === 'matching' || view === 'birthday'">
        <view class="split"
          ><view class="panel stack">
            <text class="panel-head">{{ view === 'matching' ? '匹配偏好' : '选择生日月日' }}</text>
            <SelectField
              v-if="view === 'matching'"
              v-model="matchesFilter"
              label="偏好星座"
              :options="peopleOptions"
            />
            <DateField v-else v-model="birth" label="生日" />
            <text class="notice">这里展示 Mock 星友。在匹配列表中只使用公开资料。</text>
            <button
              class="btn primary"
              @tap="
                connections.write({
                  ...connections.state.value,
                  matching: !connections.state.value.matching,
                  skipped: [],
                })
              "
            >
              {{ connections.state.value.matching ? '暂停匹配' : '开始匹配' }}
            </button> </view
          ><view class="stack">
            <text v-if="!connections.state.value.matching" class="panel muted">开启后查看示例候选。</text>
            <text v-else-if="!candidates.length" class="panel muted">当前条件下没有更多候选。</text>
            <view v-else v-for="item in candidates" :key="item.id" class="panel stack">
              <text class="avatar" :style="{ backgroundColor: item.color }">{{ item.name.slice(0, 1) }}</text>
              <text class="panel-head">{{ item.name }} · {{ signById(item.sign).name }}</text
              ><text>{{ view === 'birthday' ? item.birthday + ' · ' + item.bio : item.reason }}</text>
              <view class="actions">
                <button
                  class="btn primary"
                  :disabled="connections.state.value.liked.includes(item.id)"
                  @tap="likePerson(item)"
                >
                  {{ connections.state.value.liked.includes(item.id) ? '已喜欢' : '喜欢' }}
                </button>
                <button class="btn" @tap="toggle('skipped', item.id, true)">跳过</button>
                <NavLink class="btn" :to="destination('social', 'person', { id: item.id })">查看主页</NavLink>
                <button
                  v-if="rooms.state.value.some((entry) => entry.user === item.id)"
                  class="btn"
                  @tap="openChat(item)"
                >
                  发消息
                </button>
              </view>
            </view>
          </view></view
        >
      </template>
      <template v-else-if="view === 'person' || view === 'feed'">
        <view v-if="view === 'person' && !own && !personAllowed" class="panel muted"
          >此公开资料当前不可用。</view
        >
        <template v-else>
          <view v-if="view === 'person'" class="panel stack">
            <text class="avatar">{{ personName(query.id || 'self').slice(0, 1) }}</text>
            <text class="panel-head">{{ personName(query.id || 'self') }}</text>
            <text>{{ own ? account.state.value?.bio || '还没有填写签名。' : person?.bio }}</text>
            <text v-if="own" class="muted"
              >{{ account.state.value?.publicBirthday ? account.state.value.birth.slice(5) : '' }}
              {{
                account.state.value?.publicSign && account.state.value.birth
                  ? birthdaySign(account.state.value.birth).name
                  : ''
              }}
              {{ account.state.value?.publicMbti ? account.state.value.mbti : '' }}</text
            >
            <text v-else-if="person" class="muted"
              >{{ signById(person.sign).name }} · {{ person.birthday }} · {{ person.type }}</text
            >
            <view class="actions">
              <template v-if="own"
                ><NavLink class="btn" :to="destination('account', 'public-edit')">编辑公开资料</NavLink>
                <NavLink class="btn" :to="destination('social', 'following')"
                  >关注 {{ connections.state.value.following.length }} · 粉丝 1</NavLink
                ></template
              >
              <template v-else-if="person"
                ><button class="btn primary" @tap="toggle('following', person.id)">
                  {{ connections.state.value.following.includes(person.id) ? '已关注' : '关注' }}
                </button>
                <button class="btn" @tap="openChat(person)">私聊</button>
                <NavLink class="btn" :to="destination('social', 'invite', { id: person.id })"
                  >邀请合盘</NavLink
                >
                <button class="btn" @tap="flag(person.id)">举报</button
                ><button class="btn" @tap="block(person.id)">拉黑</button></template
              >
            </view>
          </view>
          <view class="section-heading"
            ><text class="section-title">动态</text
            ><NavLink v-if="own || view === 'feed'" class="link" :to="destination('social', 'publish')"
              >发布动态 ›</NavLink
            ></view
          >
          <view v-if="view === 'feed'" class="chips"
            ><button
              v-for="name in ['全部动态', '我的关注']"
              :key="name"
              class="chip"
              :class="{ selected: relationTab === name }"
              @tap="relationTab = name"
            >
              {{ name }}
            </button></view
          >
          <view v-for="post in visiblePosts" :key="post.id" class="panel stack">
            <NavLink class="link" :to="destination('social', 'person', { id: post.user })"
              >{{ personName(post.user) }} · {{ post.date }}</NavLink
            >
            <text>{{ post.body }}</text
            ><image v-if="post.image" class="image-preview" :src="post.image" mode="aspectFit" />
            <view class="actions">
              <button class="btn" @tap="react(post)">
                {{ post.liked ? '已赞' : '点赞' }} {{ post.likes }}
              </button>
              <NavLink
                v-if="post.user === 'self'"
                class="btn"
                :to="destination('social', 'publish', { post: post.id })"
                >编辑</NavLink
              >
              <button v-if="post.user === 'self'" class="btn" @tap="deletePost(post.id)">删除</button>
              <button v-else class="link" @tap="flag(post.id)">举报</button>
            </view>
          </view>
          <text v-if="!visiblePosts.length" class="panel muted">这里还没有动态。</text>
        </template>
      </template>
      <template v-else-if="view === 'publish'">
        <view class="panel stack"
          ><text class="notice">动态和图片在当前设备展示。</text>
          <textarea v-model="body" class="field area" maxlength="700" placeholder="分享一项有趣的观察" />
          <image v-if="image" class="image-preview" :src="image" mode="aspectFit" />
          <view class="actions"
            ><button class="btn" @tap="pickImage((path) => (image = path))">选择图片</button
            ><button v-if="image" class="btn" @tap="image = ''">移除图片</button>
            <button class="btn primary" :disabled="!body.trim()" @tap="savePost">保存动态</button></view
          >
        </view>
      </template>
      <template v-else-if="view === 'following' || view === 'blocks'">
        <view v-if="view === 'following'" class="chips"
          ><button
            v-for="name in ['我的关注', '关注我的']"
            :key="name"
            class="chip"
            :class="{ selected: relationTab === name }"
            @tap="relationTab = name"
          >
            {{ name }}
          </button></view
        >
        <view class="panel">
          <view
            v-for="item in people.filter((entry) =>
              view === 'blocks'
                ? connections.state.value.blocked.includes(entry.id)
                : !connections.state.value.blocked.includes(entry.id) &&
                  (relationTab === '我的关注'
                    ? connections.state.value.following.includes(entry.id)
                    : entry.id === 'mu'),
            )"
            :key="item.id"
            class="row"
          >
            <text v-if="view === 'blocks'">{{ item.name }}</text
            ><NavLink v-else :to="destination('social', 'person', { id: item.id })"
              >{{ item.name }} ›</NavLink
            >
            <button v-if="view === 'blocks'" class="link" @tap="toggle('blocked', item.id, false)">
              取消拉黑
            </button>
          </view>
          <text v-if="view === 'blocks' && !connections.state.value.blocked.length" class="muted"
            >没有已拉黑的用户。</text
          >
          <text
            v-if="
              view === 'following' && relationTab === '我的关注' && !connections.state.value.following.length
            "
            class="muted"
            >还没有关注任何人。</text
          >
        </view>
      </template>
      <template v-else-if="view === 'messages'">
        <view class="chips"
          ><button
            v-for="name in ['私聊', '关注与互动', '合盘邀请', '活动与提醒']"
            :key="name"
            class="chip"
            :class="{ selected: tab === name }"
            @tap="tab = name"
          >
            {{ name }}{{ name === '私聊' && unreadMessages ? ' ' + unreadMessages : '' }}
          </button></view
        >
        <view class="panel stack">
          <template v-if="tab === '私聊'">
            <NavLink
              v-for="item in rooms.state.value.filter(
                (item) => !connections.state.value.blocked.includes(item.user),
              )"
              :key="item.user"
              class="row-link"
              :to="destination('social', 'chat', { id: item.user })"
              ><view
                ><text class="block">{{ personName(item.user) }}</text
                ><text class="muted small">{{
                  item.messages.at(-1)?.type === 'text' ? item.messages.at(-1)?.body : '会话记录'
                }}</text></view
              ><text class="gold">{{ item.unread ? '未读' : '›' }}</text></NavLink
            >
          </template>
          <template v-else-if="tab === '合盘邀请'">
            <NavLink
              v-for="item in invites.state.value.filter(
                (entry) => !connections.state.value.blocked.includes(entry.user),
              )"
              :key="item.id"
              class="row-link"
              :to="destination('social', 'invite', { invite: item.id })"
              ><text
                >{{ personName(item.user) }} ·
                {{ item.direction === 'inbound' ? '发来' : '收到' }}合盘邀请</text
              ><text class="gold">{{ item.status === 'pending' ? '待确认' : '查看状态' }} ›</text></NavLink
            >
          </template>
          <template v-else>
            <button
              v-for="notice in notices.state.value.filter((item) => item.category === tab)"
              :key="notice.id"
              class="row"
              @tap="
                notices.write(
                  notices.state.value.map((item) =>
                    item.id === notice.id ? { ...item, unread: false } : item,
                  ),
                )
              "
            >
              <view
                ><text class="block">{{ notice.title }}</text
                ><text class="muted small">{{ notice.copy }}</text></view
              ><text class="gold">{{ notice.unread ? '标记已读' : '已读' }}</text>
            </button>
          </template>
        </view>
      </template>
      <template v-else-if="view === 'chat'">
        <view v-if="!room || !personAllowed" class="panel muted">当前无法访问这条会话。</view>
        <view v-else class="workspace">
          <view class="panel stack"
            ><text class="panel-head">{{ personName(room.user) }}</text>
            <NavLink class="link" :to="destination('social', 'person', { id: room.user })">查看主页 ›</NavLink
            ><button class="link" @tap="flag(room.user)">举报</button
            ><button class="link" @tap="block(room.user)">拉黑</button>
          </view>
          <view class="panel stack"
            ><text class="notice">Mock 真人私聊 · 消息只写入当前设备。</text>
            <view
              v-for="message in room.messages"
              :key="message.id"
              class="dm"
              :class="{ own: message.from === 'me' }"
            >
              <image
                v-if="message.type === 'image'"
                class="image-preview"
                :src="message.body"
                mode="aspectFit"
              />
              <text v-else>{{ message.type === 'card' ? '结果卡 · ' : '' }}{{ message.body }}</text>
            </view>
            <textarea v-model="input" class="field area" maxlength="500" placeholder="写一条消息" />
            <view class="actions"
              ><button class="btn primary" :disabled="!input.trim()" @tap="sendMessage()">发送</button>
              <button class="btn" @tap="input += ' ✨'">表情 ✨</button
              ><button class="btn" @tap="pickImage((path) => sendMessage('image', path))">图片</button></view
            >
            <view class="actions"
              ><SelectField
                v-model="sourceId"
                label="分享结果卡"
                :options="
                  readings.state.value
                    .filter((item) => item.saved)
                    .map((item) => ({ value: item.id, label: item.title }))
                "
              />
              <button class="btn" :disabled="!sourceId" @tap="shareCard">确认发送卡片</button></view
            >
          </view>
        </view>
      </template>
      <template v-else-if="view === 'invite'">
        <view class="panel stack">
          <text class="panel-head">{{
            outgoing
              ? personName(outgoing.user) + ' · 合盘邀请'
              : '邀请 ' + personName(query.id || '') + ' 合盘'
          }}</text>
          <text class="notice">只共享确认过的关系摘要。完整出生资料留在私人档案中。</text>
          <template v-if="!outgoing">
            <textarea v-model="reason" class="field area" maxlength="220" placeholder="说明本次合盘用途" />
            <SelectField v-model="ownProfile" label="你的档案" :options="profileChoices" />
            <SelectField v-model="secondProfile" label="另一份示例档案" :options="profileChoices" />
            <button class="btn primary" @tap="invite">发送 Mock 邀请</button>
          </template>
          <template v-else>
            <text>{{ outgoing.reason }}</text>
            <text class="gold">{{
              { pending: '待双方确认', accepted: '双方已确认', revoked: '已撤销', declined: '已拒绝' }[
                outgoing.status
              ]
            }}</text>
            <template v-if="outgoing.status === 'pending'">
              <SelectField v-model="secondProfile" label="确认共享档案" :options="profileChoices" />
              <view class="actions"
                ><button class="btn primary" @tap="updateInvite('accepted')">
                  {{ outgoing.direction === 'outbound' ? '模拟对方同意' : '同意并共享摘要' }}
                </button>
                <button
                  class="btn"
                  @tap="updateInvite(outgoing.direction === 'inbound' ? 'declined' : 'revoked')"
                >
                  {{ outgoing.direction === 'inbound' ? '拒绝' : '撤销邀请' }}
                </button></view
              >
            </template>
            <template v-else-if="outgoing.status === 'accepted'">
              <NavLink
                class="btn primary"
                :to="destination('charts', 'match', { id: outgoing.first, second: outgoing.second })"
                >打开双方合盘</NavLink
              >
              <button class="btn" @tap="updateInvite('revoked')">撤销共享</button>
            </template>
          </template>
        </view>
      </template>
    </view>
  </AppShell>
</template>
<style scoped>
.dm {
  justify-self: start;
  padding: 9px 12px;
  border-radius: 10px;
  color: var(--text);
  background: #2b1e38;
  max-width: 85%;
  overflow-wrap: anywhere;
}
.dm.own {
  justify-self: end;
  background: #4b345f;
}
</style>
