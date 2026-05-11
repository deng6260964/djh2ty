# TDD 缺陷修复工作流验证记录

> 状态：closed
> 范围：后端、测试、通用 skill 试运行
> 更新：2026-05-11

## 批次总览

- 输入来源：当前项目推荐测试命令与 `tdd-bugfix-workflow` 试运行。
- 输入总数：2。
- 已关闭：2。
- 阻塞：0。
- needs-info：0。
- 高风险缺陷：0。
- 串行/并行策略：串行处理。先运行测试发现失败，再完成根因定位、最小修复和回归验证。
- 最终结论：本轮发现并修复 2 个时间敏感测试缺陷；未发现当前验证范围内的产品代码失败。`tdd-bugfix-workflow` 能支撑自动化缺陷闭环，但在项目落地时需要把“测试缺陷”和“产品缺陷”明确区分。

## 自动化安全预检

- execution_env：local。
- environment_verified_by：后端 pytest 使用 `sqlite+aiosqlite:///:memory:?cache=shared` 测试库；前端执行本地 build。
- target_url_or_service：无真实 URL；HTTP 测试使用 `http://test` ASGI transport。
- credential_source（脱敏）：测试 fixture 内置账号。
- operation_class：local-write。
- data_scope：fixture。
- external_systems_touched：无。
- dry_run_available / dry_run_used：不适用。
- rollback_or_cleanup_plan：测试 fixture 清理内存库；代码改动仅限测试文件和文档。
- stop_or_degrade_decision：继续自动化执行。
- stop_reason：无。
- residual_safety_risk：无真实外部副作用；保留 pytest-asyncio 配置弃用告警作为后续维护风险。

## 缺陷归一化

| bug_id | source_ref | title | defect_type | severity | risk_flags | status | closure_decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-20260511-001 | EV-001-command-red | 学生账户测试使用固定日期导致“下节课”断言随时间失效 | test-bug | medium | test-flaky, time-dependent | closed | closed |
| BUG-20260511-002 | EV-008-fixed-date-scan | 老师端集成测试中的未来课程/作业日期会在 2026-05 后自然过期 | test-bug | medium | test-flaky, time-dependent | closed | closed |

## 复现与根因

复现命令 `pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q` 失败于 `tests/test_billing.py::TestBillingRecords::test_my_account_returns_current_student_balance`。

失败现象：接口返回余额、充值、扣费统计均正确，但 `next_course_id` 为 `None`，测试期望为新建课程 ID。

根因：测试数据把“下节课”固定为 `2026-05-06 10:00`。本次执行日期为 `2026-05-11`，该课程已经早于业务代码中的 `Course.start_time > datetime.now()` 条件。业务逻辑按“未来 scheduled 课程”查询下一节课，返回 `None` 是合理行为；缺陷属于测试数据时间敏感，而不是接口逻辑错误。

## 修复摘要

BUG-20260511-001：

- 修改 `backend/tests/test_billing.py`。
- 将固定课程时间改为 `datetime.now() + timedelta(days=1)`。
- `end_time` 改为基于 `start_time + timedelta(minutes=90)`。
- 保持业务断言不变：余额 150、下节课预计扣费 225、需要收费提醒、最近充值/扣费记录各 1 条。

BUG-20260511-002：

- 修改 `backend/tests/test_integration.py`。
- 将课程详情闭环中的 `2026-05-12` 课程时间和 `2026-05-14` 作业截止日期改为基于当前时间的相对日期。
- 将请假补课闭环中的 `2026-05-13` 原课程和 `2026-05-15` 补课时间改为相对未来日期。
- 保留 2026-03/2026-04 固定周、冲突检测、复制上一周和日历样本日期，因为这些用例依赖固定周语义，不属于自然过期风险。

## 证据索引

| evidence_id | 阶段 | bug_id | 类型 | 路径/命令/链接 | 环境/版本 | 采集时间 | 退出码/结论 | 关键摘要 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EV-001-command-red | reproduce | BUG-20260511-001 | command | `pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:10 CST | 1 | `1 failed, 43 passed`；`next_course_id` 实际 `None`，期望 `course.id` |
| EV-002-root-cause | diagnose | BUG-20260511-001 | diff/manual | `backend/tests/test_billing.py` 与 `backend/app/routers/billing.py` | local | 2026-05-11 17:12 CST | 结论 | 测试课程固定为 `2026-05-06`，不满足 `Course.start_time > datetime.now()` |
| EV-003-command-green-single | regression | BUG-20260511-001 | command | `pytest tests/test_billing.py::TestBillingRecords::test_my_account_returns_current_student_balance -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:12 CST | 0 | `1 passed in 0.64s` |
| EV-004-command-green-targeted | regression | BUG-20260511-001 | command | `pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:12 CST | 0 | `44 passed in 16.95s` |
| EV-005-command-green-full-backend | regression | BUG-20260511-001 | command | `pytest -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:13 CST | 0 | `121 passed in 41.39s` |
| EV-006-command-admin-build | regression | BUG-20260511-001 | command | `npm run build`，cwd=`admin-web` | local | 2026-05-11 17:10 CST | 0 | 管理端构建通过；仅有 Vite CJS Node API 弃用提示 |
| EV-007-command-student-build | regression | BUG-20260511-001 | command | `npm run build`，cwd=`student-web` | local | 2026-05-11 17:10 CST | 0 | 学生端构建通过；仅有 Vite CJS Node API 弃用提示 |
| EV-008-fixed-date-scan | diagnose | BUG-20260511-002 | command/manual | `rg -n "datetime\\(2026\\|date\\(2026\\|2026-05\\|2026, 5\\|2026-04\\|2026-03" backend/tests` | local | 2026-05-11 17:23 CST | 结论 | 识别出 `test_integration.py` 中未来语义固定日期；固定周业务样本保留 |
| EV-009-command-green-v2-flow | regression | BUG-20260511-002 | command | `pytest tests/test_integration.py::TestTeacherV2AccountCourseFlow -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:27 CST | 0 | `5 passed in 2.46s` |
| EV-010-command-green-full-backend-after-latent-fix | regression | BUG-20260511-002 | command | `pytest -q`，cwd=`backend` | local / SQLite test DB | 2026-05-11 17:28 CST | 0 | `121 passed in 47.06s` |

## 验证覆盖矩阵

| bug_id | 原始路径验证 | 失败测试/等价证据 | 根因回归 | 相邻路径 | 高风险专项 | 结果 | 证据 ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-20260511-001 | 学生端账户接口 `/api/billing/my/account` | 有 | 有 | 后端核心老师端套件、完整后端 pytest、两端前端 build | 不适用，未触碰扣费逻辑 | 通过 | EV-001, EV-003, EV-004, EV-005, EV-006, EV-007 |
| BUG-20260511-002 | 课程详情闭环、请假补课闭环 | 诊断证据 | 有 | 老师端 V2 集成流、完整后端 pytest | 不适用，未触碰业务逻辑 | 通过 | EV-008, EV-009, EV-010 |

## 改动与测试完整性审计

- git status --short：`M backend/tests/test_billing.py`、`M backend/tests/test_integration.py`，新增本记录，更新测试入口与文档地图。
- 计划内改动：修复时间敏感测试；记录本次 skill 验证结果。
- 无计划改动：无。
- 测试/mock/fixture/snapshot 变化：只调整测试用例中的时间数据；未新增 mock、fixture 或 snapshot。
- 测试完整性结论：通过。没有 `.skip`、弱化断言、删除覆盖或只改 fixture 绕过业务问题。业务断言保持原样。

## Skill 试运行评审

通过项：

- 能引导先复现再修复，避免把 `next_course_id=None` 误判为业务代码缺陷。
- 根因门禁有效：修复前先检查业务查询条件和测试数据时间。
- 自动化安全门禁适配当前本地测试场景，没有中断用户确认。
- 证据 ID 和最终记录要求能沉淀完整过程，便于事后审计。

暴露的落地建议：

- 项目使用该 skill 时，应在缺陷类型里显式区分 `product-bug`、`test-bug`、`environment-bug`、`documentation-bug`。
- 时间相关测试建议沉淀项目约定：优先使用相对时间或可注入时钟，避免固定“未来日期”自然过期。
- 后续如果执行 browser-use 回归，应沿用本记录格式补充截图、DOM、控制台和接口响应证据。

## 后续建议

- 固定日期扫描已处理未来语义样本；仍保留 2026-03/2026-04 固定周测试作为业务稳定样本。
- 可考虑在 pytest 配置中显式设置 `asyncio_default_fixture_loop_scope`，消除 pytest-asyncio 弃用告警。
