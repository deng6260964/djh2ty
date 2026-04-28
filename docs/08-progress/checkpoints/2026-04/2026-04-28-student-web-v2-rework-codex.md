# 2026-04-28 student-web-v2-rework 断点快照

> 状态：当前
> 范围：学生端、后端、文档
> 更新：2026-04-28
> 工作流：student-web-v2-rework
> 负责人：Codex
> 处理状态：closed

## 中断原因

本 checkpoint 已关闭。2026-04-28 校正并恢复使用本地已有 `postgres:16-alpine` 数据库环境后，已完成真实浏览器冒烟。

## 本次目标

完成整个项目开发和验收收敛：确认老师端 V2 已收口，补齐学生端新版基础承接，新增必要后端接口和测试，运行自动化验证，并同步事实源、进度、变更和测试文档。完成标准是后端全量测试、管理端构建、学生端构建通过；真实浏览器冒烟若受环境阻塞，需记录阻塞和恢复步骤。

## 已完成

- 阅读最小启动上下文、老师端 V2 状态、PRD、原型、实现计划、项目进度和两个 workstream。
- 确认老师端 V2 主链路已基本收口，剩余主要是学生端新版承接和发布前回归。
- 新增 `GET /api/billing/my/account`，复用老师端账户聚合逻辑，供学生/家长端只读查看余额、下一节课风险、最近收款和最近扣费。
- 新增后端测试 `test_my_account_returns_current_student_balance`，覆盖当前学生账户只读接口。
- 学生端新增首页：聚合账户余额/余额风险、最近课程、待完成作业、最新反馈。
- 学生端新增账户明细页：展示当前余额、最近扣费和最近收款。
- 学生端默认入口调整为首页，保留课程、作业、反馈、进度、资料底部 Tab。
- 学生端完成路由懒加载和 Vite 拆包，移除单个约 1.2 MB 入口包和 500 kB chunk 警告。
- 同步 `docs/01-product/teacher-v2/status.md`、`docs/04-implementation/teacher-v2/plan.md`、`docs/08-progress/project-status.md`、相关 workstream、后端测试报告、文档地图和变更记录。
- 已执行验证：
  - `cd backend && pytest tests/test_billing.py -q`：17 passed
  - `cd backend && pytest tests/test_billing.py tests/test_courses.py tests/test_teacher_workbench.py -q`：44 passed
  - `cd backend && pytest -q`：121 passed
  - `cd student-web && npm run build`：通过
  - `cd admin-web && npm run build`：通过

## 未完成

- 已补充真实浏览器/移动视口冒烟：学生端登录、首页、账户明细、课程、作业、反馈、进度、资料均通过。
- 已补充管理端 P0 页面级浏览器复核：工作台、学生、课程、收费与账户、作业、反馈、学习复盘、资料、设置均通过。
- 待数据库环境恢复后，需要复核学生端登录、首页、账户明细、课程、作业、反馈、进度、资料。
- 待数据库环境恢复后，建议复核管理端 P0 主链路是否仍与 2026-04-28 browser-use 回归记录一致。

## 当前现场

### 自动采集

- 分支：main
- 当前提交：d498d1a
- 工作流：student-web-v2-rework
- 负责人：Codex
- 相关范围：学生端、后端、文档

### 变更文件

- backend/app/routers/billing.py
- backend/tests/test_billing.py
- docs/01-product/teacher-v2/status.md
- docs/04-implementation/doc-map.md
- docs/04-implementation/teacher-v2/plan.md
- docs/05-testing/backend/test-report.md
- docs/08-progress/project-status.md
- docs/08-progress/workstreams/admin-web-regression-refresh.md
- docs/08-progress/workstreams/student-web-v2-rework.md
- student-web/src/App.tsx
- student-web/src/components/TabBar.tsx
- student-web/src/styles/tabbar.css
- student-web/src/utils/format.ts
- student-web/vite.config.ts
- docs/07-changes/2026-04/2026-04-28-student-web-code-splitting.md
- docs/07-changes/2026-04/2026-04-28-student-web-v2-acceptance.md
- student-web/src/api/billing.ts
- student-web/src/pages/Account/
- student-web/src/pages/Home/

### 最近修改文档

- docs/01-product/teacher-v2/status.md
- docs/04-implementation/doc-map.md
- docs/04-implementation/teacher-v2/plan.md
- docs/05-testing/backend/test-report.md
- docs/08-progress/project-status.md
- docs/08-progress/workstreams/admin-web-regression-refresh.md
- docs/08-progress/workstreams/student-web-v2-rework.md
- docs/07-changes/2026-04/2026-04-28-student-web-code-splitting.md
- docs/07-changes/2026-04/2026-04-28-student-web-v2-acceptance.md

### Diff 统计

```text
 backend/app/routers/billing.py                     | 192 +++++++++++----------
 backend/tests/test_billing.py                      |  77 +++++++++
 docs/01-product/teacher-v2/status.md               |  21 ++-
 docs/04-implementation/doc-map.md                  |   2 +
 docs/04-implementation/teacher-v2/plan.md          |  10 +-
 docs/05-testing/backend/test-report.md             |   7 +-
 docs/08-progress/project-status.md                 |  10 +-
 .../workstreams/admin-web-regression-refresh.md    |  11 +-
 .../workstreams/student-web-v2-rework.md           |  23 ++-
 student-web/src/App.tsx                            |  38 ++--
 student-web/src/components/TabBar.tsx              |   4 +-
 student-web/src/styles/tabbar.css                  |   2 +-
 student-web/src/utils/format.ts                    |   5 +
 student-web/vite.config.ts                         |  18 ++
 14 files changed, 285 insertions(+), 135 deletions(-)
```

### 暂存区 Diff 统计

```text
无已暂存 diff
```

### 最近提交

- d498d1a docs: 新增断点快照流程及相关脚本
- e155846 docs: add agent orchestration workflow adapter
- 3f8be66 docs: add ai workflow skill adapter
- fa7beba docs: 新增进度同步目录和测试流程指南
- ca37c83 teacher-v2: complete course workflow and docs

## 风险与阻塞

- 已关闭：真实浏览器冒烟已执行，发现并修复学生端登录成功后跳旧课程页的问题。
- 不要重复探索：本项目直接用普通 SQLite 启动后端会遇到 PostgreSQL `ARRAY` 等方言兼容问题；pytest 是通过 `conftest.py` monkey patch 解决的，不代表生产/开发服务可直接 SQLite 启动。
- 代码风险：学生端账户接口是新增只读接口，已有 pytest 覆盖主路径；浏览器层空状态和真实登录态仍需验收。
- 构建提示：`admin-web` 和 `student-web` 构建仍有既有 Vite CJS Node API deprecation warning，不阻塞本轮。

## 下一步

1. 恢复时先读 `docs/08-progress/project-status.md`、`docs/08-progress/workstreams/student-web-v2-rework.md`、`docs/07-changes/2026-04/2026-04-28-student-web-v2-acceptance.md`。
2. 后续新需求另开 workstream；不要继续沿用本 checkpoint 作为进行态。

## 建议验证命令

- cd backend && pytest -q
- cd admin-web && npm run build
- cd student-web && npm run build

## 关联文档

- `docs/08-progress/workstreams/student-web-v2-rework.md`
- `docs/08-progress/project-status.md`
