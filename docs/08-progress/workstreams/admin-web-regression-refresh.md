# 管理端回归刷新工作流

> 状态：当前
> 范围：管理端
> 更新：2026-04-28

## 负责人

未分配

## 目标

按老师端 V2 最新实现重新执行管理端 browser-use 全量回归，刷新验证记录，确认主链路基本收口后的真实可用性。

## 当前进度

状态：待开始。

已有测试文档集中在 `docs/05-testing/browser-use/`，但验证记录需要按最新代码和最新数据状态重新执行后刷新。

## 影响范围

- `admin-web/`
- `backend/`
- `docs/05-testing/browser-use/full-regression.verification.md`
- `docs/05-testing/browser-use/dashboard-workbench.verification.md`

## 风险与阻塞

- 需要本地后端、管理端和测试数据处于可用状态。
- 如果验证中发现产品行为变化，应同步更新 PRD、原型或实现计划。
- 如果只更新测试结论而不更新事实源，后续研发会继续读到旧状态。

## 下一步

1. 启动本地数据库、后端和管理端。
2. 按 `docs/05-testing/browser-use/full-regression.spec.md` 执行全量回归。
3. 按结果刷新验证记录。
4. 如发现缺陷，创建新的工作流或变更记录。

## 同步输出

暂无。执行后应记录测试时间、环境、通过项、失败项、截图或关键观察。
