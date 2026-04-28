# 2026-04-27 文档结构复盘

> 状态：当前
> 范围：全项目
> 更新：2026-04-27

本文基于当前 `docs/` 目录结构，复盘文档治理是否能支撑后续 vibecoding、多人并行需求实现和代码重构。

## 1. 当前结论

当前文档结构已经基本满足“单项目长期演进 + AI 协作 + 多人接手”的需要。

现有结构解决了三个核心问题：

- 当前事实源明确：从 `docs/00-index.md` 和 `docs/01-product/current.md` 进入。
- 过时材料隔离：旧 PRD、旧流程、旧 API、旧数据字典等已归入 `docs/99-archive/`。
- 变更可追溯：重要变更进入 `docs/07-changes/`，不再只散落在 AI 对话或实现计划中。

但如果进入更高强度的多人并行开发，还需要补充 `workstreams` 和 `decisions` 两类文档入口。

## 2. 当前目录职责

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
  99-archive/
```

| 目录 | 当前职责 | 评价 |
| --- | --- | --- |
| `docs/00-index.md` | 项目文档总入口 | 清晰，适合作为 AI 和研发的第一入口 |
| `docs/01-product/` | 当前产品基线、V2 PRD、项目状态 | 清晰，当前事实源集中 |
| `docs/02-design/` | 当前 V2 原型、流程原型、设计规范、交互规范 | 清晰，历史线框已隔离 |
| `docs/03-architecture/` | 技术栈、部署说明 | 偏轻，后续需要补架构决策目录 |
| `docs/04-implementation/` | 实施计划、文档流程、文档地图、后端开发参考 | 清晰，但还缺并行任务流入口 |
| `docs/05-testing/` | 测试报告、browser-use 用例和验证记录 | 清晰，已从实现目录拆出 |
| `docs/06-ai-worklogs/` | AI 会话提炼结论 | 目录已预留，当前暂无内容 |
| `docs/07-changes/` | 已确认或已完成的重要变更记录 | 清晰，适合追溯 |
| `docs/99-archive/` | 过时文档与旧参考材料 | 清晰，能避免旧文档误导 |

## 3. 对多人并行的支撑程度

### 已经能支撑的部分

当前结构已经能支撑这些协作动作：

- 新人或 AI agent 快速读取当前项目状态。
- 需求实现后同步更新产品状态和实施计划。
- 重要行为变化通过 `docs/07-changes/` 追溯。
- 测试资产独立管理，不再混在实现文档里。
- 旧文档不会直接出现在主阅读路径中。

### 仍然不足的部分

多人并行时，仍可能出现这些问题：

- 多个人同时修改 `docs/04-implementation/teacher-v2/plan.md`，产生冲突。
- 一个需求涉及多个模块时，缺少独立的任务流文档承载影响范围和冲突风险。
- 跨模块技术决策目前没有独立 ADR 入口。
- `docs/04-implementation/teacher-v2/plan.md` 同时包含历史计划和当前状态，后续可能越来越长。

## 4. 建议补充的两个目录

### 4.1 并行任务流目录

建议新增：

```text
docs/04-implementation/workstreams/
  README.md
  teacher-v2-course-detail-loop.md
  student-web-v2-rework.md
```

用途：

- 记录某个并行需求或重构任务的目标。
- 标记负责人、影响文件、冲突风险。
- 记录当前进度和交接事项。
- 完成后再更新主计划和变更记录。

适合场景：

- 多人同时做不同需求。
- 多个 AI agent 分别处理不同模块。
- 一个任务横跨后端、管理端、学生端。

### 4.2 架构决策目录

建议新增：

```text
docs/03-architecture/decisions/
  README.md
  ADR-0001-course-auto-charge.md
  ADR-0002-makeup-course-state.md
```

用途：

- 记录长期有效的跨模块技术或业务规则决策。
- 避免关键规则只存在于实现代码或变更记录中。
- 为后续重构提供约束。

适合场景：

- 自动扣费与回滚规则。
- 请假 / 待补课状态流转。
- 学生端与老师端接口边界。
- 大规模前端拆包策略。

## 5. 推荐协作流程

### 5.1 开始一个并行需求

1. 阅读 `docs/00-index.md`。
2. 阅读当前产品基线和实施计划。
3. 创建或更新一个 workstream 文档。
4. 标记影响范围、风险和可能冲突的其他任务。

### 5.2 开发过程中

1. 不频繁修改主 PRD。
2. 将临时推进状态写在 workstream 中。
3. 发现跨模块规则变化时，新建 ADR。
4. AI 会话结论如有复用价值，写入 `docs/06-ai-worklogs/`。

### 5.3 完成后

1. 更新 `docs/01-product/teacher-v2/status.md`。
2. 更新 `docs/04-implementation/teacher-v2/plan.md`。
3. 更新测试或验证记录。
4. 新增 `docs/07-changes/` 变更记录。
5. 如果新增、移动、归档文档，同步更新 `docs/04-implementation/doc-map.md`。

## 6. 当前最小改进建议

建议下一步只做小增量，不做大迁移：

1. 新增 docs/04-implementation/workstreams/README.md 和任务模板。
2. 新增 docs/03-architecture/decisions/README.md 和 ADR 模板。
3. 将 `docs/04-implementation/teacher-v2/plan.md` 的顶部“当前状态”继续保持短小，历史计划内容后续可逐步拆分或归档。
4. 保持 `docs/07-changes/` 作为所有重要完成态变更的追溯入口。

## 7. 总体评价

当前文档结构已经从“过程文档混杂”升级为“可检索、可归档、可追溯”的结构。

它现在适合：

- 单人持续 vibecoding
- AI agent 接手任务
- 中小规模团队协作
- 老师端 V2 后续收尾和学生端重构

如果要进一步支撑多人并行和长期重构，重点不再是继续移动目录，而是补充 workstream 和 ADR 这两个协作层。
