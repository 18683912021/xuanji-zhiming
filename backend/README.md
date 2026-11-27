# 玄机知命后端

Python 3.12、FastAPI、SQLAlchemy 异步会话、psycopg 3、PostgreSQL 17、Alembic 和 Docker Compose。目录和前端独立。PC 和 H5 使用同源代理接入，API 放在 `/api/v1`。

## 1. 启动数据库和 API

从项目根目录运行以下命令。

```sh
cd backend
cp .env.example .env
docker compose up -d --build --wait
```

Compose 启动 PostgreSQL，随后运行数据库迁移、导入基础知识，再启动一个 Uvicorn 进程。默认 API 绑定 `127.0.0.1:8000`，数据库留在 Compose 网络，数据保存在 PostgreSQL 命名卷。

- [接口文档](http://127.0.0.1:8000/api/docs)
- [OpenAPI JSON](http://127.0.0.1:8000/api/openapi.json)
- [API 存活检查](http://127.0.0.1:8000/api/health/live)
- [数据库就绪检查](http://127.0.0.1:8000/api/health/ready)

部署时在创建数据库前把 `POSTGRES_PASSWORD` 换成随机十六进制密码，设置 `COOKIE_SECURE=true` 和 `ENVIRONMENT=production`，把实际 HTTPS 源写入 `WEB_ORIGINS`。将 [API 反代配置](deploy/nginx-api.conf) 引入现有 Nginx 的 HTTPS 站点。小服务器上的 Compose 配置给数据库和 API 分别设置了 384 MiB 与 320 MiB 的内存上限。

## 2. 联调核心业务

以下路径均在 `/api/v1` 下。

| 模块 | 接口和行为 |
| --- | --- |
| 账号与会话 | `/auth/status` 返回当前支持的登录方式。`/auth/register` 使用用户名与密码，`/auth/login` 接收用户名或邮箱及密码，`/auth/credentials` 设置跨端账号或更新密码。可通过 `/auth/email/code` 和 `/auth/email/bind` 绑定邮箱，或通过 `/auth/send-code` 和 `/auth/reset-password` 找回密码。小程序支持 `/auth/wechat` 和 `/auth/wechat/bind`。Web 使用 HttpOnly Cookie，小程序使用独立的 Bearer 会话。 |
| 出生档案与日记 | `/me/profiles` 支持新增、查看、编辑和删除。 `/me/journal` 按日期保存与回看，可绑定本人体验结果。 |
| 排盘与占卜 | `POST /readings/bazi` 支持公历、农历闰月、时区和未知时辰。 `/readings/tarot` 提供 78 张牌和五套牌阵， `/readings/daily-tarot` 按账号与选定时区的当地日期保留一张。 `/readings/oracle` 抽原创签文， `/readings/liuyao` 支持三钱模拟与手动录入。 |
| 体验记录 | 执行普通体验时带 `Idempotency-Key`。同一账号、功能及键返回同一次结果，键复用到不同输入返回 409。记录保存输入或档案快照及规则版本，可查、保存、写笔记、删除。 |
| 西洋本命盘 | `POST /readings/astro` 使用 pyephemera 计算盘面，支持普拉西德、等宫制和整宫制、回归或恒星黄道，以及相位容许度。 |
| 轻占卜与梦境 | `/readings/dice`、`/readings/book`、`/readings/dream` 保存对应结果，梦境可以绑定解梦助手。 |
| 分享与基础报告 | `/shares` 生成七天有效的可撤回摘要，`/reports` 按体验快照生成八字、本命盘或回顾报告。 |
| 图鉴、运势、历法 | `/zodiac`、`/zodiac/{sign}`、`/fortune/{sign}`、`/calendar/day`。运势当前使用基础编辑内容，接口用 `content_kind` 标明。 |
| AI 对话 | `/ai/roles`、`/ai/conversations`、`/ai/conversations/{id}/turns`。每个新会话独立保存，读取历史无需模型。发送使用 POST SSE 返回状态和校验后的结果。 |

八字采用当地钟表时间和北京时间节气瞬间，默认在当地午夜分日，也可按 23 时换日。日柱和时干共用同一换日规则。未知时辰时省略时柱，跨节气时保留能够确定的柱。历法输入支持 1901–2099 年，月相依据当地中午的日月黄经差划分八个阶段。 [lunar-python 四柱参考样本](https://github.com/6tail/lunar-python/blob/master/test/EightCharTest.py) · [美国海军天文台月相说明](https://aa.usno.navy.mil/faq/moon_phases)

邮箱验证码配置见 `.env.example`。配置 SMTP 和 `AUTH_CODE_SECRET` 后可绑定邮箱或找回密码，验证码 5 分钟失效，30 秒可重发。绑定邮箱需要当前密码及邮箱验证码。配置 `WECHAT_APP_SECRET` 后启用小程序授权，后端按 AppID 和 OpenID 识别账号。微信用户在小程序重新验证微信身份后，即可为同一账号设置用户名和密码。邮箱为选填，旧邮箱账号仍可用原密码登录。重设密码会撤销旧会话。 [uni.login](https://uniapp.dcloud.net.cn/api/plugins/login.html)

新密码至少 8 个字符。本地开发可在 `.env` 设置 `DEVELOPMENT_ADMIN_PASSWORD` 来预置 `admin`。数据库保存初始密码的哈希，重启会保留已设置的密码。该账号仅在开发模式且密码配置有效时启用。

## 3. 接入 AI 模型与知识库

在 `.env` 设置 `AI_PROVIDER`、`AI_API_KEY`、`AI_MODEL`，重新创建 API 容器。使用官方 DeepSeek 时设 `AI_PROVIDER=deepseek`、`AI_MODEL=deepseek-flash`，省略 `AI_BASE_URL` 即使用官方端点。DeepSeek 对话以非思考模式执行工具调用。`AI_BASE_URL` 可配置自定义服务端点。

使用支持 Embedding 的端点时，可设置 `AI_EMBEDDING_MODEL` 并选择支持输出 1536 维向量的模型，再执行 `seed_knowledge --embed`。DeepSeek 官方聊天端点使用术语检索。

```sh
docker compose up -d --wait
docker compose exec api python -m scripts.seed_knowledge --embed
```

当前包含 AI 塔罗师、占卜师、占星师、解梦助手和报告助手。每轮校验角色和已绑定的体验，裁剪最近六轮历史，按角色检索知识，再由 Pydantic AI 调用只读工具、生成结构化结果并核对引用。内置知识先按术语别名匹配，配置向量后补充 pgvector 相似度查询。塔罗、六爻和个人星盘可带当次结果解读。 [Pydantic AI](https://ai.pydantic.dev/agents/) · [pgvector](https://github.com/pgvector/pgvector)

发送传入 `client_message_id`、`text` 和 `task`。同一会话同时生成一轮；中断或失败后可用相同消息 ID 和 `retry: true` 重试。Agent 在发消息的请求内运行，支持超时与断开取消。SSE 先发 `status`，再发带引用的 `result`。 [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/)

## 4. 开发与验证

```sh
uv sync
uv run ruff check .
uv run python -m pytest -q
```

将 `TEST_DATABASE_URL` 指向独立测试数据库可以运行 PostgreSQL 集成测试。先以该地址作为 `DATABASE_URL` 运行 `uv run alembic upgrade head` 和 `uv run python -m scripts.seed_knowledge`。集成测试使用模型替身验证对话、工具和引用，真实模型联调取决于模型配置。

前端联调与现有示例范围见[前端 README](../frontend/README.md)。进阶盘型、云端深度报告、真人社交和权益服务仍属后续范围。支付保持关闭。
