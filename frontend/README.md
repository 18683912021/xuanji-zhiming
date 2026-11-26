# 玄机知命 · 前端

PC、H5 和微信小程序共用 uni-app Vue 3、TypeScript 和 Vite 工程。PC 与 H5 使用同一份 Web 构建，桌面断点展开首页双栏、常用工具、排盘工作区和会话侧栏。H5 和小程序共用移动布局、页面内容、交互及 Mock 数据。微信小程序 AppID 为 `wx99173f0f5cf30a60`。

| 目录 | 内容 |
| --- | --- |
| `apps/client/src/pages` | 首页、探索、今日、AI、个人中心、排盘、占卜、社交和权益九组路由 |
| `apps/client/src/features` | 页面所属的领域逻辑、示例资料和本机存储。排盘及起卦保留已有计算，专业盘和解读主要使用 Mock |
| `apps/client/src/components` | 导航、页面外壳、表单控件和横滑数据表 |
| `apps/client/src/shared` | 路由构建、存储和日期工具 |
| `packages/theme` | 三端共用的紫曜 V2 颜色和字体 |
| `assets/art/home` | 首页效果图及星轨背景原图 |
| `assets/art/icons` | 25 枚鎏金图标的透明原稿及生成提示。统一的 PNG 导出位于客户端静态资源目录 |

## 启动和构建

在本目录运行：

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm typecheck
pnpm build
```

- Web 预览使用 Vite 打印的地址。桌面与手机宽度分别显示 PC 和 H5 布局。生产产物在 `apps/client/dist/build/h5/`。
- 微信小程序产物在 `apps/client/dist/build/mp-weixin/`。在微信开发者工具选择该目录导入。需要持续编译时运行 `pnpm dev:mp-weixin`，导入 `apps/client/dist/dev/mp-weixin/`。
- 一级导航为首页、探索、今日、AI 对话、我的。页面入口由 `pages.json` 注册，各业务组通过 `view` 选择录入、详情或历史等页面。例如 `/pages/divination/index?view=tarot` 是塔罗问事。

## Mock 体验

- 可以直接抽牌、排基础八字、起卦和查看运势。结果可保存、写笔记、加日记、生成 Mock 报告，也可带入 AI 角色。
- 首次进入 AI 对话可用体验登录。对话各自保存历史，发送后才模拟生成，历史可续聊、重命名或删除。
- 档案、记录、日记、匹配、私聊、分享、星币和模拟订单保存在当前客户端。分享链接在同一份本机数据里预览。支付入口提供权益说明。
- 运营后台后续单独开发。正式账号、跨端同步、专业排盘服务和真实 AI 接口留待后端联调。

[产品规划](../产品规划.md) · [技术架构与开发规划](../技术架构与开发规划.md) · [紫曜视觉体系 V2](../美术设计方向.md)
