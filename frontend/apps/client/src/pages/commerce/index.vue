<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AppShell from '../../components/AppShell.vue'
import AppSwitch from '../../components/AppSwitch.vue'
import NavLink from '../../components/NavLink.vue'
import SelectField from '../../components/SelectField.vue'
import SectionHeading from '../../components/SectionHeading.vue'
import { remaining } from '../../features/ai/state'
import {
  addresses,
  orders,
  productFavorites,
  products,
  wallet,
  type Address,
  type Order,
} from '../../features/commerce/state'
import { confirmAction, destination, go, toast, type Query } from '../../shared/navigation'
import { dateKey, makeId } from '../../shared/storage'

const query = ref<Query>({})
const titles: Record<string, string> = {
  index: '体验权益',
  member: '会员中心',
  wallet: '星币与任务',
  referral: '邀请体验',
  shop: '珍宝阁',
  product: '商品详情',
  addresses: '模拟收货地址',
  address: '编辑模拟地址',
  checkout: '模拟结算',
  orders: '模拟订单',
  order: '模拟订单详情',
  payment: '支付说明',
}
const view = computed(() => (query.value.view && Object.prototype.hasOwnProperty.call(titles, query.value.view) ? query.value.view : 'index'))
const product = computed(() => products.find((item) => item.id === query.value.id))
const spec = ref('')
const quantity = ref(1)
const addressId = ref('')
const edit = ref<Address>({ id: '', name: '', district: '', line: '', isDefault: false })
const order = computed(() => orders.state.value.find((item) => item.id === query.value.id))
const onlyFavorites = ref(false)
const orderStatus = ref('全部')
const coupon = ref('')
const trial = ref(false)
const status = ref('')

onLoad((params) => {
  query.value = params || {}
  spec.value =
    query.value.spec && product.value?.spec.includes(query.value.spec)
      ? query.value.spec
      : product.value?.spec[0] || ''
  addressId.value =
    addresses.state.value.find((item) => item.isDefault)?.id || addresses.state.value[0]?.id || ''
  const existing = addresses.state.value.find((item) => item.id === query.value.id)
  if (existing) edit.value = { ...existing }
})
const addressOptions = computed(() =>
  addresses.state.value.map((item) => ({ value: item.id, label: item.name + ' · ' + item.district })),
)
function earn(kind: 'lastCheckIn' | 'lastInvite') {
  if (wallet.state.value[kind] === dateKey()) return
  const amount = kind === 'lastCheckIn' ? 3 : 5
  const state = wallet.state.value
  wallet.write({
    ...state,
    [kind]: dateKey(),
    balance: state.balance + amount,
    ledger: [
      {
        id: makeId(),
        delta: amount,
        title: kind === 'lastCheckIn' ? '每日签到' : '模拟邀请奖励',
        day: dateKey(),
      },
      ...state.ledger,
    ],
  })
}
function favorite() {
  if (!product.value) return
  const id = product.value.id
  const values = productFavorites.state.value
  productFavorites.write(values.includes(id) ? values.filter((item) => item !== id) : [id, ...values])
}
function saveAddress() {
  if (!(edit.value.name.trim() && edit.value.district.trim() && edit.value.line.trim())) return
  const value = { ...edit.value, id: edit.value.id || makeId() }
  const others = addresses.state.value.filter((item) => item.id !== value.id)
  if (!others.length) value.isDefault = true
  if (
    addresses.write([
      value,
      ...others.map((item) => (value.isDefault ? { ...item, isDefault: false } : item)),
    ])
  )
    go(destination('commerce', 'addresses'), 'replace')
}
function removeAddress(item: Address) {
  confirmAction('删除模拟地址', '从本机移除此地址。', () => {
    const remaining = addresses.state.value.filter((entry) => entry.id !== item.id)
    if (item.isDefault && remaining[0]) remaining[0] = { ...remaining[0], isDefault: true }
    addresses.write(remaining)
  })
}
function placeOrder() {
  const item = product.value
  const address = addresses.state.value.find((entry) => entry.id === addressId.value)
  if (!item || !address || !item.spec.includes(spec.value)) return toast('请核对规格和模拟地址。')
  const draft: Order = {
    id: makeId(),
    product: item.title,
    spec: spec.value,
    qty: quantity.value,
    amount: item.price * quantity.value,
    destination: address.district + ' · ' + address.line,
    createdAt: dateKey(),
    status: '模拟待确认',
  }
  if (orders.write([draft, ...orders.state.value]))
    go(destination('commerce', 'order', { id: draft.id }), 'replace')
}
function updateOrder(next: Order['status']) {
  const id = order.value?.id
  if (!id) return
  orders.write(orders.state.value.map((item) => (item.id === id ? { ...item, status: next } : item)))
}
</script>

<template>
  <AppShell section="commerce" :title="titles[view]" :detail="view !== 'index'">
    <view class="content-width stack">
      <text class="notice">免费体验 · 订单与价格为 Mock 示例，真实支付关闭。</text>
      <template v-if="view === 'index'">
        <view class="cols-3">
          <NavLink class="panel stack" :to="destination('commerce', 'member')"
            ><text class="panel-head">会员权益</text
            ><text class="muted">AI {{ remaining.ai }} 次 · 报告 {{ remaining.reports }} 次</text
            ><text class="gold">查看说明 ›</text></NavLink
          >
          <NavLink class="panel stack" :to="destination('commerce', 'wallet')"
            ><text class="panel-head">星币与任务</text
            ><text class="muted">本机体验余额 {{ wallet.state.value.balance }}</text
            ><text class="gold">签到与流水 ›</text></NavLink
          >
          <NavLink class="panel stack" :to="destination('commerce', 'shop')"
            ><text class="panel-head">珍宝阁</text><text class="muted">浏览样品和模拟规格</text
            ><text class="gold">打开目录 ›</text></NavLink
          >
        </view>
        <view class="actions"
          ><NavLink class="btn" :to="destination('commerce', 'orders')">模拟订单</NavLink
          ><NavLink class="btn" :to="destination('commerce', 'addresses')">模拟收货地址</NavLink></view
        >
      </template>
      <template v-else-if="view === 'member'">
        <view class="panel stack"
          ><text class="panel-head">免费体验权益</text
          ><text>每日 AI 追问 8 次，深度报告 3 次。跨日恢复额度。</text>
          <text class="gold">剩余 AI {{ remaining.ai }} 次 · 报告 {{ remaining.reports }} 次</text>
          <view class="row"
            ><text>内测权益卡</text><text>{{ trial ? '已兑换 · 本次演示' : '可用演示码 XUANJI' }}</text></view
          >
          <input v-if="!trial" v-model="coupon" class="field" maxlength="20" placeholder="输入演示兑换码" />
          <button
            v-if="!trial"
            class="btn primary"
            :disabled="!coupon.trim()"
            @tap="
              coupon.trim().toUpperCase() === 'XUANJI' ? (trial = true) : (status = '兑换码无效，请核对。')
            "
          >
            体验兑换
          </button>
          <text v-if="status && !trial" class="error">{{ status }}</text>
        </view>
      </template>
      <template v-else-if="view === 'wallet'">
        <view class="split"
          ><view class="panel stack"
            ><text class="panel-head">体验星币 {{ wallet.state.value.balance }}</text
            ><button
              class="btn primary"
              :disabled="wallet.state.value.lastCheckIn === dateKey()"
              @tap="earn('lastCheckIn')"
            >
              {{ wallet.state.value.lastCheckIn === dateKey() ? '今日已签到' : '签到领取 3 星币' }}
            </button>
            <NavLink class="btn" :to="destination('commerce', 'referral')">邀请奖励</NavLink></view
          >
          <view class="panel stack"
            ><text class="panel-head">获得记录</text
            ><view v-for="item in wallet.state.value.ledger" :key="item.id" class="row"
              ><text>{{ item.title }} · {{ item.day }}</text
              ><text class="gold">+{{ item.delta }}</text></view
            ></view
          ></view
        >
      </template>
      <template v-else-if="view === 'referral'">
        <view class="panel stack"
          ><text class="panel-head">邀请好友体验玄机知命</text
          ><text class="muted">Mock 邀请码 · XUANJI26。模拟一次邀请落地后，可记录体验星币奖励。</text>
          <view class="actions"
            ><button class="btn" @tap="copyCode">复制邀请码</button>
            <button
              class="btn primary"
              :disabled="wallet.state.value.lastInvite === dateKey()"
              @tap="earn('lastInvite')"
            >
              {{ wallet.state.value.lastInvite === dateKey() ? '今日奖励已记录' : '模拟邀请完成' }}
            </button></view
          ></view
        >
      </template>
      <template v-else-if="view === 'shop'">
        <view class="actions"
          ><button class="chip" :class="{ selected: onlyFavorites }" @tap="onlyFavorites = !onlyFavorites">
            {{ onlyFavorites ? '显示全部' : '只看收藏' }}</button
          ><NavLink class="btn" :to="destination('commerce', 'orders')">模拟订单</NavLink></view
        >
        <view class="cols-3"
          ><NavLink
            v-for="item in products.filter(
              (entry) => !onlyFavorites || productFavorites.state.value.includes(entry.id),
            )"
            :key="item.id"
            class="panel stack product-card"
            :to="destination('commerce', 'product', { id: item.id })"
          >
            <text class="product-icon">{{ item.glyph }}</text
            ><text class="panel-head">{{ item.title }}</text
            ><text class="muted">{{ item.description }}</text
            ><text class="gold">示例价 ¥{{ item.price }}</text></NavLink
          ></view
        >
        <text v-if="onlyFavorites && !productFavorites.state.value.length" class="muted"
          >还没有收藏样品。</text
        >
      </template>
      <template v-else-if="view === 'product' || view === 'checkout'">
        <view v-if="product" class="split">
          <view class="panel stack product-card"
            ><text class="product-icon">{{ product.glyph }}</text
            ><text class="panel-head">{{ product.title }}</text
            ><text class="muted">{{ product.description }}</text
            ><text class="gold">示例价 ¥{{ product.price }} · 样例库存 {{ product.stock }}</text></view
          >
          <view class="panel stack"
            ><SelectField
              v-model="spec"
              label="规格"
              :options="product.spec.map((value) => ({ value, label: value }))"
            />
            <template v-if="view === 'product'"
              ><button class="btn" @tap="favorite">
                {{ productFavorites.state.value.includes(product.id) ? '取消收藏' : '收藏样品' }}
              </button>
              <NavLink class="btn primary" :to="destination('commerce', 'checkout', { id: product.id, spec })"
                >预览模拟结算</NavLink
              ></template
            >
            <template v-else>
              <SelectField v-model="addressId" label="模拟收货地址" :options="addressOptions" /><NavLink
                class="link"
                :to="destination('commerce', 'addresses')"
                >管理模拟地址 ›</NavLink
              >
              <view class="actions"
                ><text>数量</text><button class="btn" :disabled="quantity <= 1" @tap="quantity--">−</button
                ><text>{{ quantity }}</text
                ><button class="btn" :disabled="quantity >= product.stock" @tap="quantity++">+</button></view
              >
              <text class="gold">模拟合计 ¥{{ product.price * quantity }}</text
              ><button class="btn primary" @tap="placeOrder">创建模拟订单</button>
            </template>
          </view>
        </view>
        <text v-else class="panel muted">未找到这个演示商品。</text>
      </template>
      <template v-else-if="view === 'addresses'">
        <view class="actions"
          ><NavLink class="btn primary" :to="destination('commerce', 'address')">添加模拟地址</NavLink></view
        >
        <view class="panel stack"
          ><view v-for="item in addresses.state.value" :key="item.id" class="row">
            <view
              ><text class="block">{{ item.name }}{{ item.isDefault ? ' · 默认' : '' }}</text
              ><text class="muted small">{{ item.district }} · {{ item.line }}</text></view
            >
            <view class="actions"
              ><NavLink class="link" :to="destination('commerce', 'address', { id: item.id })">编辑</NavLink
              ><button class="link" @tap="removeAddress(item)">删除</button></view
            > </view
          ><text v-if="!addresses.state.value.length" class="muted">还没有模拟收货地址。</text></view
        >
      </template>
      <template v-else-if="view === 'address'">
        <view class="panel stack"
          ><text class="notice">请填写虚构信息用于演示。</text>
          <view
            ><text class="field-label">收件人</text><input v-model="edit.name" class="field" maxlength="20"
          /></view>
          <view
            ><text class="field-label">地区</text><input v-model="edit.district" class="field" maxlength="30"
          /></view>
          <view
            ><text class="field-label">详细地址</text><input v-model="edit.line" class="field" maxlength="60"
          /></view>
          <view class="switch-row"
            ><text>设为默认</text
            ><AppSwitch label="设为默认" :checked="edit.isDefault" @change="edit.isDefault = $event"
          /></view>
          <button class="btn primary" @tap="saveAddress">保存模拟地址</button></view
        >
      </template>
      <template v-else-if="view === 'orders'">
        <view class="chips"
          ><button
            v-for="item in ['全部', '模拟待确认', '模拟已确认', '已取消', '模拟售后']"
            :key="item"
            class="chip"
            :class="{ selected: orderStatus === item }"
            @tap="orderStatus = item"
          >
            {{ item }}
          </button></view
        >
        <view class="panel stack">
          <NavLink
            v-for="item in orders.state.value.filter(
              (item) => orderStatus === '全部' || item.status === orderStatus,
            )"
            :key="item.id"
            class="row-link"
            :to="destination('commerce', 'order', { id: item.id })"
          >
            <view
              ><text class="block">{{ item.product }}</text
              ><text class="muted small">{{ item.createdAt }} · {{ item.spec }}</text></view
            ><text class="gold">{{ item.status }} ›</text>
          </NavLink>
          <text
            v-if="!orders.state.value.some((item) => orderStatus === '全部' || item.status === orderStatus)"
            class="muted"
            >暂无该状态的模拟订单。</text
          >
        </view>
      </template>
      <template v-else-if="view === 'order'">
        <view v-if="order" class="panel stack"
          ><text class="panel-head">{{ order.product }} · {{ order.status }}</text>
          <text>{{ order.spec }} × {{ order.qty }} · 模拟金额 ¥{{ order.amount }}</text
          ><text class="muted">{{ order.destination }}</text>
          <view v-if="order.status === '模拟待确认'" class="actions"
            ><button class="btn primary" @tap="updateOrder('模拟已确认')">模拟确认</button
            ><button class="btn" @tap="updateOrder('已取消')">取消</button></view
          >
          <button v-if="order.status === '模拟已确认'" class="btn" @tap="updateOrder('模拟售后')">
            演示售后申请
          </button>
          <NavLink class="link" :to="destination('commerce', 'orders')">全部模拟订单 ›</NavLink> </view
        ><text v-else class="panel muted">未找到这笔模拟订单。</text>
      </template>
      <view v-else class="panel stack"
        ><text class="panel-head">当前为免费体验</text><text>可以浏览权益，交易入口关闭。</text
        ><NavLink class="btn primary" :to="destination('commerce')">查看体验权益</NavLink></view
      >
    </view>
  </AppShell>
</template>
<script lang="ts">
function copyCode() {
  uni.setClipboardData({ data: 'XUANJI26' })
}
</script>
<style scoped>
.product-card {
  background:
    radial-gradient(ellipse at 25% 13%, #67477358, #21152f00 66%), linear-gradient(150deg, #30203d, #1e142b);
}
</style>
