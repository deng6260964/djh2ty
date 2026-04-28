# 2026-04-28 测试流程指南归集

> 状态：当前
> 范围：测试、文档
> 更新：2026-04-28
> 类型：文档

## 背景

老师端 V2 已进入主链路基本收口阶段，后端 pytest、管理端 browser-use、人工专项验收和文档归集已经形成一套实践经验。为了避免后续测试依赖原始 AI 对话或零散执行记录，需要将流程沉淀为长期测试文档。

## 变更内容

- 新增 `docs/05-testing/testing-workflow.md`，覆盖测试分层、用例编写、执行动作、失败处理、文档归集和交接清单。
- 更新 `docs/05-testing/README.md`，将测试流程指南加入测试文档入口。
- 更新 `docs/04-implementation/doc-map.md`，登记新增长期测试文档。

## 影响范围

- 产品文档：无。
- 设计文档：无。
- 架构文档：无。
- 后端：无代码变更。
- 管理端：无代码变更。
- 学生端：无代码变更。
- 微信小程序：无代码变更。

## 兼容性与风险

- 是否影响旧数据：否。
- 是否影响现有接口：否。
- 是否影响多人并行开发：正向影响，统一测试与交接口径。
- 是否需要迁移或回滚方案：否。

## 验证方式

- 命令：未执行代码测试，仅进行文档归集。
- 页面：不涉及。
- 数据：不涉及。
- 结果：测试流程文档已加入 `docs/05-testing/` 入口和文档地图。

## 关联文档

- 当前事实源：`docs/05-testing/testing-workflow.md`
- 测试入口：`docs/05-testing/README.md`
- 文档地图：`docs/04-implementation/doc-map.md`
- AI 工作日志：无。
- 相关 PR / 提交：无。

## 后续事项

- [ ] 按最新老师端实现重新执行 `docs/05-testing/browser-use/full-regression.spec.md`。
- [ ] 刷新 `docs/05-testing/browser-use/full-regression.verification.md`，确认学习复盘修复后的结果。
