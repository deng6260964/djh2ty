# 断点快照索引

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本目录用于存放一次未完成工作中断前的现场快照。它服务于“下次继续”或“换人接手”，不替代工作流文档、实现计划或变更记录。

## 目录规则

按月份分组：

```text
docs/08-progress/checkpoints/YYYY-MM/YYYY-MM-DD-workstream-owner.md
```

## 推荐生成方式

优先由模型或 skill 主动触发脚本生成草稿：

```bash
node scripts/create-checkpoint.mjs --workstream student-web-v2-rework --owner codex
```

脚本负责自动采集 Git 分支、当前提交、变更文件、diff 统计、最近提交和建议验证命令。模型负责补齐本次目标、已完成、未完成、风险与下一步。

## 处理状态

| 状态 | 含义 |
| --- | --- |
| open | 等待后续恢复 |
| resumed | 已经被下一次工作接上 |
| closed | 任务完成，信息已沉淀到事实源或变更记录 |
| archived | 过期保留，仅作参考 |

## 清理规则

- checkpoint 被恢复后，将处理状态改为 `resumed`。
- 工作流完成后，将相关 checkpoint 改为 `closed`，并把完成事实沉淀到 `docs/07-changes/`。
- 长期无价值的 checkpoint 可归档，但不要删除仍有恢复价值的现场信息。
