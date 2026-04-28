# 仓库工作指南

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

## 当前基线

当前活跃产品基线是老师端 V2 改造。处理新需求前，优先阅读以下文档，并将它们作为旧文档之前的主要事实源：

- `docs/01-product/teacher-v2/status.md` — 当前项目状态和下一步
- `docs/01-product/current.md` — 当前产品基线入口
- `docs/01-product/teacher-v2/prd.md` — 当前老师端 PRD
- `docs/02-design/teacher-v2/prototype.md` — 当前老师端原型说明
- `docs/04-implementation/teacher-v2/plan.md` — 实施进度和剩余工作
- `docs/08-progress/project-status.md` — 当前进行态和多人并行工作流

旧文档如 `docs/99-archive/legacy/product/prd-v1.md`、`docs/99-archive/legacy/design/web-wireframes-v1.md` 仅用于历史对照。

## AI 编码工作流适配

本项目执行本地通用技能：

- `ai-coding-workflow`：用于开发、修复、重构、性能定位、测试刷新和代码改动。
- `document-governance-workflow`：用于创建、更新、归档、整理文档，维护变更记录、进度记录、checkpoint 和文档地图。

开发、修复、重构、测试刷新和文档治理时，先按对应 skill 进行任务分级、最小上下文读取、Phase/Gate 控制、验证和交接；再结合本文件中的当前基线、项目结构、测试命令和文档卫生规则执行。

本项目适配说明见：`docs/04-implementation/development-usage-guide.md`。

本项目的最小启动上下文为：

- `docs/00-index.md`
- `docs/01-product/current.md`
- `docs/01-product/teacher-v2/status.md`
- `docs/08-progress/project-status.md`

本项目的高风险业务包括：课程状态流转、自动扣费、充值、余额回滚、批量复制课程、鉴权、删除和跨端学生信息展示。涉及这些内容时，至少按通用工作流中的 L 级任务处理。

## 项目结构与模块组织

本仓库按客户端和服务端拆分：

- `backend/`：FastAPI 后端服务，领域代码在 `app/`，迁移在 `alembic/`，pytest 测试在 `tests/`，上传文件在 `uploads/`
- `admin-web/`：React + Vite + TypeScript 管理端，页面代码放在 `src/pages/`，共享 UI 放在 `src/components/`，API 封装放在 `src/api/`，状态管理放在 `src/store/`
- `student-web/`：React + Vite + TypeScript 学生端，目录约定同管理端
- `miniprogram/`：微信小程序，页面在 `pages/`，请求封装在 `api/`，工具函数在 `utils/`

老师端 V2 已经在 `backend/` 和 `admin-web/` 落地，关键位置包括：

- 工作台：`backend/app/routers/dashboard.py`、`admin-web/src/pages/Dashboard/`
- 课程周视图与复制上一周：`backend/app/routers/courses.py`、`admin-web/src/pages/Courses/`
- 学生账户与预收充值：`backend/app/routers/billing.py`、`admin-web/src/pages/Billing/`、`admin-web/src/pages/Students/`
- 设置页：`admin-web/src/pages/Settings/`

## 构建、测试与开发命令

后端：

- `docker-compose up -d`：启动本地 PostgreSQL
- `cd backend && pip install -r requirements.txt`：安装 FastAPI 和 pytest 依赖
- `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`：启动 API，文档地址为 `http://localhost:8000/api/docs`
- `cd backend && pytest`：运行完整后端测试

前端：

- `cd admin-web && npm install && npm run dev`
- `cd admin-web && npm run build`
- `cd student-web && npm install && npm run dev`
- `cd student-web && npm run build`

当前老师端工作常用验证命令：

- `cd backend && pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q`
- `cd admin-web && npm run build`

## 代码风格与命名约定

遵循各子项目已有风格：

- Python 使用 4 空格缩进、类型提示、snake_case 模块名，例如 `routers/students.py`
- React/TypeScript 使用 2 空格缩进、PascalCase 组件文件名，例如 `CourseCard.tsx`
- hooks/store 使用 camelCase，例如 `authStore.ts`
- 页面入口文件沿用 `index.tsx`
- API、类型和格式化工具分别放在 `src/api`、`src/types`、`src/utils`

仓库没有统一 formatter 配置，扩展代码前先匹配周边代码风格。

修改老师端 V2 流程时，应沿着当前方向演进，不要回退到旧的模块并列后台结构：

- 将 dashboard 视为老师工作台
- 将 courses 视为主要工作流入口
- 将 billing 视为预收余额管理，而不是传统账单后台
- 将 students 视为次级总览和复盘入口

## 测试指南

后端测试使用 `pytest` 和 `pytest-asyncio`。新增测试放在 `backend/tests/` 下，文件命名为 `test_*.py`，函数命名为 `test_*`，类命名为 `Test*`，遵循 `backend/pytest.ini`。

新增路由、schema 变化和鉴权流程时，优先补 API 级测试。Web 应用当前没有测试运行器，提交前至少验证 `npm run build`。

如果改动老师端 V2 后端，应围绕这些接口更新或新增测试：

- `/api/dashboard/workbench`
- `/api/courses/week`
- `/api/courses/copy-week-preview`
- `/api/courses/copy-week-confirm`
- `/api/billing/students/{id}/account`
- `/api/billing/recharge`

## 提交与 PR 指南

当前 workspace 没有可用 Git 元数据，无法检查历史提交风格。提交信息使用简短祈使句，例如 `backend: add resource share validation` 或 `student-web: fix login redirect`。

PR 描述应包含：

- 改动范围
- 影响端：`backend`、`admin-web`、`student-web`、`miniprogram`
- UI 改动截图
- schema 或环境变量变化
- 已执行的验证命令

## 安全与配置

敏感信息放在本地 `.env` 文件，不要提交凭据或生成的上传文件。`backend/uploads/` 和前端构建产物如 `student-web/dist/` 视为生成物，除非任务明确要求，否则不要提交。

## 文档卫生

文档入口是 `docs/00-index.md`。文档归集规则、检索顺序和 vibecoding 交接规则见 `docs/04-implementation/documentation-workflow.md`。

更新计划或规格时，应同步维护当前 V2 文档中的真实实现进度：

- `docs/01-product/teacher-v2/status.md`
- `docs/04-implementation/teacher-v2/plan.md`

多人并行需求、重构、测试刷新或文档治理进入进行态时，应同步维护：

- `docs/08-progress/project-status.md`
- `docs/08-progress/workstreams/`

任务未完成但需要暂停、换人接手或下次继续时，应生成 checkpoint 断点快照：

- 运行 `node scripts/create-checkpoint.mjs --workstream <workstream> --owner <agent-or-user>`
- 由模型补齐本次目标、已完成、未完成、风险与下一步
- 运行 `node scripts/check-progress.mjs`

旧文档优先标记为历史文档，不要轻易删除，除非它们明显是无用文件或已被生成物替代。

`.specstory/` 等原始 AI 会话历史仅作为参考材料。重要决策、进度变化和后续任务应总结到当前项目文档，或归档到 `docs/06-ai-worklogs/`。

已确认或已完成的重要产品、设计、架构、接口、数据或实现变更，应新增记录到 `docs/07-changes/`。

新增、删除、重命名长期 Markdown 文档，或改变文档角色时，应同步更新 `docs/04-implementation/doc-map.md`。
