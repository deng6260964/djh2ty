# 文档地图

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文列出项目自有 Markdown 文档，并说明每份文档的状态、范围和用途。第三方依赖目录 `node_modules/`、构建产物、缓存目录中的文档不纳入本地图。

## 阅读优先级

一般产品或实现工作，先阅读：

1. `docs/00-index.md`
2. `docs/04-implementation/documentation-workflow.md`
3. `docs/01-product/current.md`
4. `docs/01-product/teacher-v2/status.md`
5. `docs/01-product/teacher-v2/prd.md`
6. `docs/02-design/teacher-v2/prototype.md`
7. `docs/04-implementation/teacher-v2/plan.md`
8. `docs/08-progress/project-status.md`

然后根据任务类型继续阅读相关架构、设计、后端或测试文档。

## 核心入口文档

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/00-index.md` | 当前 | 全项目 | 项目文档总入口 |
| `docs/04-implementation/documentation-workflow.md` | 当前 | 全项目 | 文档归集、检索顺序和 vibecoding 交接流程 |
| `docs/04-implementation/doc-map.md` | 当前 | 全项目 | 项目自有 Markdown 文档完整地图 |
| `docs/07-changes/README.md` | 当前 | 全项目 | 变更记录目录说明 |
| `docs/08-progress/README.md` | 当前 | 全项目 | 进度同步目录说明 |
| `docs/08-progress/project-status.md` | 当前 | 全项目 | 当前进行态、并行工作流和下一步总览 |
| `docs/08-progress/checkpoint-usage.md` | 当前 | 全项目 | checkpoint 断点保存、恢复和关闭使用说明 |
| `README.md` | 当前 | 全项目 | 仓库说明和文档入口提示 |
| `AGENTS.md` | 当前 | 全项目 | Agent 使用的仓库工作规则 |
| `CLAUDE.md` | 当前 | 全项目 | Claude Code 使用的仓库工作规则 |

## 当前 V2 活跃基线

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/01-product/current.md` | 当前 | 全项目 | 当前产品基线入口 |
| `docs/01-product/teacher-v2/status.md` | 当前 | 老师端 V2 | 当前状态、下一步和优先级入口 |
| `docs/01-product/teacher-v2/prd.md` | 当前 | 老师端 V2 | 当前老师端产品基线 |
| `docs/02-design/teacher-v2/prototype.md` | 当前 | 老师端 V2 | 当前老师端原型基线 |
| `docs/04-implementation/teacher-v2/plan.md` | 当前 | 老师端 V2 | 实施计划、进度和剩余工作 |

## 设计文档

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/02-design/teacher-v2/flow-prototype.md` | 参考 | 老师端 V2 | V2 流程型原型补充文档 |
| `docs/02-design/teacher-v2/hifi-prototype/` | 参考 | 老师端 V2 | V2 高保真原型静态资产 |
| `docs/02-design/design-system.md` | 参考 | 全项目 | 通用设计规范参考 |
| `docs/02-design/interaction-guide.md` | 参考 | 全项目 | 通用交互规范参考 |

## 架构文档

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/03-architecture/tech-stack.md` | 参考 | 全项目 | 技术栈和总体架构参考 |
| `docs/03-architecture/deployment.md` | 参考 | 部署 | 部署架构参考 |

## 开发与验证文档

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/04-implementation/backend/README.md` | 参考 | 后端 | 后端启动和开发参考 |
| `docs/04-implementation/development-usage-guide.md` | 当前 | 全项目 | 本项目对 `ai-coding-workflow` 和 `document-governance-workflow` 两个通用 skill 的适配说明 |
| `docs/04-implementation/documentation-retrospective-2026-04-27.md` | 当前 | 全项目 | 当前文档结构复盘 |
| `docs/05-testing/README.md` | 当前 | 全项目 | 测试文档统一入口 |
| `docs/05-testing/testing-workflow.md` | 当前 | 全项目 | 测试流程指南，覆盖用例编写、执行动作、失败处理和文档归集 |
| `docs/05-testing/backend/test-report.md` | 参考 | 后端 | 后端测试覆盖快照 |
| `docs/05-testing/browser-use/README.md` | 当前 | 管理端 | browser-use 集成测试目录入口 |
| `docs/05-testing/browser-use/dashboard-workbench.spec.md` | 当前 | 管理端 | 老师工作台专项集成测试用例 |
| `docs/05-testing/browser-use/full-regression.spec.md` | 当前 | 管理端 | 老师端 V2 全量回归测试用例 |
| `docs/05-testing/browser-use/dashboard-workbench.verification.md` | 参考 | 管理端 | 工作台验证记录快照 |
| `docs/05-testing/browser-use/full-regression.verification.md` | 参考 | 管理端 | 全量回归验证记录快照 |

## 进度同步

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/08-progress/workstreams/README.md` | 当前 | 全项目 | 并行工作流进度索引 |
| `docs/08-progress/workstreams/student-web-v2-rework.md` | 当前 | 学生端 | 学生端新版承接进行态记录 |
| `docs/08-progress/workstreams/admin-web-regression-refresh.md` | 当前 | 管理端 | 管理端 browser-use 回归刷新进行态记录 |
| `docs/08-progress/checkpoints/README.md` | 当前 | 全项目 | 断点快照目录说明 |

## 变更记录

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/07-changes/template/change-record-template.md` | 参考 | 全项目 | 变更记录模板 |
| `docs/07-changes/2026-04/2026-04-27-doc-structure-cleanup.md` | 当前 | 全项目 | 文档结构清理与归档变更记录 |
| `docs/07-changes/2026-04/2026-04-27-testing-docs-folder.md` | 当前 | 文档、测试 | 测试文档目录归集变更记录 |
| `docs/07-changes/2026-04/2026-04-27-teacher-v2-auto-charge.md` | 当前 | 老师端 V2 | 完成课程自动扣费与取消回滚变更记录 |
| `docs/07-changes/2026-04/2026-04-27-teacher-v2-main-closure.md` | 当前 | 老师端 V2 | 课程详情、待补课池、学生详情复盘和拆包收口记录 |
| `docs/07-changes/2026-04/2026-04-27-doc-structure-retrospective.md` | 当前 | 全项目 | 文档结构复盘整理记录 |
| `docs/07-changes/2026-04/2026-04-28-testing-workflow.md` | 当前 | 测试、文档 | 测试流程文档和测试目录归集记录 |
| `docs/07-changes/2026-04/2026-04-28-progress-docs-folder.md` | 当前 | 文档、全项目 | 新增进度同步目录和并行工作流记录 |
| `docs/07-changes/2026-04/2026-04-28-progress-checkpoint-workflow.md` | 当前 | 文档、全项目 | 新增断点快照流程和自动采集脚本记录 |
| `docs/07-changes/2026-04/2026-04-28-development-usage-guide.md` | 当前 | 全项目 | AI 编码与文档治理 skill 沉淀及项目适配层引用记录 |

## 原始 AI 历史

| 位置 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `.specstory/` | 原始参考 | 全项目 | 原始 AI 会话历史；重要决策需提炼到当前文档或 `docs/06-ai-worklogs/` |

## 归档材料

| 文档 | 状态 | 范围 | 用途 |
| --- | --- | --- | --- |
| `docs/99-archive/legacy/product/prd-v1.md` | 归档 | 全项目 | 旧版 PRD，仅用于历史对照 |
| `docs/99-archive/legacy/product/flows-v1.md` | 归档 | 全项目 | 旧版核心业务流程，仅用于历史对照 |
| `docs/99-archive/legacy/product/user-stories-v1.md` | 归档 | 全项目 | 旧版模块化用户故事，仅用于历史对照 |
| `docs/99-archive/legacy/design/web-wireframes-v1.md` | 归档 | 管理端 | 旧版管理端线框，仅用于历史对照 |
| `docs/99-archive/reference/product/data-dict-v1.md` | 归档 | 全项目 | 旧版数据字典，真实模型以代码为准 |
| `docs/99-archive/reference/architecture/api-design-v1.md` | 归档 | 后端 | 旧版 API 设计参考，真实接口以路由和测试为准 |
| `docs/99-archive/reference/architecture/database-schema-v1.md` | 归档 | 后端 | 旧版数据库设计参考，真实模型以代码为准 |
| `docs/99-archive/reference/design/miniprogram-wireframes-v1.md` | 归档 | 微信小程序 | 小程序旧线框，后续学生/家长端改造需重新校准 |

## 维护规则

新增长期 Markdown 文档时，应同步更新本文档，并在新文档标题下方加入标准状态块：

```md
> 状态：当前 | 草案 | 参考 | 历史 | 归档
> 范围：老师端 V2 | 后端 | 管理端 | 学生端 | 微信小程序 | 全项目
> 更新：YYYY-MM-DD
```
