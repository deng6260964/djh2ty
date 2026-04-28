# 文档归集说明与工作流程

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文定义当前 `docs/` 新结构下，文档如何组织、更新、验证和交接。目标是在 vibecoding、多 agent 协作和多人研发过程中，让模型与研发都能快速找到当前事实、历史背景、测试依据和变更记录。

## 1. 文档原则

### 1.1 只认一个当前基线

当前活跃产品基线是老师端 V2 改造。当旧文档与当前基线冲突时，默认以当前文档为准；只有在明确做历史对照时才阅读历史文档。

当前事实源文档按这个顺序读取：

- `docs/01-product/current.md` — 当前产品基线入口
- `docs/01-product/teacher-v2/status.md` — 当前状态、下一步和优先级
- `docs/01-product/teacher-v2/prd.md` — 当前老师端 PRD
- `docs/02-design/teacher-v2/prototype.md` — 当前老师端原型说明
- `docs/04-implementation/teacher-v2/plan.md` — 实施进度和剩余工作

完整项目自有 Markdown 文档清单见 `docs/04-implementation/doc-map.md`。测试资产见 `docs/05-testing/README.md`。当前进行态见 `docs/08-progress/project-status.md`。重要完成态变更见 `docs/07-changes/README.md`。

归档文档如 `docs/99-archive/legacy/product/prd-v1.md`、`docs/99-archive/legacy/design/web-wireframes-v1.md` 只作为历史对照材料，不作为当前决策依据。

### 1.2 文档必须声明角色

新增或大幅修改长期文档时，应在标题下方加入状态块：

```md
> 状态：当前 | 草案 | 参考 | 历史 | 归档
> 范围：老师端 V2 | 后端 | 管理端 | 学生端 | 微信小程序 | 全项目
> 更新：YYYY-MM-DD
```

状态含义：

- `当前`：当前事实源，可作为产品、设计、实现或流程决策依据
- `草案`：尚未被确认采用
- `参考`：有价值但不保证与当前实现完全一致
- `历史`：已被新文档替代，仅用于历史对照
- `归档`：仅保留记录，不作为决策依据

### 1.3 过程记录不是产品事实

AI 对话、`.specstory/` 历史、截图、临时调查笔记和生成过程材料，都只是原始素材。如果其中包含重要决策、实现状态或后续任务，应提炼到当前文档，而不是依赖原始聊天记录。

## 2. 推荐检索顺序

修改产品行为、设计、架构或实现前，按以下顺序阅读：

1. `docs/00-index.md`
2. `docs/04-implementation/documentation-workflow.md`
3. 需要完整文档清单时阅读 `docs/04-implementation/doc-map.md`
4. `docs/01-product/current.md`
5. `docs/01-product/teacher-v2/status.md`
6. `docs/01-product/teacher-v2/prd.md`
7. `docs/02-design/teacher-v2/prototype.md`
8. `docs/04-implementation/teacher-v2/plan.md`
9. 涉及多人并行、当前负责人或阻塞状态时阅读 `docs/08-progress/project-status.md`
10. 涉及测试时阅读 `docs/05-testing/README.md` 和相关用例 / 验证记录
11. 涉及历史变更时阅读 `docs/07-changes/`
12. 涉及技术或部署时阅读 `docs/03-architecture/`
13. 仅在明确做历史对照时阅读 `docs/99-archive/`

老师端 V2 工作中，`docs/01-product/teacher-v2/status.md` 是最快的项目状态入口。

## 3. 文档归属

当前项目文档已经采用分层目录结构。

| 目录 | 用途 | 说明 |
| --- | --- | --- |
| `docs/00-index.md` | 文档总入口 | 所有模型和研发接手时优先阅读 |
| `docs/01-product/` | 产品需求、状态、业务流程、历史需求 | 当前 V2 产品事实源放在 `teacher-v2/` |
| `docs/02-design/` | 原型、线框、设计规范、交互说明 | 当前 V2 设计事实源放在 `teacher-v2/` |
| `docs/03-architecture/` | API、数据模型、部署、技术栈 | 真实代码变化后再更新，避免写成纯设想 |
| `docs/04-implementation/` | 实施计划、任务拆解、研发交接和文档流程 | 研发推进和交接材料放在这里 |
| `docs/05-testing/` | 测试用例、测试报告、验证记录 | 测试资产统一入口，包含后端 pytest 报告和管理端 browser-use 用例 |
| `docs/06-ai-worklogs/` | AI 工作日志 | 仅存放提炼后的会话结论，不放原始长对话 |
| `docs/07-changes/` | 变更记录 | 记录已确认或已完成的重要变更 |
| `docs/08-progress/` | 进度同步 | 记录当前进行态、负责人、阻塞点和多人并行工作流 |
| `docs/99-archive/` | 已归档材料 | 仅保留记录，不作为当前决策依据 |
| `.specstory/` | 原始 AI 会话历史 | 不作为当前产品事实 |

## 4. Vibecoding 工作流

### 4.1 编码前

非琐碎改动开始前：

1. 按推荐检索顺序阅读当前基线文档。
2. 判断影响面：`backend`、`admin-web`、`student-web`、`miniprogram`、纯文档，或多个端。
3. 确认需求是否符合老师端 V2 方向。
4. 检查是否已有相关 `docs/07-changes/` 记录，避免重复推翻既有决策。
5. 检查是否已有相关 `docs/08-progress/` 工作流，避免多人并行时重复推进或覆盖上下文。
6. 如果产品行为不清楚，先澄清目标行为，再改代码。

### 4.2 编码中

实现过程中的笔记应保持轻量。不要为每个小改动都创建长期文档。

只有出现以下情况时，才在过程中新增或更新文档：

- 产品决策发生变化
- 工作流或验收标准发生变化
- 实施阶段完成或优先级调整
- 引入新的技术约定
- 测试策略、测试用例或验证结果发生变化
- 后续研发如果不看 AI 对话就无法理解上下文

### 4.3 编码后

一次有意义的 vibecoding 结束时，根据改动类型更新文档：

| 改动类型 | 必须更新的文档 |
| --- | --- |
| 产品状态或优先级变化 | 更新 `docs/01-product/teacher-v2/status.md` |
| 老师端实现进度变化 | 更新 `docs/04-implementation/teacher-v2/plan.md` |
| 负责人、阻塞、当前进行态变化 | 更新 `docs/08-progress/project-status.md` 和相关工作流文档 |
| 未完成任务需要中断或换人接手 | 运行 `node scripts/create-checkpoint.mjs` 并补齐 `docs/08-progress/checkpoints/` 中的断点快照 |
| 产品行为或验收标准变化 | 更新当前 PRD 或相关流程文档 |
| UI / 交互行为变化 | 更新 `docs/02-design/` 下相关文档 |
| API、数据结构、部署或技术约定变化 | 更新 `docs/03-architecture/` 下相关文档 |
| 测试用例、测试策略或验证结果变化 | 更新 `docs/05-testing/` 下相关文档 |
| 已确认或已完成的重要变更 | 在 `docs/07-changes/` 下按年月新增变更记录 |
| AI 会话中产生可复用过程结论 | 在 `docs/06-ai-worklogs/` 下新增工作日志 |
| 只有代码变化且文档仍准确 | 不需要更新文档，但在交接说明中说明这一点 |

## 5. 按目录更新规则

### 5.1 产品文档

更新位置：

- `docs/01-product/current.md`
- `docs/01-product/teacher-v2/status.md`
- `docs/01-product/teacher-v2/prd.md`

适用情况：

- 产品目标、优先级、验收标准发生变化
- 当前阶段判断发生变化
- 旧产品假设被废弃或替换

### 5.2 设计文档

更新位置：

- `docs/02-design/teacher-v2/prototype.md`
- `docs/02-design/teacher-v2/flow-prototype.md`
- `docs/02-design/design-system.md`
- `docs/02-design/interaction-guide.md`

适用情况：

- 页面结构、用户路径、核心交互发生变化
- 设计规范或通用交互约定发生变化

### 5.3 架构文档

更新位置：

- `docs/03-architecture/tech-stack.md`
- `docs/03-architecture/deployment.md`

适用情况：

- 技术栈、部署方式、运行环境发生变化
- 跨模块技术约定发生变化

如果后续出现大量跨模块决策，建议新增 `docs/03-architecture/decisions/` 存放 ADR。

### 5.4 实施文档

更新位置：

- `docs/04-implementation/teacher-v2/plan.md`
- `docs/04-implementation/backend/README.md`
- `docs/04-implementation/documentation-workflow.md`
- `docs/04-implementation/doc-map.md`

适用情况：

- 任务阶段、实现计划、开发交接方式发生变化
- 后端启动、开发或调试方式发生变化
- 文档结构发生变化

实施计划只维护方案、阶段和任务拆解，不承载日常负责人同步。多人并行进行态放入 `docs/08-progress/`。

### 5.5 测试文档

更新位置：

- `docs/05-testing/README.md`
- `docs/05-testing/backend/test-report.md`
- `docs/05-testing/browser-use/*.spec.md`
- `docs/05-testing/browser-use/*.verification.md`

适用情况：

- 新增或调整测试用例
- 重新执行 browser-use 或后端测试
- 测试环境、测试数据、未执行项发生变化

### 5.6 AI 工作日志

更新位置：

- `docs/06-ai-worklogs/`

适用情况：

- AI 会话产生了有复用价值的过程结论
- 结论不适合放入 PRD、实现计划、测试记录或变更记录

不要把完整聊天记录粘贴进去，只保留目标、决策、影响范围、验证和后续任务。

### 5.7 变更记录

更新位置：

- `docs/07-changes/YYYY-MM/YYYY-MM-DD-topic.md`

适用情况：

- 已确认或已完成的重要变更
- 需要解释“为什么变、变了什么、影响哪里、如何验证”

### 5.8 进度同步文档

更新位置：

- `docs/08-progress/README.md`
- `docs/08-progress/project-status.md`
- `docs/08-progress/workstreams/*.md`
- `docs/08-progress/checkpoints/YYYY-MM/*.md`

适用情况：

- 多人或多个 agent 并行推进需求、重构、测试或文档治理
- 负责人、工作流状态、阻塞点、下一步发生变化
- 一个任务暂时不适合写入完成态变更记录，但需要让接手者知道当前进展
- 一次对话或一次工作未完成，但用户需要暂停、切换上下文或换人接手

边界：

- `docs/04-implementation/` 管理“怎么实现”
- `docs/08-progress/` 管理“当前做到哪里”
- `docs/07-changes/` 管理“已经完成或确认了什么”

同一事项从计划进入进行态时，应进入进度文档；从进行态变成完成事实时，应沉淀到变更记录和对应事实源。

checkpoint 断点快照由脚本和模型共同完成：

1. 脚本自动采集客观现场：分支、提交、变更文件、diff 统计、最近提交和建议验证命令。
2. 模型根据当前对话补齐主观上下文：本次目标、已完成、未完成、风险、阻塞和下一步。
3. 后续恢复时，先读 `docs/08-progress/project-status.md`，再读对应 `docs/08-progress/workstreams/*.md`，最后读最新 open checkpoint。
4. checkpoint 被恢复后，将 `处理状态` 从 `open` 改为 `resumed`；工作流完成后改为 `closed`。

推荐命令：

```bash
node scripts/create-checkpoint.mjs --workstream student-web-v2-rework --owner codex
node scripts/check-progress.mjs
```

### 5.9 归档文档

更新位置：

- `docs/99-archive/`

适用情况：

- 文档已经不再适合作为当前事实源
- 文档仍有历史对照价值
- 旧 API、旧数据结构、旧 PRD、旧线框需要避免误导后续模型

归档文档状态必须为 `归档`。

## 6. 变更记录

当一次开发、重构或文档整理产生了可追溯的结果，应新增变更记录。变更记录面向团队协作，重点说明事实结果，不记录完整过程。

推荐位置：

推荐按 docs/07-changes/年月/日期-主题.md 存放。

模板：

```text
docs/07-changes/template/change-record-template.md
```

变更记录应包含：

- 背景
- 变更内容
- 影响范围
- 兼容性与风险
- 验证方式
- 关联文档
- 后续事项

## 7. AI 工作日志

只有当一次会话产生了有复用价值、但不适合放入 PRD、实施计划或架构文档的决策时，才创建 AI 工作日志。

推荐位置：

推荐按 docs/06-ai-worklogs/日期-主题.md 存放。

推荐模板：

```md
# YYYY-MM-DD 主题

## 目标

本次会话要解决什么问题。

## 决策

- 决策：原因

## 影响范围

- `backend/...`
- `admin-web/...`

## 验证

- 执行的命令和结果

## 后续任务

- 明确的下一步
```

不要把完整聊天记录粘贴进工作日志。只总结决策、影响范围、验证结果和后续任务。

## 8. 命名规则

长期文档使用清晰的 kebab-case 文件名，例如 teacher-v2-billing-recharge、student-web-v2-navigation、course-copy-week-flow。

避免模糊命名：

- notes
- new-plan
- final
- todo2

只有日志或快照类文档使用日期前缀：

- 2026-04-26-doc-architecture
- 2026-04-26-teacher-v2-handoff

## 9. 交接清单

完成较大任务前，回答这些问题：

- 当前状态或下一步是否发生变化？
- 某个实施阶段是否推进了？
- 产品行为是否与当前 PRD 或原型相比发生变化？
- API、数据结构、部署或测试约定是否发生变化？
- 测试用例或验证记录是否需要更新？
- 是否需要新增一条 `docs/07-changes/` 变更记录？
- 是否需要更新 `docs/08-progress/` 中的负责人、阻塞或下一步？
- 当前任务如果未完成，是否需要生成 checkpoint 断点快照？
- 是否有 AI 会话结论需要沉淀到 `docs/06-ai-worklogs/`？
- 后续研发是否能不看原始 AI 对话也理解当前状态？

只要任一答案为“是”，就应在交接前更新相关当前文档。

新增、删除、重命名长期 Markdown 文档，或改变文档角色时，应在同一次改动中更新 `docs/04-implementation/doc-map.md`。

## 10. 当前目录结构

```text
docs/
  00-index.md
  01-product/
  02-design/
  03-architecture/
  04-implementation/
  05-testing/
  06-ai-worklogs/
  07-changes/
  08-progress/
  99-archive/
```

不要在功能开发过程中顺手做大规模目录迁移。目录迁移应作为独立文档整理任务处理，并同步更新 `docs/04-implementation/doc-map.md`。
