# 老师端 V2 主链路收口

> 状态：当前
> 范围：backend、admin-web、docs
> 更新：2026-04-27
> 日期：2026-04-27
> 类型：实现

## 背景

老师端 V2 仍遗留课程详情闭环、请假 / 待补课池、学生详情复盘入口、学习复盘白屏和 `antd` 大 chunk 等问题。本次集中补齐老师端主链路，避免完成课程、课后记录、作业、扣费和补课继续割裂。

## 变更内容

- 新增课程详情聚合接口 `GET /api/courses/{id}/detail-v2`。
- 新增课程完成接口 `POST /api/courses/{id}/complete`，支持保存课后反馈、可选布置作业、完成课程和自动扣费。
- 新增请假 / 待补课池接口：
  - `POST /api/courses/{id}/leave`
  - `GET /api/courses/makeup-pool`
  - `POST /api/courses/{id}/makeup`
- 新增学生详情作业接口 `GET /api/students/{id}/assignments`。
- 管理端课程页新增课程详情弹窗、保存并完成课程、请假转待补、待补课池和安排补课入口。
- 学生详情新增课后反馈和学习复盘 Tab。
- 修复学习复盘页知识点接口返回结构不匹配导致的白屏。
- 调整 Vite 拆包策略，取消把 `antd` 聚合成单个大 chunk。

## 影响范围

- 课程完成现在可以从课程详情弹窗中完成课后记录、作业和自动扣费。
- 请假课程会进入待补课池，安排补课后原课程状态变为 `makeup_scheduled`。
- 学生详情可直接查看作业、账户、课后反馈和学习复盘。
- 管理端构建产物不再出现单个 `antd` 约 1.1MB 的 chunk。

## 验证方式

- `cd backend && pytest -q`
- `cd admin-web && npm run build`

## 后续注意

- browser-use 全量回归记录需要基于最新实现重新执行并刷新。
- 学生端新版承接仍是独立后续工作。
