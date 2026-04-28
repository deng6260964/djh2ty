# 新增断点快照流程

> 状态：当前
> 范围：文档、全项目
> 更新：2026-04-28

## 背景

当前 `docs/08-progress/` 已经可以记录工作流级别的进行态，但还缺少一次未完成对话或一次中断现场的恢复记录。多人并行和 AI 协作时，如果任务没有完成就中断，后续接手者需要知道本次目标、已完成事项、未完成事项、风险和下一步。

## 变更内容

- 新增 `docs/08-progress/checkpoints/` 作为断点快照目录。
- 新增 `scripts/create-checkpoint.mjs`，自动采集 Git 分支、当前提交、变更文件、diff 统计、最近提交和建议验证命令。
- 新增 `scripts/check-progress.mjs`，校验 checkpoint 引用的 workstream、处理状态和长期开启状态。
- 更新文档流程，明确 checkpoint 由模型或 skill 主动触发，不使用 Git hooks 强制拦截。

## 影响范围

- 未完成任务中断时，可以通过 checkpoint 快速恢复现场。
- 多人并行时，每个人或每个 agent 使用独立 checkpoint 文件，减少同一进度文档的编辑冲突。
- 完成态事实仍需沉淀到 `docs/07-changes/`，不能只停留在 checkpoint。

## 兼容性与风险

无代码运行时影响。主要风险是 checkpoint 被生成后未由模型补齐上下文，因此流程要求脚本生成后必须补充“本次目标、已完成、未完成、风险与下一步”。

## 验证方式

- `node scripts/check-progress.mjs`
- 项目文档一致性检查

## 后续事项

- 后续可以将通用工具包中的 `progress-checkpoint` skill 安装到具体 agent 环境，进一步降低人工操作。
