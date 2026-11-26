<script setup lang="ts">
import { computed } from 'vue'
import AppShell from '../../components/AppShell.vue'
import AppIcon from '../../components/AppIcon.vue'
import NavLink from '../../components/NavLink.vue'
import ToolCard from '../../components/ToolCard.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import SelectField from '../../components/SelectField.vue'
import { preferences, availableProfiles } from '../../features/account/state'
import { tools } from '../../features/catalog/tools'
import { birthdaySign, signById, signs } from '../../features/catalog/zodiac'
import { readings } from '../../features/divination/records'
import { liuyaoDraft } from '../../features/divination/draft'
import { officialRoles, sessions } from '../../features/ai/state'
import { currentTerm } from '../../features/calendar/terms'
import { destination, go } from '../../shared/navigation'
import { dateKey, displayDate } from '../../shared/storage'

const date = dateKey()
const term = currentTerm()
const signOptions = signs.map(({ id, name }) => ({ value: id, label: name }))
const sign = computed(() => signById(preferences.state.value.sign))
const personal = computed(() => preferences.state.value.fortuneMode === 'personal')
const profile = computed(() => availableProfiles.value[0]!)
const todaySign = computed(() => (personal.value ? birthdaySign(profile.value.date) : sign.value))
const recent = computed(() => readings.state.value[0])

const activity = computed(() => {
  const list = [
    ...readings.state.value.map((item) => ({
      id: item.id,
      title: item.title,
      status: item.saved ? '已保存' : '最近体验',
      time: item.createdAt,
      to: destination('account', 'result', { id: item.id }),
    })),
    ...sessions.state.value.map((item) => ({
      id: item.id,
      title: item.roleName,
      status: '继续对话',
      time: item.updated,
      to: destination('ai', 'chat', { id: item.id }),
    })),
  ].sort((a, b) => b.time.localeCompare(a.time))
  const draft = liuyaoDraft.state.value
  if (draft.lines.length || draft.question.trim()) {
    list.unshift({
      id: 'draft-liuyao',
      title: '六爻问事',
      status: '未完成 · ' + draft.lines.length + '/6 爻',
      time: date,
      to: destination('divination', 'liuyao'),
    })
  }
  return list.slice(0, 3)
})

const quickTools = tools.slice(0, 6)
const discoveries = tools.filter((tool) => ['astro', 'match', 'dream'].includes(tool.to.view || ''))
const homeRoles = officialRoles.slice(0, 3)

function togglePersonal() {
  preferences.write({ ...preferences.state.value, fortuneMode: personal.value ? 'sign' : 'personal' })
}
function chooseSign(value: string) {
  preferences.write({ ...preferences.state.value, sign: value, fortuneMode: 'sign' })
}
function seeTools() {
  uni.pageScrollTo({
    selector: '#home-tools',
    duration: preferences.state.value.reducedMotion ? 0 : 260,
    fail: () => go(destination('explore')),
  })
}
</script>

<template>
  <AppShell section="home">
    <view class="home-hero">
      <image
        class="hero-art desktop-art"
        src="/static/hero-desktop.webp"
        mode="aspectFill"
        aria-hidden="true"
      />
      <image
        class="hero-art mobile-art"
        src="/static/hero-mobile.webp"
        mode="aspectFill"
        aria-hidden="true"
      />
      <view class="hero-wash" aria-hidden="true"></view>
      <view class="content-width hero-layout">
        <view class="hero-copy">
          <text class="hero-title">
            <text class="title-line">窥天地玄机，</text>
            <text class="title-line">知人生万象</text>
          </text>
          <text class="hero-subtitle">
            <text>以东方智慧为引，</text><text class="subtitle-continuation">探索命理、梦境与人生可能。</text>
          </text>
          <view class="actions hero-actions">
            <button class="btn primary realm-button" @tap="seeTools">
              开启玄境 <text aria-hidden="true">→</text>
            </button>
            <NavLink class="btn secondary-button" :to="destination('divination', 'tarot')"
              >抽一张塔罗</NavLink
            >
          </view>
        </view>

        <view class="panel stack today-card">
          <SectionHeading title="今日一览">
            <text class="gold small today-date">{{ displayDate(date) }} · {{ term.title }}</text>
          </SectionHeading>
          <view class="today-main">
            <AppIcon name="zodiac" class="today-glyph" />
            <view>
              <text class="block today-label">
                {{ personal ? profile.name + ' · 个人运势' : todaySign.name + ' · 今日运势' }}
              </text>
              <text class="block muted">{{ todaySign.prompt }}</text>
            </view>
          </view>
          <view class="today-controls">
            <SelectField
              label="星座"
              :model-value="sign.id"
              :options="signOptions"
              @update:model-value="chooseSign"
            />
            <view class="today-actions">
              <button class="link" @tap="togglePersonal">
                {{ personal ? '切回星座运势' : '切换个人运势' }}
              </button>
              <NavLink
                class="link"
                :to="
                  destination('today', personal ? 'personal' : 'fortune', { sign: sign.id, id: profile.id })
                "
              >
                查看今日详情 ›
              </NavLink>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view class="content-width home-content">
      <view id="home-tools" class="section-block">
        <SectionHeading title="常用工具" :to="destination('explore')" />
        <view class="quick-grid">
          <ToolCard v-for="tool in quickTools" :key="tool.title" v-bind="tool" feature />
        </view>
      </view>

      <view class="section-block split">
        <view class="panel stack">
          <SectionHeading title="继续上次" :to="destination('account', 'records')" action="全部记录" />
          <view v-if="activity.length">
            <NavLink v-for="item in activity" :key="item.id" class="row-link" :to="item.to">
              <view>
                <text>{{ item.title }}</text>
                <text class="muted block small">{{ displayDate(item.time) }} · {{ item.status }}</text>
              </view>
              <text class="gold">›</text>
            </NavLink>
          </view>
          <view v-else class="stack">
            <text class="muted">抽完牌或排完盘，最近的体验会出现在这里。</text>
            <NavLink class="link" :to="destination('explore', 'topic', { id: 'tarot' })"
              >看三张牌示例 ›</NavLink
            >
          </view>
        </view>
        <view class="panel stack">
          <SectionHeading title="每日小体验" :to="destination('today')" action="打开今日" />
          <view class="daily-links">
            <NavLink class="row-link" :to="destination('divination', 'daily')">
              <text>每日塔罗</text><text class="gold">翻开日签 ›</text>
            </NavLink>
            <NavLink class="row-link" :to="destination('today', 'calendar', { date })">
              <text>星象日历</text><text class="gold">{{ term.title }} ›</text>
            </NavLink>
            <NavLink class="row-link" :to="destination('account', 'journal-edit', { date })">
              <text>私人日记</text><text class="gold">记录今天 ›</text>
            </NavLink>
          </view>
        </view>
      </view>

      <view class="section-block">
        <SectionHeading title="发现与报告" :to="destination('ai', 'reports')" action="报告目录" />
        <view class="cols-3">
          <ToolCard v-for="tool in discoveries" :key="tool.title" v-bind="tool" />
        </view>
      </view>

      <view class="section-block panel home-ai">
        <SectionHeading title="AI 对话" :to="destination('ai')" action="查看角色" />
        <view class="role-links">
          <NavLink
            v-for="role in homeRoles"
            :key="role.id"
            class="home-role"
            :to="destination('ai', 'role', { id: role.id })"
          >
            <AppIcon :glyph="role.glyph" />
            <view>
              <text class="block">{{ role.name }}</text>
              <text class="muted small">{{ role.specialty }}</text>
            </view>
          </NavLink>
        </view>
        <view class="actions">
          <NavLink
            class="btn primary"
            :to="recent ? destination('ai', 'new', { source: recent.id }) : destination('ai', 'new')"
          >
            {{ recent ? '询问最近结果' : '新建对话' }}
          </NavLink>
        </view>
      </view>
    </view>
  </AppShell>
</template>

<style scoped>
.home-hero {
  position: relative;
  overflow: hidden;
  background: #160e20;
  border-bottom: 1px solid #57405a6e;
}
.hero-art,
.hero-wash {
  position: absolute;
  pointer-events: none;
}
.hero-art {
  top: clamp(-112px, -5.6vw, -42px);
  left: 50%;
  width: min(100%, 1680px);
  height: min(66.6667vw, 1120px);
  transform: translateX(-50%);
}
.mobile-art {
  display: none;
}
.hero-wash {
  inset: 0;
  background:
    linear-gradient(90deg, #130d1fea, #150d1e8c 38%, #160e1e05 66%, #150e1eaa 100%),
    linear-gradient(0deg, #160e20 0%, #160e2000 27%);
}
.hero-layout {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(330px, 0.9fr);
  align-items: center;
  gap: clamp(26px, 6vw, 95px);
  padding: clamp(45px, 5vw, 76px) 0;
}
.hero-title {
  display: block;
  font: 600 clamp(43px, 5vw, 75px) / 1.13 var(--serif);
  letter-spacing: 0.04em;
  color: #f7edf6;
  text-shadow: 0 3px 18px #12091f;
}
.title-line {
  display: block;
}
.hero-subtitle {
  display: block;
  max-width: 33em;
  margin: 20px 0 25px;
  font: 450 clamp(14px, 1.3vw, 19px) / 1.68 var(--serif);
  color: #ead9ee;
  letter-spacing: 0.035em;
}
.hero-actions .btn {
  min-height: 47px;
  padding: 0 18px;
  font: 600 16px/1.2 var(--serif);
}
.realm-button {
  min-width: 148px;
}
.secondary-button {
  background: #23172cd9;
}
.today-card {
  gap: 17px;
  padding: 21px;
  background: linear-gradient(144deg, #302039f4, #1e142bf7 80%);
  border-color: #775a758e;
}
.today-date {
  white-space: nowrap;
}
.today-main {
  display: flex;
  align-items: center;
  gap: 13px;
}
.today-glyph {
  flex: 0 0 49px;
  width: 49px;
  height: 49px;
}
.today-label {
  font-weight: 650;
  margin-bottom: 3px;
}
.today-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 14px;
}
.today-actions {
  display: grid;
  gap: 3px;
}
.home-content {
  position: relative;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}
.home-ai {
  gap: 18px;
}
.role-links {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.home-role {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #60496c;
  border-radius: 9px;
  padding: 12px;
  background: #24182e;
}
.home-role .app-icon {
  width: 34px;
  height: 34px;
}
@media (max-width: 1110px) {
  .quick-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 767px) {
  .desktop-art {
    display: none;
  }
  .mobile-art {
    display: block;
    top: -12vw;
    height: 150vw;
  }
  .hero-wash {
    background: linear-gradient(0deg, #191025fa, #1710203d 70%, #17102054 100%);
  }
  .hero-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 18px;
    padding: 26px 0 18px;
  }
  .hero-title {
    font-size: clamp(33px, 8.6vw, 51px);
  }
  .hero-subtitle {
    margin: 9px 0 14px;
    max-width: 24em;
  }
  .subtitle-continuation {
    display: block;
  }
  .hero-actions .btn {
    min-height: 44px;
    padding: 0 12px;
    font-size: 15px;
  }
  .realm-button {
    min-width: 126px;
  }
  .today-card {
    gap: 10px;
    padding: 13px;
  }
  .today-glyph {
    flex-basis: 38px;
    width: 38px;
    height: 38px;
  }
  .today-controls {
    gap: 11px;
  }
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 9px;
  }
  .role-links {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
}
</style>
