# 2026-04-27 文档结构清理与归档

> 状态：当前
> 范围：全项目
> 更新：2026-04-27
> 类型：文档

## 背景

项目原有过程文档分散在 `requirements/`、`design/`、`architecture/`、子项目测试目录和 AI 会话历史中。多人继续开发时，模型和研发容易误读旧 PRD、旧线框、旧 API 设计或旧数据字典为当前事实源。

## 变更内容

- 建立 `docs/` 分层文档结构。
- 将当前产品、设计、架构、实现文档迁移到 `docs/01-product/`、`docs/02-design/`、`docs/03-architecture/`、`docs/04-implementation/`。
- 将过时文档归档到 `docs/99-archive/`。
- 新增 `docs/00-index.md`、`docs/01-product/current.md`、`docs/04-implementation/documentation-workflow.md`、`docs/04-implementation/doc-map.md`。
- 新增 `docs/07-changes/` 用于记录后续变更。

## 影响范围

- 产品文档：`docs/01-product/`
- 设计文档：`docs/02-design/`
- 架构文档：`docs/03-architecture/`
- 实施文档：`docs/04-implementation/`
- 归档文档：`docs/99-archive/`
- Agent 入口：`AGENTS.md`、`CLAUDE.md`

## 兼容性与风险

- 旧路径如 requirements/PRD.md、design/web-wireframes.md 已不再作为文档入口。
- 后续模型和研发应从 `docs/00-index.md` 开始阅读。
- 已归档文档仅用于历史对照，不作为当前决策依据。

## 验证方式

- 检查项目自有 Markdown 文档均有中文状态块。
- 检查 `docs/04-implementation/doc-map.md` 覆盖全部项目自有 Markdown。
- 检查具体本地 `.md` / `.html` 引用存在。

## 关联文档

- 当前事实源：`docs/00-index.md`
- 文档流程：`docs/04-implementation/documentation-workflow.md`
- 文档地图：`docs/04-implementation/doc-map.md`

## 后续事项

- [ ] 多人并行开发前，补充 `docs/04-implementation/workstreams/`。
- [ ] 涉及跨模块规则变化时，补充 `docs/03-architecture/decisions/`。
