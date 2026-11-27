import { dateKey } from '../../shared/storage'
import { accountStore } from '../../shared/api'

export interface Product {
  id: string
  title: string
  spec: string[]
  description: string
  glyph: string
  stock: number
  price: number
}
export const products: Product[] = [
  {
    id: 'journal',
    title: '星象观察手札',
    spec: ['玄夜紫 · 64 页', '烟雾紫 · 64 页'],
    description: '节气写生、月相小记与日常观察的留白页。',
    glyph: '▤',
    stock: 12,
    price: 36,
  },
  {
    id: 'cards',
    title: '紫曜塔罗图鉴卡',
    spec: ['基础图鉴 · 22 张', '完整图鉴 · 78 张'],
    description: '原创紫曜配色的牌义图鉴示例，用来学习牌位与正逆位。',
    glyph: '✧',
    stock: 8,
    price: 62,
  },
  {
    id: 'print',
    title: '东方星宿折页',
    spec: ['月白纸', '夜紫纸'],
    description: '四象与二十八星宿的中文索引示例。',
    glyph: '⋇',
    stock: 15,
    price: 22,
  },
]
export interface Address {
  id: string
  name: string
  district: string
  line: string
  isDefault: boolean
}
export interface Order {
  id: string
  product: string
  spec: string
  qty: number
  amount: number
  destination: string
  createdAt: string
  status: '模拟待确认' | '模拟已确认' | '已取消' | '模拟售后'
}
export const wallet = accountStore('wallet', {
  balance: 20,
  lastCheckIn: '',
  lastInvite: '',
  ledger: [{ id: 'initial', delta: 20, title: '体验赠送', day: dateKey() }],
})
export const productFavorites = accountStore<string[]>('product-favorites', [])
export const addresses = accountStore<Address[]>('demo-addresses', [
  { id: 'demo', name: '演示收件人', district: '示例城市', line: '样例路 01 号', isDefault: true },
])
export const orders = accountStore<Order[]>('demo-orders', [])
