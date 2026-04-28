# Browser-use 全量回归验证记录

> 状态：参考
> 范围：管理端
> 更新：2026-04-26
> 验证时间：2026-04-26
> 验证目标：`docs/05-testing/browser-use/full-regression.spec.md`
> 验证方式：Codex in-app browser + `browser-use`，辅以后端 API 创建测试数据。

## 环境

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`
- 后端健康检查：通过，`{"status":"ok","service":"家教辅助系统"}`
- 登录账号：`admin / admin123`

## 测试数据

本次为执行数据依赖用例，创建了以下测试数据：

- 学生：`BU测试学生-213455`
- 年级：`初二`
- 科目：`数学`、`英语`
- 家长电话：`18800000001`
- 预收充值：`¥300`
- 测试课程：`2026-04-26 09:00-10:30 数学`

说明：删除类用例未执行，因为会删除本地数据，需要用户单独确认。

## 结果汇总

| 分类 | 结果 |
| --- | --- |
| 服务健康检查 | 通过 |
| 认证与路由守卫 | 通过 |
| 全局布局与导航 | 通过 |
| 工作台 | 通过 |
| 学生管理 | 通过 |
| 课程管理 | 通过 |
| 收费与账户 | 通过 |
| 作业中心 | 通过 |
| 反馈复盘 | 通过 |
| 资料管理 | 通过 |
| 设置 | 通过 |
| 学习复盘 | 失败 |
| P0 主业务链 | 通过 |
| 删除类用例 | 未执行，需确认 |
| 真实文件上传/下载/分享 | 未执行，需准备测试文件与确认上传 |

## 已通过用例

### 认证与布局

- `BU-AUTH-001` 未登录访问 `/dashboard` 自动跳转 `/login`
- `BU-AUTH-002` 管理员登录后进入 `/dashboard`
- `BU-AUTH-003` 已登录访问 `/login` 自动回工作台
- `BU-AUTH-004` 退出登录后回到 `/login`
- `BU-LAYOUT-001` 侧边栏折叠按钮存在，导航结构可见

### 工作台

- `BU-DASH-001` 工作台 V2 信息结构可见
- `BU-DASH-002` 空数据状态可读
- `BU-DASH-003` “快速排课”弹窗可打开，字段完整
- `BU-DASH-004` 快速操作按钮存在，可进入课程、学生、收费页

### 学生管理

- `BU-STU-001` 学生页结构通过
- `BU-STU-002` 新增学生必填校验通过
- `BU-STU-003` 使用测试数据验证学生列表可显示新学生

### 课程管理

- `BU-COURSE-001` 课程页结构通过
- `BU-COURSE-002` 排课表单必填校验通过
- `BU-COURSE-003` 使用测试数据验证课程页可显示新课程
- `BU-COURSE-007` 点击“完成”后课程状态变为“已完成”

### 收费与账户

- `BU-BILL-001` 收费页结构通过
- `BU-BILL-002` 记录预收充值必填校验通过
- `BU-BILL-003` 使用测试数据验证充值统计/记录可追踪
- `BU-BILL-006` 课时单价设置弹窗可打开

### 作业中心

- `BU-ASG-001` 作业页结构通过
- `BU-ASG-002` 布置作业必填校验通过

### 反馈复盘

- `BU-FB-001` 反馈页结构通过
- `BU-FB-002` 新建反馈弹窗可打开，关联课程、本节课表现、知识点掌握、存在问题、下节课计划等区域可见

备注：反馈表单使用富文本编辑器，空内容提交后没有稳定的原生错误文案暴露到 DOM；本次以弹窗结构和必填区域存在性作为验证依据。

### 资料管理

- `BU-RES-001` 资料页结构通过
- `BU-RES-002` 上传资料弹窗可打开，不填资料名称提交后显示“请输入资料名称”

### 设置

- `BU-SET-001` 设置页结构通过

### P0 主业务链

- `BU-FLOW-001-PREP` 测试学生课程在课程页可见且状态为待上课
- `BU-COURSE-007` 课程完成动作通过
- `BU-FLOW-001-STUDENT` 完成课程后学生列表仍可追踪
- `BU-FLOW-001-BILLING` 收费页可追踪充值金额
- `BU-FLOW-001-DASHBOARD` 完成主链后工作台仍可加载，并展示今日课程

## 失败用例

### `BU-PROG-001` / `BU-PROG-002` 学习复盘页面失败

> 2026-04-27 代码修复记录：已将 `progressApi.listKnowledgePoints()` 改为读取分页响应中的 `items`，并通过 `admin-web` 构建验证。该 browser-use 用例仍需按最新代码重新执行后更新为正式通过记录。

现象：

- 访问 `/progress` 后页面白屏。
- DOM snapshot 为空。
- 浏览器控制台报错：

```text
TypeError: knowledgePoints.filter is not a function
at ProgressPage (admin-web/src/pages/Progress/index.tsx:355)
```

原因定位：

- 前端 `progressApi.listKnowledgePoints()` 声明返回 `KnowledgePoint[]`。
- 实际后端 `/api/progress/knowledge-points` 返回分页结构：

```json
{"items":[],"total":0,"page":1,"page_size":50,"pages":0}
```

- `ProgressPage` 将该对象直接赋给 `knowledgePoints`，随后调用 `knowledgePoints.filter(...)` 导致白屏。

影响：

- 学习复盘页面不可用。
- “记录成绩”按钮和知识点标签页无法测试。

建议修复方向：

- 将 `progressApi.listKnowledgePoints()` 改为读取 `response.data.items`，或后端改为返回数组。
- 前端增加兜底：`setKnowledgePoints(Array.isArray(result) ? result : result.items ?? [])`。

## 未执行用例

以下用例涉及删除本地数据，需用户在动作前单独确认：

- `BU-STU-007` 删除测试学生
- `BU-COURSE-009` 删除课程
- `BU-ASG-007` 删除作业
- `BU-FB-006` 删除反馈
- `BU-PROG-005` 删除成绩
- `BU-RES-007` 删除资料

以下用例需要准备真实上传文件或更多学生端/提交态数据，本次未执行：

- `BU-RES-003` 不支持文件类型拦截
- `BU-RES-004` 上传资料成功
- `BU-RES-005` 分享资料
- `BU-RES-006` 下载资料
- `BU-ASG-005` 批改作业抽屉
- `BU-ASG-006` 保存批改结果
- `BU-FLOW-003` 作业布置 -> 待批改提醒
- `BU-FLOW-004` 课程反馈 -> 反馈复盘完整创建
- `BU-FLOW-005` 资料上传 -> 分享给学生

## 测试执行备注

- 早期若干失败是 browser-use 断言等待过早或按钮可访问名与用例描述不一致造成，已按实际 DOM 重跑并通过。
- 当前真正阻塞功能的是学习复盘白屏问题。
- 本次没有执行删除操作，避免清理用户本地数据。
