# 家教辅助系统 V2 项目状态

> 状态：当前
> 范围：老师端 V2
> 更新：2026-04-26
> 更新日期：2026-04-26
> 适用范围：老师端 V2 改造进度跟踪

## 1. 当前结论

老师端 V2 已经从“方案和原型阶段”进入“真实可用但仍需收尾”的阶段。

目前最核心的老师端主链路已经具备：

- 工作台查看待办
- 课程周视图与周末排课
- 复制上一周课程
- 调课 / 完成 / 取消
- 学生账户查看
- 预收充值
- 收费提醒

## 2. 已完成

### 后端

- `GET /api/dashboard/workbench`
- `GET /api/courses/week`
- `POST /api/courses/copy-week-preview`
- `POST /api/courses/copy-week-confirm`
- `GET /api/billing/students/{id}/account`
- `POST /api/billing/recharge`

### 前端

- 老师工作台
- 课程页新版周视图
- 复制上一周课程弹窗
- 学生详情账户 Tab
- 收费与账户页重构
- 设置页
- 作业中心、反馈复盘、学习复盘的一轮收口
- 路由级懒加载与构建拆包

## 3. 进行中 / 待收尾

- 课程详情中的课后记录、反馈、作业进一步串联
- 请假 / 待补课池
- 取消课后的余额回滚规则
- 学生端按新版方案继续重构
- `antd` 大包进一步优化

## 4. 文档关系

- 文档归集流程：`docs/04-implementation/documentation-workflow.md`
- 文档地图：`docs/04-implementation/doc-map.md`
- 产品基线：`docs/01-product/teacher-v2/prd.md`
- 原型基线：`docs/02-design/teacher-v2/prototype.md`
- 开发拆解：`docs/04-implementation/teacher-v2/plan.md`

当前已经补充文档归集入口 `docs/00-index.md`、完整文档地图 `docs/04-implementation/doc-map.md`，并将归集流程引入 `AGENTS.md` 与 `CLAUDE.md`。

## 5. 建议执行顺序

1. 继续补课程详情闭环
2. 完成请假 / 待补课池
3. 收口学生端
4. 最后做更深的前端性能优化
