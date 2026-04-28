# 2026-04-28 AI 编码与文档治理 skill 沉淀

> 状态：当前
> 范围：全项目
> 更新：2026-04-28
> 类型：文档

## 背景

项目已经形成老师端 V2 当前基线、文档归集流程、进度同步和测试文档目录。为了让流程资产可迁移到其他项目，通用 AI 编码流程和文档治理流程不再只作为项目文档维护，而是沉淀为本地 skills；当前项目通过 `AGENTS.md`、`CLAUDE.md` 和适配说明引用它们。

## 变更内容

- 在外部工具包 `docs-governance-toolkit/skills/` 中沉淀两个 skill 源文件。
- 安装本地 skill 副本：`~/.agents/skills/ai-coding-workflow/SKILL.md`。
- 安装本地 skill 副本：`~/.agents/skills/document-governance-workflow/SKILL.md`。
- 将 `docs/04-implementation/development-usage-guide.md` 调整为本项目对两个通用 skill 的适配说明。
- 在 `AGENTS.md` 和 `CLAUDE.md` 中引用两个 skill。
- 更新 `docs/00-index.md` 和 `docs/04-implementation/doc-map.md` 中的说明。

## 影响范围

- 产品文档：不改变当前老师端 V2 产品事实。
- 设计文档：不改变当前原型或交互事实。
- 架构文档：不改变技术架构。
- 后端：无代码影响。
- 管理端：无代码影响。
- 学生端：无代码影响。
- 微信小程序：无代码影响。

## 兼容性与风险

- 是否影响旧数据：否。
- 是否影响现有接口：否。
- 是否影响多人并行开发：是，后续开发和文档治理应优先按两个 workflow skill 执行。
- 是否需要迁移或回滚方案：否。

## 验证方式

- 命令：未运行代码验证，文档和本地 skill 改动。
- 页面：不涉及。
- 数据：不涉及。
- 结果：已检查 skill 文件、入口引用、适配说明、文档地图和变更记录。

## 关联文档

- 本地 skill：`~/.agents/skills/ai-coding-workflow/SKILL.md`
- 本地 skill：`~/.agents/skills/document-governance-workflow/SKILL.md`
- 外部工具包：`/Users/dengjinhui/workspace/self/docs-governance-toolkit/skills/`
- 项目适配：`docs/04-implementation/development-usage-guide.md`
- 文档归集：`docs/04-implementation/documentation-workflow.md`
- 文档地图：`docs/04-implementation/doc-map.md`
- 相关 PR / 提交：暂无

## 后续事项

- [ ] 后续模拟讨论时按两个 workflow skill 逐阶段演练，并根据实际摩擦继续修订项目适配层、任务分级、Gate 和文档触发规则。
