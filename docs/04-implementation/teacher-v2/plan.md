# 家教辅助系统 V2 老师端实现拆解

> 状态：当前
> 范围：老师端 V2
> 更新：2026-04-27
> 版本：1.0
> 日期：2026-04-21
> 基于文档：
> - `docs/01-product/teacher-v2/prd.md`
> - `docs/02-design/teacher-v2/prototype.md`
> - `docs/02-design/teacher-v2/flow-prototype.md`
> - `docs/02-design/teacher-v2/hifi-prototype/index.html`

## 0. 进度状态（2026-04-23）

### 0.1 当前判断

本计划已不再是纯待办文档，老师端第一阶段和大部分第二、第三阶段内容已经落地到真实代码。

### 0.2 Phase 状态

| Phase | 状态 | 说明 |
| --- | --- | --- |
| Phase 1：主链路闭环 | 已完成 | 已落地工作台、课程周视图、课程详情课后记录、可选作业、学生账户、收费提醒、预收充值、完成课程自动扣费主链路 |
| Phase 2：课程运营能力 | 已完成老师端基础闭环 | 已落地复制上一周课程、调课入口、完成/取消、取消或删除已完成课程后的自动扣费回滚、请假/待补课池/安排补课 |
| Phase 3：老师端效率增强 | 大部分完成 | 已落地作业中心、设置页、收费与账户页重构；反馈/进度已进入学生详情，同时保留一级入口用于集中复盘 |

### 0.3 已落地清单

- 老师工作台：`/dashboard`
- 课程 7 天周视图：`/courses`
- 课程详情闭环：课后记录、最近反馈/作业、可选布置作业、保存并完成课程、自动扣费
- 复制上一周课程：预览 + 确认接口与前端弹窗
- 课程调课基础能力：课程编辑、完成、取消、请假、待补课池、安排补课
- 完成课程自动扣费：完成课程时生成扣费记录并更新学生账户余额
- 取消 / 删除已完成课程回滚：删除对应自动扣费记录，恢复学生账户余额
- 学生账户、课后反馈、学习复盘：学生详情中的 Tab
- 收费与账户页：待收费学生、预收充值、未结清记录、课时单价、汇总报表
- 设置页：课时单价与提醒规则说明
- 作业中心、反馈复盘、学习复盘：已按新版语义做一轮页面收口
- 管理端构建拆包：移除单个 `antd` 大 chunk

### 0.4 待继续项

- 按最新实现重新执行 browser-use 全量回归并刷新验证记录
- 学生端按新版承接方案继续重构
- 若继续做性能优化，可进一步分析首屏依赖和按页拆包

## 1. 文档目标

本文件用于把新版老师端 PRD 和高保真原型拆解成可执行的开发任务。

输出目标：

- 明确老师端优先实现顺序
- 明确每个模块的前后端边界
- 明确数据库和接口需要补什么
- 明确哪些旧模块要保留，哪些要重构

## 2. 实施总原则

### 2.1 先打通主链路，再补外围

优先打通：

`工作台 -> 课程总览 -> 课程详情 -> 课后记录 -> 自动扣费 -> 收费提醒 -> 学生账户`

不要先做：

- 花哨图表
- 复杂统计
- 次要资料能力
- 非主流程提醒

### 2.2 尽量基于现有后端演进

当前仓库里已有：

- 学生
- 课程
- 作业
- 收费
- 资料
- 仪表盘

所以实现策略应为：

- 复用已有模型和路由骨架
- 调整字段和聚合接口
- 减少无必要的整体推翻

### 2.3 先让老师端可用，再追求完全一致

高保真稿是目标体验，但开发优先级以流程可用为主。

## 3. 建议的实现阶段

## Phase 1：主链路闭环

目标：

- 老师每天能用系统完成最核心的 5 件事

范围：

- 工作台
- 课程总览
- 课程详情
- 课后记录
- 自动扣费
- 待收费提醒
- 学生账户页

验收标准：

- 老师可看到今日课程、待补记录、待收费提醒
- 老师可完成一节课并自动扣费
- 系统可根据余额判断下一节课是否需收费
- 老师可录入收款并即时解除提醒

## Phase 2：课程运营能力

目标：

- 课程管理从“能排课”升级成“能处理真实变化”

范围：

- 复制上一周课程
- 调课
- 学生请假
- 老师请假
- 取消课
- 待补课池

验收标准：

- 支持整周复制课程并预检冲突/收费风险
- 支持课程调整且不丢失记录
- 支持取消已扣费课程后的余额回滚

## Phase 3：老师端效率增强

目标：

- 集中处理跨学生任务

范围：

- 作业中心
- 批改侧边栏
- 学生列表和详情强化
- 设置中心

验收标准：

- 作业待批改能集中处理
- 学生详情能完整查看账户和课程状态
- 单价和提醒规则可配置

## 4. 页面实现顺序

### 4.1 第一批页面

1. 老师工作台
2. 课程总览
3. 课程详情
4. 学生账户页

原因：

- 它们构成最小业务闭环

### 4.2 第二批页面

1. 调课与请假
2. 复制上一周课程
3. 新增学生
4. 快捷收款弹窗

### 4.3 第三批页面

1. 作业中心
2. 设置中心
3. 资料页适配新版风格

## 5. 页面级任务拆分

## 5.1 工作台

### 页面目标

把当天最需要处理的动作集中到一屏。

### 前端任务

- 新建工作台页面容器
- 实现 4 个核心卡片区块
  - 今日课程
  - 待补记录
  - 待收费提醒
  - 待批改作业
- 实现快速操作入口
- 实现快捷收款弹窗

### 后端任务

新增聚合接口：

`GET /api/dashboard/workbench`

返回建议结构：

```json
{
  "summary": {
    "pending_record_count": 3,
    "today_course_count": 5,
    "payment_alert_count": 2,
    "assignment_review_count": 4
  },
  "today_courses": [],
  "pending_records": [],
  "payment_alerts": [],
  "assignment_reviews": []
}
```

### 关键规则

- 待补记录优先级高于今日课程
- 收费提醒基于下一节课预计费用判断

## 5.2 课程总览

### 页面目标

支持老师查看整周课程密度，快速排课，并处理复制上一周课程。

### 前端任务

- 实现完整 7 天周视图
- 支持课程状态样式
- 支持周末高频排课展示
- 实现快速排课弹窗
- 实现复制上一周课程入口和批量预览弹窗

### 后端任务

已有接口可保留，但建议新增/扩展：

`GET /api/courses/week`

参数：

- `start_date`
- `end_date`
- `student_id`
- `subject`
- `status`

新增接口：

`POST /api/courses/copy-week-preview`

请求：

```json
{
  "source_week_start": "2026-04-13",
  "target_week_start": "2026-04-20"
}
```

返回：

```json
{
  "copyable": [],
  "conflicts": [],
  "payment_alerts": []
}
```

新增接口：

`POST /api/courses/copy-week-confirm`

### 关键规则

- 复制前先预检冲突
- 复制前先预判收费风险
- 冲突课程默认不复制

## 5.3 课程详情

### 页面目标

把一节课的所有课后动作都收束到一页完成。

### 前端任务

- 实现课程基本信息区
- 实现课前速览区
- 实现课后记录表单
- 实现本节作业区
- 实现自动扣费展示区
- 实现“保存并完成课程”完整交互

### 后端任务

建议新增：

`GET /api/courses/{id}/detail-v2`

返回：

- 课程基础信息
- 学生课前信息
- 最近反馈摘要
- 最近作业摘要
- 当前余额
- 预计扣费
- 下一节课风险

建议新增：

`POST /api/courses/{id}/complete`

请求：

```json
{
  "actual_duration": 1.5,
  "summary": "...",
  "performance": "...",
  "risk_notes": "...",
  "next_plan": "...",
  "need_parent_attention": true,
  "assignment": {
    "enabled": true,
    "title": "...",
    "content": "...",
    "due_at": "2026-04-23T20:00:00"
  }
}
```

返回：

```json
{
  "course_status": "completed",
  "charge_amount": 180,
  "balance_before": 120,
  "balance_after": -60,
  "payment_alert_triggered": true
}
```

### 关键规则

- 完成课程动作必须原子化处理
- 记录保存、扣费、提醒生成要么都成功，要么整体回滚

## 5.4 调课 / 请假 / 取消课

### 页面目标

处理课程变更，不丢业务上下文。

### 前端任务

- 实现调课弹窗
- 实现请假 / 取消课弹窗
- 展示处理后结果
- 支持“转入待补课”

### 后端任务

新增接口：

`POST /api/courses/{id}/reschedule`

`POST /api/courses/{id}/leave`

`POST /api/courses/{id}/cancel`

如课程已扣费，取消时需要支持：

`POST /api/courses/{id}/rollback-charge`

### 关键规则

- 调课优先，不建议直接删除课程
- 请假默认不扣费
- 已扣费课程取消后必须支持余额回滚

## 5.5 学生列表与详情

### 页面目标

老师能快速切换学生并看到全貌。

### 前端任务

- 实现学生列表轻量摘要
- 实现学生详情页
- 实现账户 Tab
- 实现新增学生弹窗
- 实现从学生页快速排课 / 收款

### 后端任务

扩展学生列表接口字段：

- 当前余额
- 下一节课时间
- 风险标签
- 最近上课时间

建议新增：

`GET /api/students/{id}/overview-v2`

返回：

- 基本信息
- 课程摘要
- 账户摘要
- 风险标签
- 最近作业和反馈摘要

### 关键规则

- 学生页先展示状态，不先展示长表格

## 5.6 学生账户

### 页面目标

让老师最短路径看到余额和流水。

### 前端任务

- 当前余额卡
- 最近收款卡
- 最近扣费卡
- 时间线流水
- 录入收款弹窗

### 后端任务

建议新增：

`GET /api/students/{id}/account`

返回：

```json
{
  "balance": 120,
  "estimated_lessons_left": 1.0,
  "recent_payments": [],
  "recent_charges": [],
  "payment_alert": true
}
```

建议新增：

`POST /api/students/{id}/account/payments`

### 关键规则

- 录入收款后要即时刷新余额和风险状态

## 5.7 作业中心

### 页面目标

支持跨学生集中批改和查看作业状态。

### 前端任务

- 实现 4 个标签页
  - 待批改
  - 进行中
  - 已完成
  - 逾期未交
- 实现批改侧边栏

### 后端任务

扩展作业列表接口支持任务视角查询：

`GET /api/assignments/review-center`

参数：

- `status`
- `student_id`
- `date_range`

## 5.8 设置中心

### 页面目标

管理规则，而不是承载日常操作。

### 前端任务

- 单价管理
- 提醒规则设置

### 后端任务

已有单价接口可复用，但建议补充：

- 生效时间
- 历史单价记录

提醒规则可先走简单配置接口：

`GET /api/settings/reminders`

`PUT /api/settings/reminders`

## 6. 数据结构调整建议

## 6.1 课程状态

当前建议状态：

- `scheduled`
- `completed_pending_record`
- `completed`
- `cancelled`
- `leave_pending_makeup`

说明：

- 如果不想大改现有状态枚举，也可通过补字段实现

备选方案：

- 课程主状态继续保留
- 增加 `record_completed` 布尔字段
- 增加 `makeup_required` 布尔字段

## 6.2 学生账户

当前收费模块建议从“账单”转向“账户”抽象。

建议新增或抽象：

- `student_account_balance`
- `account_payment_records`
- `account_charge_records`

如果不想新建账户表，也可基于现有 billing 体系做聚合，但要保证前端能拿到：

- 当前余额
- 最近收款
- 最近扣费
- 风险状态

## 6.3 课程完成动作

建议把“课后记录 + 扣费 + 提醒生成”封装成应用服务，不要散落在多个 router 中。

建议新增服务层：

- `CourseCompletionService`
- `PaymentAlertService`
- `WeeklyCopyService`

## 7. 接口清单建议

## 7.1 新增接口

- `GET /api/dashboard/workbench`
- `GET /api/courses/week`
- `POST /api/courses/copy-week-preview`
- `POST /api/courses/copy-week-confirm`
- `GET /api/courses/{id}/detail-v2`
- `POST /api/courses/{id}/complete`
- `POST /api/courses/{id}/reschedule`
- `POST /api/courses/{id}/leave`
- `POST /api/courses/{id}/cancel`
- `POST /api/courses/{id}/rollback-charge`
- `GET /api/students/{id}/overview-v2`
- `GET /api/students/{id}/account`
- `POST /api/students/{id}/account/payments`
- `GET /api/assignments/review-center`
- `GET /api/settings/reminders`
- `PUT /api/settings/reminders`

## 7.2 可复用接口

- 学生列表
- 基础课程列表
- 作业详情和批改
- 科目单价配置
- 资料管理

## 8. 前端代码组织建议

以 `admin-web` 为主，建议新建或重构：

### 页面目录

- `src/pages/Workbench`
- `src/pages/Courses`
- `src/pages/CourseOperations`
- `src/pages/Students`
- `src/pages/Assignments`
- `src/pages/Settings`

### 组件目录

- `src/components/workbench`
- `src/components/course`
- `src/components/student`
- `src/components/assignment`
- `src/components/account`

### API 目录

- `src/api/workbench.ts`
- `src/api/courseOperations.ts`
- `src/api/accounts.ts`
- `src/api/settings.ts`

## 9. 后端代码组织建议

以 `backend/app` 为主，建议新增：

### routers

- `workbench.py`
- `course_operations.py`
- `accounts.py`
- `settings.py`

### schemas

- `workbench.py`
- `course_operations.py`
- `account.py`
- `settings.py`

### services

- `services/course_completion.py`
- `services/weekly_copy.py`
- `services/accounting.py`
- `services/payment_alerts.py`

## 10. 实施顺序建议

### Sprint 1

- 工作台接口
- 课程详情完成闭环
- 账户页和收款

### Sprint 2

- 课程总览
- 复制上一周课程
- 调课 / 请假 / 取消课

### Sprint 3

- 学生列表和详情
- 作业中心
- 设置中心

## 11. 最小发布建议

如果要尽快落地一版可用产品，建议最小发布只包含：

- 工作台
- 课程总览
- 课程详情
- 学生账户
- 快捷收款
- 简化版学生详情

这已经足以支撑老师真实工作。

## 12. 当前高保真与开发映射

当前老师端高保真已覆盖：

- 工作台
- 课程总览
- 复制上一周课程
- 调课与请假
- 课程详情
- 学生列表与学生详情
- 作业中心
- 设置中心

因此接下来完全可以按页面逐个实现，而不是重新设计。
