# 玄机知命 · 前端

本目录包含 PC、H5、微信小程序和前端共享配色。项目根目录的四份规划文档可以单独阅读。运营后台由后续独立交付。

| 路径 | 内容 |
| --- | --- |
| `apps/web` | Vue 3、TypeScript、Vite、Vue Router 和 Pinia。PC、H5 使用同一套响应式代码 |
| `apps/miniprogram` | uni-app Vue 3 微信小程序。AppID 为 `wx99173f0f5cf30a60` |
| `packages/theme` | 三端共享的紫曜 V2 色值和字体设定 |
| `assets/art/home` | 确认的首页效果图与无字星轨背景原图。前端运行时使用压缩后的资源 |

## 代码怎么找

```text
apps/web/src/
├── main.ts、App.vue、router.ts     启动、应用外壳和路由入口
├── layout/                       页头、导航和登录提示
├── features/                     首页、八字、塔罗、六爻等业务模块
│   └── experiences/              体验结果入口、本机记录和对话
├── shared/                       通用组件、日期格式化和浏览器存储
└── styles/                       全站基础样式、表单和按钮

apps/miniprogram/src/
├── pages/                        与 pages.json 对应的小程序页面
├── features/                     节气数据与日记存储
└── styles/                       小程序全局样式
```

以八字为例，表单在 `features/bazi/BaziView.vue`，计算在 `chart.ts`，结果显示在 `BaziResult.vue`。结果页根据记录类型选用对应的结果组件。保存、编辑笔记、开启对话等操作由 `features/experiences/store.ts` 处理，记录的数据结构和读写分别在 `model.ts` 与 `repository.ts`。

新增 Web 功能时，把页面、业务逻辑和专用样式放进同一模块，再在 `router.ts` 注册入口。Web 专用组件留在 Web，小程序页面按 uni-app 的目录规则注册。三端共用的色值和字体在 `packages/theme/tokens.css`。

## 本地启动

在 `frontend/` 中执行：

```sh
pnpm install --frozen-lockfile
pnpm dev
```

浏览器打开 Vite 打印的本地地址。使用桌面宽度浏览 PC 首页，窄屏自动切换到 H5。

## 构建和导入微信开发者工具

```sh
pnpm typecheck
pnpm build
```

Web 产物在 `apps/web/dist/`。小程序产物在 `apps/miniprogram/dist/build/mp-weixin/`，其中的 `project.config.json` 以下发的 AppID 编译。将这个目录导入微信开发者工具可查看。开发时可执行 `pnpm dev:mp-weixin`，导入 `apps/miniprogram/dist/dev/mp-weixin/`。

## 体验范围

- Web 实现首页及四个功能卡，支持塔罗单张或三张抽取、八字基础排盘、三钱及手动录入六爻、问签、星座周期主题、梦境记录、笔记和本机体验记录。基础排盘按输入的当地钟表时间计算，未知时辰使用日期正午作为三柱参考。塔罗牌库当前提供 22 张大阿尔卡那。
- 解读对话支持新建独立会话、关联结果、本机保存问题及回看。登录、跨端同步和实时 AI 解读有待后端接口联调。
- 小程序提供今日节气、二十四节气图鉴及私人日记的创建、编辑、查看和删除。日记保存在当前设备。

[产品规划](../产品规划.md) · [技术架构与开发规划](../技术架构与开发规划.md) · [紫曜视觉体系 V2](../美术设计方向.md)
