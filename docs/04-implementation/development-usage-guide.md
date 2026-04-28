# AI 编码与文档治理适配说明

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文是本项目对通用 AI 编码、文档治理和多 agent 调度流程的适配层。通用流程已沉淀为本地 skills，不在项目文档中重复维护：

- `ai-coding-workflow`：开发、修复、重构、性能定位、测试刷新和代码改动。
- `document-governance-workflow`：文档创建、更新、归档、变更记录、进度记录、checkpoint 和文档地图维护。
- `agent-orchestration-workflow`：多 agent 调度、子 agent 任务书、ownership、结果审计和上下文隔离。

三个 skill 的源文件维护在外部工具包：`/Users/dengjinhui/workspace/self/docs-governance-toolkit/skills/`；本机 `~/.agents/skills/` 下的是安装副本。

`AGENTS.md` 和 `CLAUDE.md` 已引用这三个 skill。模型执行任务时应先按 skill 判断流程，再按本文和仓库入口文档读取本项目上下文。

任务涉及多个独立工作流、跨模块并行、上下文压力较大，或需要创建子 agent 时，使用 `agent-orchestration-workflow`。主 agent 必须保留任务分级、Gate、ownership 分配、结果审计和最终交接职责。

## 1. 最小启动上下文

非琐碎开发、修复、测试刷新或文档治理前，先读取：

1. `docs/00-index.md`
2. `docs/01-product/current.md`
3. `docs/01-product/teacher-v2/status.md`
4. `docs/08-progress/project-status.md`

再根据任务类型按需读取 PRD、原型、实施计划、测试文档、代码入口或变更记录。

## 2. 当前事实源

| 类型 | 文档 |
| --- | --- |
| 文档入口 | `docs/00-index.md` |
| 文档流程 | `docs/04-implementation/documentation-workflow.md` |
| 文档地图 | `docs/04-implementation/doc-map.md` |
| 当前产品基线 | `docs/01-product/current.md` |
| 老师端 V2 状态 | `docs/01-product/teacher-v2/status.md` |
| 老师端 V2 PRD | `docs/01-product/teacher-v2/prd.md` |
| 老师端 V2 原型 | `docs/02-design/teacher-v2/prototype.md` |
| 实施计划 | `docs/04-implementation/teacher-v2/plan.md` |
| 测试入口 | `docs/05-testing/README.md` |
| 进度总览 | `docs/08-progress/project-status.md` |
| 完成态变更 | `docs/07-changes/` |

旧文档只用于历史对照，默认不作为当前事实源。

## 3. 模块边界

- `backend/`：FastAPI 后端，路由在 `app/routers/`，测试在 `tests/`。
- `admin-web/`：React + Vite 管理端，老师端 V2 主链路所在。
- `student-web/`：React + Vite 学生端，后续新版承接重点。
- `miniprogram/`：微信小程序。

## 4. 常用验证

后端：

```bash
cd backend && pytest
cd backend && pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q
```

管理端：

```bash
cd admin-web && npm run build
```

学生端：

```bash
cd student-web && npm run build
```

checkpoint：

```bash
node scripts/create-checkpoint.mjs --workstream <workstream> --owner <agent-or-user>
node scripts/check-progress.mjs
```

## 5. 高风险业务

涉及以下内容时，至少按 `ai-coding-workflow` 的 L 级任务处理：

- 课程状态流转。
- 完成课程自动扣费。
- 预收充值。
- 取消或删除已完成课程后的余额回滚。
- 批量复制课程。
- 鉴权和学生端登录态。
- 删除业务数据。
- 跨端学生信息展示。

## 6. 文档沉淀位置

| 信息 | 位置 |
| --- | --- |
| 当前产品事实 | `docs/01-product/` |
| 设计事实 | `docs/02-design/` |
| 实施计划 | `docs/04-implementation/` |
| 测试用例和验证记录 | `docs/05-testing/` |
| AI 工作日志 | `docs/06-ai-worklogs/` |
| 完成态变更 | `docs/07-changes/` |
| 当前进行态 | `docs/08-progress/` |
| 未完成断点 | `docs/08-progress/checkpoints/` |
| 历史材料 | `docs/99-archive/` |

新增、删除、重命名长期 Markdown 文档，或改变文档角色时，同步更新 `docs/04-implementation/doc-map.md`。
