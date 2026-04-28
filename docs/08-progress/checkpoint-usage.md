# Checkpoint 断点使用说明

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文说明在 vibecoding、多人并行开发或 AI 协作中，如何保存和恢复未完成任务的中间态。

## 什么时候使用

出现以下情况时，建议生成 checkpoint：

- 用户说“暂停一下”“先到这里”“下次继续”“保存现场”。
- 当前任务还没完成，但已经做了文件修改或形成了关键判断。
- 任务需要换人、换 agent 或隔天继续。
- 工作流进入 `阻塞` 或 `待验证`。
- 后续接手者如果不看完整对话，就难以恢复现场。

不需要为每个小改动都生成 checkpoint。已经完成并验证的事项，应写入 `docs/07-changes/`，而不是 checkpoint。

## 保存断点

推荐由模型或 skill 主动执行：

```bash
node scripts/create-checkpoint.mjs --workstream student-web-v2-rework --owner codex
```

常用参数：

| 参数 | 说明 | 示例 |
| --- | --- | --- |
| `--workstream` | 关联的工作流文件名，不含 `.md` | `student-web-v2-rework` |
| `--owner` | 当前负责人、研发或 agent | `codex`、`claude`、`zhangsan` |
| `--scope` | 影响范围，未传时脚本会按变更文件推断 | `学生端`、`管理端`、`文档` |
| `--reason` | 中断原因 | `用户暂停，方案未完成` |
| `--dry-run` | 只预览，不写文件 | 用于检查脚本输出 |

脚本会自动生成文件到：

```text
docs/08-progress/checkpoints/YYYY-MM/YYYY-MM-DD-workstream-owner.md
```

脚本负责自动采集：

- 当前 Git 分支
- 当前提交
- 变更文件
- 最近修改文档
- diff 统计
- 最近提交
- 建议验证命令

## 模型需要补齐什么

脚本生成的是草稿。生成后，模型或 agent 应补齐这些部分：

- 本次目标：这次原本要完成什么。
- 已完成：已读文档、已做修改、已确认判断、已跑验证。
- 未完成：还差什么，哪些判断未确认。
- 风险与阻塞：当前风险、阻塞点、不要重复探索的路径。
- 下一步：恢复时先读什么、先执行什么、先验证什么。

checkpoint 应短而密，不要粘贴完整聊天记录。

## 恢复工作

恢复未完成任务时，按以下顺序阅读：

1. `docs/08-progress/project-status.md`
2. 对应 `docs/08-progress/workstreams/*.md`
3. 最新的 open checkpoint
4. 相关产品、设计、实现或测试文档

恢复后，将 checkpoint 的处理状态从：

```md
> 处理状态：open
```

改为：

```md
> 处理状态：resumed
```

如果任务最终完成，并且完成事实已经进入 `docs/07-changes/` 或对应事实源文档，则改为：

```md
> 处理状态：closed
```

## 检查进度文档

运行：

```bash
node scripts/check-progress.mjs
```

它会检查：

- checkpoint 引用的 workstream 是否存在。
- checkpoint 处理状态是否合法。
- 同一个 workstream 是否存在多个 open checkpoint。
- open checkpoint 是否长时间未处理。

## 多人并行约定

- 每个研发或 agent 使用独立 checkpoint 文件，不要多人同时编辑同一份 checkpoint。
- checkpoint 文件名应包含日期、workstream 和负责人。
- 一个 workstream 尽量只保留一个 open checkpoint。
- checkpoint 恢复后及时改为 `resumed` 或 `closed`。

## 与其他文档的边界

| 文档类型 | 作用 |
| --- | --- |
| `docs/04-implementation/` | 说明怎么实现，记录方案和任务拆解 |
| `docs/08-progress/workstreams/` | 记录某个需求、重构或测试专项的持续进行态 |
| `docs/08-progress/checkpoints/` | 保存一次未完成工作的恢复现场 |
| `docs/07-changes/` | 记录已经确认或完成的事实 |
| `docs/06-ai-worklogs/` | 沉淀可复用的 AI 会话结论 |
