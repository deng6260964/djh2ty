# 项目文档入口

> 状态：当前
> 范围：全项目
> 更新：2026-04-26

本目录是项目级文档治理入口，用于说明当前应该优先阅读哪些文档、归档材料如何使用、AI 会话记录如何归集。

## 从这里开始

- `docs/04-implementation/documentation-workflow.md` — 文档归集规则、检索顺序、vibecoding 工作流和交接清单
- `docs/04-implementation/doc-map.md` — 项目自有 Markdown 文档地图，列出每份文档的状态和用途
- `docs/07-changes/README.md` — 变更记录目录说明

## 当前活跃基线

当前产品基线是老师端 V2 改造。阅读旧文档前，请先阅读这些当前文档：

- `docs/01-product/current.md` — 当前产品基线入口
- `docs/01-product/teacher-v2/status.md` — 当前项目状态和下一步
- `docs/01-product/teacher-v2/prd.md` — 当前老师端 PRD
- `docs/02-design/teacher-v2/prototype.md` — 当前老师端原型说明
- `docs/04-implementation/teacher-v2/plan.md` — 实施进度和剩余工作

## 当前文档架构

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

## 文档地图

需要查找所有项目自有 Markdown 文档、判断文档是当前/参考/归档，或决定新文档应该放在哪里时，使用 `docs/04-implementation/doc-map.md`。

## 归档材料

过时文档已移入 `docs/99-archive/`，只用于历史对照，不应作为当前默认事实源：

- `docs/99-archive/legacy/product/prd-v1.md`
- `docs/99-archive/legacy/product/flows-v1.md`
- `docs/99-archive/legacy/product/user-stories-v1.md`
- `docs/99-archive/legacy/design/web-wireframes-v1.md`

## AI 会话记录

`.specstory/` 是原始 AI 会话历史。重要决策、进度变化和后续任务不能只留在原始对话里，应归纳到当前文档；如果不适合放入产品、设计、实现或架构文档，可归档到 `docs/06-ai-worklogs/`。

## 变更记录

已经确认或完成的重要变更，应记录到 `docs/07-changes/`。变更记录用于说明“改了什么、为什么改、影响哪里、如何验证”，方便多人并行开发时追溯上下文。
