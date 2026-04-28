# 2026-04-28 学生端 V2 基础承接收口

> 状态：当前
> 范围：学生端、后端
> 更新：2026-04-28
> 类型：产品 | 接口 | 实现 | 测试

## 背景

老师端 V2 主链路已经基本收口，剩余主要缺口是学生/家长端对老师端动作结果的承接。现有学生端已有课程、作业、反馈、资料和学习进度页面，但缺少账户余额与最近扣费的学生端只读入口，也缺少能把关键信息聚合到首屏的新版首页。

## 变更内容

- 新增 `GET /api/billing/my/account`，供学生/家长端只读查看当前余额、累计收款、累计扣费、下一节课扣费风险、最近收款和最近扣费。
- 新增学生端首页，聚合账户余额/余额风险、最近课程、待完成作业和最新反馈。
- 新增学生端账户明细页，从首页余额卡进入，展示最近扣费和最近收款。
- 学生端默认登录入口从课程页调整为首页。
- 修复学生端登录成功后仍跳转旧课程页的问题。
- 补充后端 pytest，覆盖当前登录学生只能查看自己账户数据的主路径。

## 影响范围

- 产品文档：`docs/01-product/teacher-v2/status.md`
- 设计文档：未新增单独原型文件，本轮按 V2 学生端“轻量承接”原则落地。
- 架构文档：无架构变化。
- 后端：`backend/app/routers/billing.py`、`backend/tests/test_billing.py`
- 管理端：无影响。
- 学生端：`student-web/src/App.tsx`、`student-web/src/pages/Home/`、`student-web/src/pages/Account/`、`student-web/src/api/billing.ts`
- 微信小程序：无影响。

## 兼容性与风险

- 是否影响旧数据：否，只读聚合已有 `BillingRecord`、`Course`、`SubjectPrice`。
- 是否影响现有接口：否，新增接口并复用老师端账户聚合逻辑。
- 是否影响多人并行开发：低，改动集中在学生端和收费只读接口。
- 是否需要迁移或回滚方案：不需要迁移；如学生端首页出现问题，可临时将默认入口切回 `/courses`。

## 验证方式

- 命令：`cd backend && pytest tests/test_billing.py -q`
- 结果：17 passed
- 命令：`cd backend && pytest tests/test_billing.py tests/test_courses.py tests/test_teacher_workbench.py -q`
- 结果：44 passed
- 命令：`cd backend && pytest -q`
- 结果：121 passed
- 命令：`cd student-web && npm run build`
- 结果：通过，仍存在既有 Vite CJS Node API deprecation warning
- 命令：`cd admin-web && npm run build`
- 结果：通过，仍存在既有 Vite CJS Node API deprecation warning
- 浏览器：学生端登录、首页、账户明细、课程、作业、反馈、进度、资料
- 结果：通过
- 浏览器：管理端 P0 页面级复核，覆盖工作台、学生、课程、收费与账户、作业、反馈、学习复盘、资料、设置
- 结果：通过

## 关联文档

- 当前事实源：`docs/01-product/teacher-v2/status.md`
- 实施计划：`docs/04-implementation/teacher-v2/plan.md`
- 进度工作流：`docs/08-progress/workstreams/student-web-v2-rework.md`
- 相关 PR / 提交：待提交

## 后续事项

- [x] 发布前使用真实浏览器/移动视口复核学生端登录、首页、账户明细和五个 Tab。
- [x] 浏览器复核通过后，将学生端新版承接 workstream 标记为完成。
