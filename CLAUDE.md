# CLAUDE.md

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文为 Claude Code（claude.ai/code）在本仓库中工作时提供项目说明和约束。

## 项目简介

家教辅助系统：单老师模式的教学管理工具，包含 Web 管理端（老师用）、学生 Web 端（学生/家长用）和微信小程序（学生/家长用）。

## 当前项目状态（2026-04-28）

当前活跃基线已经切换到“老师端 V2 重构”，不是旧版并列模块式后台。

文档归集、查找顺序和 vibecoding 后的文档收口流程见：
- `docs/00-index.md`
- `docs/04-implementation/development-usage-guide.md`
- `docs/04-implementation/documentation-workflow.md`
- `docs/04-implementation/doc-map.md`
- `docs/08-progress/project-status.md`

## AI 编码工作流适配

本项目执行本地通用技能：

- `ai-coding-workflow`：用于开发、修复、重构、性能定位、测试刷新和代码改动。
- `document-governance-workflow`：用于创建、更新、归档、整理文档，维护变更记录、进度记录、checkpoint 和文档地图。
- `agent-orchestration-workflow`：用于多 agent 调度、子 agent 任务书、ownership、结果审计和上下文隔离。

使用 Claude Code 处理开发、修复、重构、测试刷新和文档治理时，先按对应 skill 进行任务分级、最小上下文读取、Phase/Gate 控制、验证和交接；再结合本文的当前基线、项目结构、命令、测试策略和文档沉淀规则执行。

任务涉及多个独立工作流、跨模块并行、上下文压力较大，或需要创建子 agent 时，使用 `agent-orchestration-workflow`。主 agent 必须保留任务分级、Gate、ownership 分配、结果审计和最终交接职责。

本项目适配说明见：`docs/04-implementation/development-usage-guide.md`。

本项目的最小启动上下文为：

- `docs/00-index.md`
- `docs/01-product/current.md`
- `docs/01-product/teacher-v2/status.md`
- `docs/08-progress/project-status.md`

本项目的高风险业务包括：课程状态流转、自动扣费、充值、余额回滚、批量复制课程、鉴权、删除和跨端学生信息展示。涉及这些内容时，至少按通用工作流中的 L 级任务处理。

优先参考这些文档：
- `docs/01-product/current.md` — 当前产品基线入口
- `docs/01-product/teacher-v2/status.md` — 当前进度总览
- `docs/01-product/teacher-v2/prd.md` — 当前产品基线
- `docs/02-design/teacher-v2/prototype.md` — 当前老师端原型基线
- `docs/04-implementation/teacher-v2/plan.md` — 当前实现拆解和阶段状态
- `docs/08-progress/project-status.md` — 当前进行态和多人并行工作流

如果任务未完成但需要暂停、换人接手或下次继续，生成 checkpoint 断点快照：

```bash
node scripts/create-checkpoint.mjs --workstream <workstream> --owner claude
node scripts/check-progress.mjs
```

checkpoint 生成后，应根据当前对话补齐本次目标、已完成、未完成、风险与下一步。

旧文档 `docs/99-archive/legacy/product/prd-v1.md`、`docs/99-archive/legacy/design/web-wireframes-v1.md` 仅用于历史对照，不应作为新改动的默认依据。

老师端 V2 已进入“老师端主链路基本收口”的阶段。已落地的关键能力：
- 工作台：`/dashboard`
- 课程 7 天周视图：`/courses`
- 复制上一周课程：预览 + 确认
- 课程编辑 / 完成 / 取消
- 学生账户 Tab
- 收费与账户页重构
- 预收充值：`POST /api/billing/recharge`
- 设置页
- 作业中心、反馈复盘、学习复盘的一轮页面收口
- 课程详情中填写课后记录、可选布置作业并完成课程
- 完成课程自动扣费
- 取消 / 删除已完成课程后的自动扣费回滚
- 请假 / 待补课池 / 安排补课
- 学生详情账户、课后反馈、学习复盘 Tab

仍在收尾中的方向：
- 学生端按 V2 方案继续重构
- 管理端 browser-use 全量回归记录按最新实现重新执行并刷新
- 老师端后续性能优化在完成回归后再评估

## 开发命令

### 启动数据库
```bash
docker-compose up -d        # 使用 postgres:16-alpine 启动 PostgreSQL（localhost:5432）
docker-compose down         # 停止
```

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API 文档：http://localhost:8000/api/docs
# ReDoc：http://localhost:8000/api/redoc
```

首次启动自动建表并创建默认账户 `admin/admin123` 及 8 个科目单价（由 `app/main.py` 的 `lifespan` 处理）。

### 数据库迁移（Alembic）
```bash
cd backend
alembic revision --autogenerate -m "描述"  # 生成迁移脚本
alembic upgrade head                        # 执行迁移
alembic downgrade -1                        # 回退一步
```

注意：`alembic/versions/` 目前为空，开发环境靠 lifespan 自动建表；生产部署前需生成初始迁移。

### 前端（管理端）
```bash
cd admin-web
npm install
npm run dev                 # 启动前端（localhost:3000）
npm run build               # 生产构建（含 tsc 类型检查）
npm run preview             # 预览构建产物
```

前端环境变量在 `admin-web/.env.development`，`VITE_API_BASE_URL` 控制 API 地址。

### 学生端
```bash
cd student-web
npm install
npm run dev                 # 启动学生端（localhost:3001）
npm run build               # 生产构建（含 tsc 类型检查）
```

学生端使用独立 token 存储（`student_access_token`），与管理端隔离。学生需由老师在管理端设置 Web 登录用户名/密码后方可登录。

### 测试
```bash
cd backend
pytest tests/ -v                                  # 运行全部测试
pytest tests/test_courses.py -v                   # 运行单个模块
pytest tests/test_courses.py::TestConflictDetection -v  # 运行单个测试类
pytest tests/test_courses.py::TestConflictDetection::test_overlapping -v  # 运行单个测试
pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q
```

测试使用 SQLite 内存数据库（`aiosqlite`），无需启动 PostgreSQL。`pytest.ini` 配置了 `asyncio_mode=auto`。

## 架构概览

```
djy2ty/
├── backend/        # FastAPI 后端
├── admin-web/      # React 管理端（老师用，端口 3000）
├── student-web/    # React 学生端（学生用，端口 3001，移动端优先）
├── miniprogram/    # 微信小程序
└── docs/           # 分层项目文档
    ├── 00-index.md
    ├── 01-product/
    ├── 02-design/
    ├── 03-architecture/
    ├── 04-implementation/
    ├── 05-testing/
    ├── 06-ai-worklogs/
    ├── 07-changes/
    ├── 08-progress/
    └── 99-archive/
```

## 后端架构（backend/）

### 请求流转
```
HTTP Request
  → Nginx (生产)
  → FastAPI Middleware (日志、CORS)
  → Router (app/routers/*.py)
  → Depends(get_admin_user | get_student_user)  ← 权限检查
  → Depends(get_db)                              ← 获取 AsyncSession
  → 业务逻辑 + SQLAlchemy ORM
  → Response
```

### 目录结构
- `app/models/` — SQLAlchemy ORM 模型，继承自 `app/database.py` 的 `Base`
- `app/schemas/` — Pydantic v2 请求/响应模型
- `app/routers/` — 路由，每个模块独立文件，统一注册到 `app/main.py`
- `app/dependencies.py` — 核心依赖函数，见下方

### 权限依赖（app/dependencies.py）
- `get_current_user` — 验证 JWT，返回 User 对象，所有需要登录的接口使用
- `get_admin_user` — 仅 `role=admin`（老师）可访问
- `get_student_user` — `admin/student/parent` 均可访问
- `get_current_student` — 小程序端专用，从 JWT 中反查 Student 档案

### 关键业务约定
- **课程冲突检测**：`courses.py` 中 `check_time_conflict()` 使用区间重叠算法 `A.start < B.end AND A.end > B.start`，已取消的课程不参与检测
- **软删除**：`Student` 使用 `is_active=False`，查询时需过滤
- **收费快照**：`Course.hourly_rate` 存储创建时的单价，防止后续修改影响历史账单
- **收费按记录独立计算**：每条 BillingRecord 独立跟踪 `amount`/`paid_amount`/`status`，多付的金额不会自动分配到其他记录
- **V2 收费模型**：当前老师端主流程以“预收余额”理解收费。`BillingRecord` 仍是底层记录表，但页面和接口应优先服务“余额、扣费、收费提醒”，而不是传统账单后台思维
- **预收充值接口**：`POST /api/billing/recharge` 会写入 `amount=0`、`paid_amount>0` 的记录，用于直接增加学生余额
- **老师工作台聚合**：`GET /api/dashboard/workbench` 是当前老师端首页的主接口
- **课程周视图**：`GET /api/courses/week` 返回完整 7 天课程与收费风险信息
- **复制上一周课程**：`POST /api/courses/copy-week-preview` / `POST /api/courses/copy-week-confirm`
- **学生账户概览**：`GET /api/billing/students/{id}/account`
- **小程序端接口**：路径通常为 `/api/xxx/my`，依赖 `get_current_student` 自动按学生过滤
- **文件上传**：`app/utils/file_handler.py` 处理，存储到 `backend/uploads/YYYY/MM/uuid.ext`

### 数据库
- 异步引擎：`asyncpg`，连接池参数（pool_size=5/max_overflow=5）仅 PostgreSQL 生效，SQLite 自动跳过（见 `database.py` 条件判断）
- Session 通过 `Depends(get_db)` 注入，自动 commit/rollback
- 生产迁移用 Alembic（`alembic upgrade head`），开发环境 lifespan 自动建表

### 配置
所有配置在 `app/config.py`（Pydantic Settings），从 `backend/.env` 读取。关键变量：
- `DATABASE_URL` — 数据库连接串（默认 `postgresql+asyncpg://postgres:password@localhost:5432/tutoring_assistant`）
- `SECRET_KEY` — JWT 签名密钥（生产环境必须修改）
- `DEBUG=True` — 控制自动建表和 CORS 宽松策略
- `WECHAT_APP_ID / WECHAT_APP_SECRET` — 微信小程序配置
- `UPLOAD_DIR=./uploads` — 上传目录（相对于 backend/，运行时转为绝对路径）
- `MAX_FILE_SIZE=52428800` — 单文件上传限制（50MB）

## 前端架构（admin-web/）

### 技术栈
React 18 + TypeScript + Ant Design 5 + Vite + Zustand + Axios + Recharts + React Quill（富文本）+ Day.js

### 关键约定
- **API 客户端**：`src/api/client.ts` 统一管理 axios 实例，含自动 token 注入和 401 自动刷新逻辑。各模块 API 函数在 `src/api/*.ts`
- **认证状态**：`src/store/authStore.ts`（Zustand + localStorage 持久化），`isAuthenticated` 控制路由守卫
- **路由守卫**：未登录时重定向到 `/login`，在 `src/App.tsx` 中处理
- **API 代理**：开发环境 `/api/*` 由 Vite 代理到 `localhost:8000`（`vite.config.ts`，`changeOrigin: true`）
- **Token 存储**：localStorage `access_token`
- **老师端 V2 导航语义**：`工作台 / 学生 / 课程 / 作业 / 反馈复盘 / 学习复盘 / 收费与账户 / 资料 / 设置`
- **老师端 V2 页面方向**：
  - `Dashboard` 是工作台，不是报表首页
  - `Courses` 是主业务流入口
  - `Billing` 是收费与账户工作台，优先看待收费学生和预收充值
  - `Settings` 维护课时单价与提醒规则说明
- **前端拆包**：`src/App.tsx` 已按路由 `lazy` 加载，`vite.config.ts` 已做基础 `manualChunks`
- **性能现状**：构建已从单一超大入口包拆成多 chunk，但 `antd` 共享 chunk 仍偏大

## 学生端架构（student-web/）

### 技术栈
React 18 + TypeScript + Ant Design 5 + Vite + Zustand + Axios + Recharts + Day.js

### 关键约定
- **移动端优先**：max-width 640px 居中，底部 TabBar（5 个 tab：课程/作业/反馈/进度/资料）
- **API 客户端**：`src/api/client.ts`，token 存储在 `localStorage` key `student_access_token`（与管理端隔离）
- **认证状态**：`src/store/authStore.ts`（Zustand，storage name `student-auth-storage`）
- **路由**：`/login` 公开路由；`/courses`, `/assignments`, `/feedback`, `/progress`, `/resources` 带 TabBar；`/assignments/:id`, `/feedback/:id` 独立详情页无 TabBar
- **后端接口**：复用 `/api/xxx/my` 系列学生端接口 + `/api/resources/shared`
- **鉴权下载**：资料下载使用 fetch + blob URL（浏览器 `<a>` 无法带 Bearer token）
- **登录方式**：学生使用用户名/密码登录（需老师在管理端创建学生时设置）

### 学生端新增后端接口
- `GET /api/feedback/my/{id}` — 学生反馈详情
- `GET /api/progress/my/grades/trend?subject=` — 学生成绩趋势
- `GET /api/progress/my/knowledge-points?subject=` — 学生知识点列表
- `GET /api/courses/my` 新增 `start_date`、`end_date` 可选参数

### 后端改动：学生密码登录
- `StudentCreate` / `StudentUpdate` 新增 `username` / `password` 可选字段
- 创建/编辑学生时可设置关联 User 账号（role=student）
- `StudentResponse` 新增 `username` 字段（从关联 User 读取）

## 微信小程序架构（miniprogram/）

### 关键约定
- **请求封装**：`api/request.js`，所有接口调用走此模块，自动从 `wx.getStorageSync('token')` 读 token
- **认证**：`utils/auth.js`，`login()` 调用 `wx.login()` + `/api/auth/wechat` 换 token
- **API 地址**：`app.globalData.apiBaseUrl`，默认 `http://localhost:8000`，部署时改为实际域名
- **数据存储**：token/userInfo/studentId 存 `wx.Storage`

## 测试架构

测试使用 SQLite 内存数据库替代 PostgreSQL，通过 `tests/conftest.py` 的猴子补丁兼容：
- `ARRAY` → `JSONEncodedList`（TypeDecorator，接受任意参数以兼容 `ARRAY(String)` 等用法）
- `JSONB` → `JSONEncodedDict`（TypeDecorator，直接替换类以兼容 `mapped_column(JSONB)` 类型检查）

Fixture 依赖链：`db` → `admin_user` → `async_client` + `auth_headers` + `test_student` → `test_course`

测试隔离：每个测试结束后先执行 `session.rollback()`，然后显式清空所有表数据（SQLite StaticPool 共享同一连接，rollback 不可靠，必须显式删除数据）。

测试模块：test_auth、test_students、test_courses、test_assignments、test_billing、test_resources、test_integration。

## 文档目录

- `docs/00-index.md` — 项目级文档入口和当前活跃基线索引
- `docs/04-implementation/documentation-workflow.md` — 文档归集说明、查找顺序、vibecoding 工作流和交接清单
- `docs/04-implementation/doc-map.md` — 项目自有 Markdown 文档地图和状态表
- `docs/01-product/current.md` — 当前产品基线入口
- `docs/01-product/teacher-v2/status.md` — 当前 V2 项目状态
- `docs/01-product/teacher-v2/prd.md` — 当前老师端 V2 产品需求
- `docs/04-implementation/teacher-v2/plan.md` — 当前老师端 V2 实施拆解
- `docs/02-design/teacher-v2/prototype.md` — 当前老师端 V2 原型说明
- `docs/99-archive/legacy/product/prd-v1.md` — 旧版产品需求（遗留）
- `docs/99-archive/legacy/product/user-stories-v1.md` — 用户故事（含验收标准）
- `docs/99-archive/reference/architecture/api-design-v1.md` — 完整 API 接口规范
- `docs/99-archive/reference/architecture/database-schema-v1.md` — 数据库表结构和 ER 图
- `docs/99-archive/legacy/design/web-wireframes-v1.md` — 旧版 Web 管理端线框图（遗留）
- `docs/99-archive/reference/design/miniprogram-wireframes-v1.md` — 小程序线框图

文档维护规则：
- 重要产品、实现进度或后续任务变化，应更新当前文档，而不是只留在 AI 对话记录中
- `.specstory/` 属于原始 AI 会话历史，只作为参考材料
- 已确认或已完成的重要变更，应新增记录到 `docs/07-changes/`
- 长期文档应标注 `状态`、`范围`、`更新`
- 新增、删除、重命名或改变长期 Markdown 文档定位时，应同步更新 `docs/04-implementation/doc-map.md`
