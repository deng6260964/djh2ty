# 管理端回归刷新工作流

> 状态：当前
> 范围：管理端
> 更新：2026-04-28

## 负责人

Codex

## 目标

按老师端 V2 最新实现重新执行管理端 browser-use 全量回归，刷新验证记录，确认主链路基本收口后的真实可用性。

## 当前进度

状态：已完成。

已有测试文档集中在 `docs/05-testing/browser-use/`。`docs/05-testing/browser-use/full-regression.verification.md` 已记录 2026-04-28 的后端、管理端、学生端构建和管理端 browser-use 回归结果；本轮又补充了基于本地 `postgres:16-alpine` 的 P0 页面级真实浏览器复核。

## 影响范围

- `admin-web/`
- `backend/`
- `docs/05-testing/browser-use/full-regression.verification.md`
- `docs/05-testing/browser-use/dashboard-workbench.verification.md`

## 风险与阻塞

- 需要本地后端、管理端和测试数据处于可用状态。
- 如果验证中发现产品行为变化，应同步更新 PRD、原型或实现计划。
- 如果只更新测试结论而不更新事实源，后续研发会继续读到旧状态。
- 2026-04-28 校正：本地已有启用的 PostgreSQL 环境，镜像应使用 `postgres:16-alpine`。本轮已基于该镜像和 `localhost:5432` 完成 P0 页面级复核。

## 下一步

1. 如后续进入正式发布，按部署环境做最终人工检查。
2. 若新增管理端高风险流程，再开新回归工作流。

## 同步输出

2026-04-28：当前文档中已有一轮回归记录。本轮项目进度检查重新执行后端关键测试、管理端构建、学生端构建，均通过。后端全量 `pytest -q` 通过；真实浏览器复核基于本地 `postgres:16-alpine` 环境完成，覆盖工作台、学生、课程、收费与账户、作业、反馈、学习复盘、资料、设置。
