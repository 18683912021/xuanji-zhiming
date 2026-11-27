# 玄机知命 · 前端

PC、H5 和微信小程序共用 uni-app Vue 3、TypeScript 和 Vite 工程。PC 与 H5 使用同一份 Web 构建，桌面断点展开首页双栏、常用工具、排盘工作区和会话侧栏。H5 和小程序共用移动布局、页面内容和业务逻辑。微信小程序 AppID 为 `wx99173f0f5cf30a60`。

| 目录 | 内容 |
| --- | --- |
| `apps/client/src/pages` | 首页、探索、今日、AI、个人中心、排盘、占卜、社交和权益九组路由 |
| `apps/client/src/features` | 领域逻辑、API 数据转换、前端计算与示例资料 |
| `apps/client/src/components` | 导航、页面外壳、表单控件和横滑数据表 |
| `apps/client/src/shared` | 统一 API、会话、SSE、路由、存储与日期工具 |
| `packages/theme` | 三端共用的紫曜 V2 颜色和字体 |
| `apps/client/src/static` | 页面实际加载的首页背景、登录和注册背景、鎏金图标 |

## 启动和构建

先在 [后端目录](../backend/README.md) 启动 API 和 PostgreSQL，再在前端目录运行。

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm typecheck
pnpm build
```

- Web 预览使用 Vite 打印的地址。桌面与手机宽度分别显示 PC 和 H5 布局。生产产物在 `apps/client/dist/build/h5/`。
- 微信小程序产物在 `apps/client/dist/build/mp-weixin/`。在微信开发者工具选择该目录导入。需要持续编译时运行 `pnpm dev:mp-weixin`，导入 `apps/client/dist/dev/mp-weixin/`。
- 一级导航为首页、探索、今日、AI 对话、我的。页面入口由 `pages.json` 注册，各业务组通过 `view` 选择录入、详情或历史等页面。登录和注册分别使用 `/pages/login/index` 和 `/pages/register/index`。例如 `/pages/divination/index?view=tarot` 是塔罗问事。

## 当前联调范围

| 模块 | 数据来源 |
| --- | --- |
| 账号、档案与记录 | 注册使用用户名和密码，邮箱可稍后绑定。PC、H5 和小程序可用用户名或已验证的邮箱与密码登录。微信用户在小程序内设置用户名和密码后，即可用原账号跨端登录。注册保留游客记录，登录已有账号可带入选定的游客体验。 |
| 核心体验 | 八字、塔罗牌阵和日签、六爻、问签、星骰、答案之书与梦境记录走真实 API。星座图鉴、农历和节气读后端，运势使用基础编辑内容。 |
| 西洋本命盘 | 根据出生时刻、时区、经纬度和宫制计算星体、宫头、上升点、天顶、相位与逆行。用户可以把持久化盘面带入 AI 占星对话。 |
| AI 与报告 | 云端角色通过 SSE 发消息，支持历史、新会话、引用、重试和停止。八字、星盘和回顾基础报告由体验快照生成并按账号保存。 |
| 本机体验 | 紫微、进阶流运和合盘、真人社交、试用权益、商城、部分报告和私有角色仍是本机示例。支付保持关闭。 |

本地 PC 和 H5 通过 Vite 将同源 `/api` 代理至 `127.0.0.1:8000`。部署时由 Nginx 转发同源 `/api`。需独立演示本机数据时可以运行 `VITE_XUANJI_MODE=mock pnpm dev`。

小程序联调时为构建提供 `VITE_XUANJI_API_ORIGIN`，值为已在微信后台登记的 HTTPS API 域名。小程序使用服务端 Bearer 凭证及请求分块接口，Web 使用 Cookie。微信登录与绑定由后端的 `WECHAT_APP_SECRET` 启用，该值只配置在后端。在「设置与隐私」可管理跨端登录账号和邮箱绑定。已绑定微信的用户还可以在小程序通过微信验证重设密码。 [uni.request 文档](https://uniapp.dcloud.net.cn/api/request/request.html) · [uni.login 文档](https://uniapp.dcloud.net.cn/api/plugins/login.html)

[产品规划](../产品规划.md) · [技术架构与开发规划](../技术架构与开发规划.md) · [紫曜视觉体系 V2](../美术设计方向.md)
