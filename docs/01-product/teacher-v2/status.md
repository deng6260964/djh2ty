# 家教辅助系统 V2 项目状态

> 状态：当前
> 范围：老师端 V2
> 更新：2026-04-28
> 更新日期：2026-04-28
> 适用范围：老师端 V2 改造进度跟踪

## 1. 当前结论

老师端 V2 已经从“真实可用但仍需收尾”进入“主链路开发与验收收敛完成”的阶段。老师端主链路已经基本收口，学生端也已完成课程、作业、反馈、资料、学习进度和账户余额的基础承接，并通过本地真实浏览器冒烟。

目前最核心的老师端主链路已经具备：

- 工作台查看待办
- 课程周视图与周末排课
- 复制上一周课程
- 调课 / 完成 / 取消
- 课程详情中填写课后记录、可选布置作业并完成课程
- 完成课程自动扣费
- 取消 / 删除已完成课程后的自动扣费回滚
- 请假 / 待补课池 / 安排补课
- 学生账户查看
- 预收充值
- 收费提醒
- 学生详情内查看课后反馈和学习复盘
- 学生/家长端查看课程、作业、反馈、学习资料、学习进度、账户余额与最近扣费

## 2. 已完成

### 后端

- `GET /api/dashboard/workbench`
- `GET /api/courses/week`
- `GET /api/courses/{id}/detail-v2`
- `POST /api/courses/{id}/complete`
- `POST /api/courses/{id}/leave`
- `GET /api/courses/makeup-pool`
- `POST /api/courses/{id}/makeup`
- `POST /api/courses/copy-week-preview`
- `POST /api/courses/copy-week-confirm`
- `PATCH /api/courses/{id}/status` 完成课程时生成自动扣费记录，取消已完成课程时回滚自动扣费
- `DELETE /api/courses/{id}` 删除已自动扣费课程时回滚自动扣费
- `GET /api/billing/students/{id}/account`
- `GET /api/billing/my/account`
- `POST /api/billing/recharge`
- `GET /api/students/{id}/assignments`
- 学生端 `/my` 接口：`/api/courses/my`、`/api/assignments/my`、`/api/feedback/my`、`/api/resources/shared`、`/api/progress/my`

### 前端

- 老师工作台
- 课程页新版周视图
- 课程详情弹窗：最近反馈 / 最近作业 / 课后记录 / 可选布置作业 / 保存并完成课程
- 请假 / 待补课池 / 安排补课入口
- 复制上一周课程弹窗
- 学生详情账户、课后反馈、学习复盘 Tab
- 收费与账户页重构
- 设置页
- 作业中心、反馈复盘、学习复盘的一轮收口
- 路由级懒加载与构建拆包；移除单个 `antd` 大 chunk
- 学生端新版基础承接：首页、课程、作业、反馈、学习进度、资料、账户明细
- 学生端路由级懒加载与构建拆包，移除单个 1.2 MB 入口包

## 3. 进行中 / 待收尾

- 当前主链路开发、自动化验证和本地真实浏览器冒烟均已收敛。
- 正式发布前如切换部署环境，建议再做一轮人工账号、数据备份和关键路径检查。

## 4. 文档关系

- 文档归集流程：`docs/04-implementation/documentation-workflow.md`
- 文档地图：`docs/04-implementation/doc-map.md`
- 产品基线：`docs/01-product/teacher-v2/prd.md`
- 原型基线：`docs/02-design/teacher-v2/prototype.md`
- 开发拆解：`docs/04-implementation/teacher-v2/plan.md`

当前已经补充文档归集入口 `docs/00-index.md`、完整文档地图 `docs/04-implementation/doc-map.md`，并将归集流程引入 `AGENTS.md` 与 `CLAUDE.md`。

## 5. 建议执行顺序

1. 如进入正式发布，做部署环境人工检查和数据备份确认。
2. 若后续继续做性能优化，再进一步分析真实加载体验和按页依赖。
3. 新功能、新互动或更完整 E2E 自动化另开工作流。
