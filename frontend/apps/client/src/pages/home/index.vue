<script setup lang="ts">
import { computed } from 'vue'
import AppShell from '../../components/AppShell.vue'
import { usePageMotion } from '../../shared/pageMotion'
import AppIcon from '../../components/AppIcon.vue'
import NavLink from '../../components/NavLink.vue'
import ToolCard from '../../components/ToolCard.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import SelectField from '../../components/SelectField.vue'
import { preferences, availableProfiles } from '../../features/account/state'
import { tools } from '../../features/catalog/tools'
import { useFortune } from '../../features/catalog/remote'
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
const fortune = useFortune(todaySign, computed(() => date))
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
const entering = usePageMotion()
</script>

<template>
  <AppShell section="home" :entering="entering">
    <view class="home-backdrop" aria-hidden="true">
      <view class="nebula-band">
        <image class="nebula-art" src="/static/hero-desktop.webp" mode="scaleToFill" />
      </view>
      <view class="nebula-band nebula-lower">
        <image class="nebula-art" src="/static/hero-desktop.webp" mode="scaleToFill" />
      </view>
      <view class="home-sky">
        <image class="hero-art desktop-art" src="/static/hero-desktop.webp" mode="aspectFill" />
        <image class="hero-art mobile-art" src="/static/hero-mobile-v02.webp" mode="aspectFill" />
      </view>
    </view>

    <view :class="{ 'page-arrival': entering }">
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
      </view>

      <view class="content-width">
        <view class="home-panel today-card">
          <view class="today-heading">
            <text class="section-title">今日一览</text>
            <text class="gold small today-date">{{ displayDate(date) }} · {{ term.title }}</text>
          </view>
          <view class="today-main">
            <AppIcon name="zodiac" class="today-glyph" />
            <view>
              <text class="block today-label">
                {{ personal ? profile.name + ' · 个人运势' : todaySign.name + ' · 今日运势' }}
              </text>
              <text class="block muted">{{ fortune?.summary || todaySign.prompt }}</text>
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
      <view class="section-block tool-section">
        <view id="home-tools" class="tool-scroll-target" aria-hidden="true"></view>
        <SectionHeading title="常用工具" :to="destination('explore')" />
        <view class="quick-grid">
          <ToolCard v-for="tool in quickTools" :key="tool.title" v-bind="tool" feature plain />
        </view>
      </view>

      <view class="section-block split">
        <view class="home-panel stack">
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
        <view class="home-panel stack">
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
          <ToolCard v-for="tool in discoveries" :key="tool.title" v-bind="tool" plain />
        </view>
      </view>

      <view class="section-block home-panel home-ai">
        <SectionHeading title="AI 对话" :to="destination('ai')" action="查看角色" />
        <view class="role-links">
          <NavLink
            v-for="role in homeRoles"
            :key="role.id"
            class="home-role plain-card"
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
.home-backdrop {
  position: absolute;
  inset: calc(var(--header-row-height) + var(--status-padding, 0px) + 1px) 0 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 8% 48%, #3921407a, transparent 55%),
    radial-gradient(ellipse at 82% 87%, #3c224980, transparent 55%),
    linear-gradient(#160e20, #1a1122 58%, #160d1d);
}
.nebula-band {
  position: absolute;
  inset: 0 0 25%;
  overflow: hidden;
  opacity: 0.46;
  mix-blend-mode: screen;
  -webkit-mask-image: linear-gradient(transparent, #000 25%, #000 72%, transparent);
  mask-image: linear-gradient(transparent, #000 25%, #000 72%, transparent);
}
.nebula-lower {
  top: 43%;
  bottom: -17%;
  transform: scaleX(-1);
  opacity: 0.56;
}
.nebula-art {
  /* Sample the fog at the right edge, beyond the armillary sphere. */
  position: absolute;
  top: -28%;
  left: -250%;
  width: 350%;
  height: 205%;
}
.home-sky {
  position: absolute;
  inset: 0 0 auto;
  height: clamp(600px, 66.6667vw, 1024px);
  -webkit-mask-image: linear-gradient(#000 53%, transparent 98%);
  mask-image: linear-gradient(#000 53%, transparent 98%);
}
.hero-art {
  position: absolute;
  top: 0;
  left: 72%;
  width: clamp(900px, 100vw, 1536px);
  height: clamp(600px, 66.6667vw, 1024px);
  transform: translateX(-50%);
  filter: brightness(1.12) contrast(1.045);
}
.desktop-art {
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 24%, #000 81%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 24%, #000 81%, transparent);
}
.mobile-art {
  display: none;
}
.hero-layout {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  align-items: center;
  min-height: clamp(365px, 36vw, 520px);
  padding: 36px 0;
}
.hero-copy::before {
  display: block;
  width: clamp(94px, 15vw, 184px);
  height: 2px;
  margin-bottom: clamp(13px, 1.8vw, 23px);
  content: '';
  background: linear-gradient(90deg, #e8bf76, #f5d9a6 11%, #a5753d 39%, transparent 95%);
  box-shadow: 0 1px #331e2c, 0 0 12px #d7a45644;
}
.hero-title {
  display: block;
  font: 600 clamp(41px, 4.8vw, 74px) / 1.13 var(--serif);
  letter-spacing: 0.04em;
  color: #fff3e4;
  text-shadow:
    0 1px #af795994,
    0 3px 1px #190c1b,
    0 0 3px #000,
    0 0 8px #000,
    0 0 17px #000,
    0 0 30px #000,
    0 0 44px #000e;
}
.title-line {
  display: block;
}
.title-line + .title-line { color: #f4dfbd; }
.hero-subtitle {
  display: block;
  max-width: 33em;
  margin: 20px 0 25px;
  font: 450 clamp(14px, 1.3vw, 19px) / 1.68 var(--serif);
  color: #ead9ee;
  letter-spacing: 0.035em;
  text-shadow:
    0 0 2px #000,
    0 0 5px #000,
    0 0 11px #000,
    0 0 21px #000,
    0 0 30px #000d;
}
.hero-actions .btn {
  min-height: 51px;
  padding: 0 21px;
  font: 650 17px/1.2 var(--serif);
}
.hero-actions .realm-button {
  min-width: 179px;
  gap: 15px;
  font-size: 20px;
  letter-spacing: .04em;
}
.hero-actions .secondary-button {
  color: #f8e8d1;
  background: linear-gradient(160deg, #74503824, #170e2370 76%);
  border-color: #cfaa7776;
  box-shadow: inset 0 1px #f9d8a12f, 0 4px 12px #08040d8e;
}
.home-panel {
  position: relative;
  min-width: 0;
  border-top: 1px solid #b58b626b;
  box-shadow: inset 0 1px #0e071980;
  padding: 16px 0 0;
}
.home-panel::before {
  position: absolute;
  top: -1px;
  left: 0;
  width: 107px;
  height: 1px;
  background: linear-gradient(90deg, #f0cca5cb, transparent);
  pointer-events: none;
  content: '';
}
.today-card {
  display: grid;
  grid-template-columns: minmax(126px, 0.7fr) minmax(0, 1.85fr) minmax(0, 1.7fr);
  align-items: center;
  column-gap: clamp(12px, 2.6vw, 37px);
  padding: 17px 19px;
  border: 1px solid #a67d607e;
  border-radius: 12px;
  box-shadow: inset 0 1px #ffda9c28, inset 0 -1px #10081b8f, 0 7px 21px #0a040e57;
}
.today-card::before { left: 13px; }
.today-heading {
  display: grid;
  gap: 6px;
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
.home-shell .today-glyph { filter: drop-shadow(0 2px 3px #0a050d) drop-shadow(0 0 9px #dba8624d); }
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
.tool-section {
  position: relative;
}
.tool-scroll-target {
  position: absolute;
  top: calc(0px - var(--header-row-height) - var(--status-padding, 0px) - 13px);
  left: 0;
  width: 1px;
  height: 1px;
  pointer-events: none;
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
  border-width: 1px;
  border-style: solid;
  border-radius: 9px;
  padding: 12px;
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
  .home-sky {
    height: max(150vw, min(163vw, 946px));
  }
  .mobile-art {
    display: block;
    top: -5vw;
    left: 50%;
    width: max(100%, min(112vw, 650px));
    height: max(150vw, min(168vw, 975px));
  }
  .hero-layout {
    display: block;
    min-height: 0;
    padding: min(67vw, 390px) 0 28px;
    text-align: center;
  }
  .hero-copy::before {
    height: 1px;
    margin: 0 auto 13px;
    background: var(--gold-rule);
  }
  .hero-title {
    font-size: clamp(33px, 8.6vw, 51px);
  }
  .hero-subtitle {
    margin: 11px auto 16px;
    max-width: 24em;
  }
  .subtitle-continuation {
    display: block;
  }
  .hero-actions {
    justify-content: center;
  }
  .hero-actions .btn {
    min-height: 44px;
    padding: 0 12px;
    font-size: 15px;
  }
  .hero-actions .realm-button {
    min-width: 142px;
    gap: 8px;
    font-size: 17px;
  }
  .today-card {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
    padding: 14px;
  }
  .today-heading {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
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
