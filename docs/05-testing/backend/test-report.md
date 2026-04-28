# 测试报告

> 状态：参考
> 范围：后端
> 更新：2026-04-28
> 说明：后端测试覆盖快照；当前测试结果以最新本地 `pytest` 运行为准。

## 最近一次执行结果

| 时间 | 命令 | 结果 | 备注 |
| --- | --- | --- | --- |
| 2026-04-28 本轮 | `cd backend && pytest -q` | 121 passed in 45.44s | 新增学生端账户接口回归；出现 `pytest-asyncio` fixture loop scope deprecation warning，不影响本次结果 |
| 2026-04-28 10:03 CST | `cd backend && pytest -q` | 120 passed in 42.50s | 出现 `pytest-asyncio` fixture loop scope deprecation warning，不影响本次结果 |

## 测试环境说明

- **测试框架**：pytest 8.3.3 + pytest-asyncio 0.24.0
- **HTTP 测试客户端**：httpx 0.27.2 (AsyncClient + ASGITransport)
- **测试数据库**：SQLite 内存数据库（aiosqlite 驱动），与 PostgreSQL 开发数据库完全隔离
- **运行命令**：
  ```bash
  cd backend
  conda activate tutoring-assistant
  pip install pytest==8.3.3 pytest-asyncio==0.24.0 aiosqlite==0.20.0
  pytest tests/ -v
  ```

---

## 测试覆盖范围

| 模块 | 测试文件 | 测试用例数 |
|------|---------|-----------|
| 认证（auth） | test_auth.py | 15 |
| 学生管理（students） | test_students.py | 18 |
| 课程管理（courses） | test_courses.py | 23 |
| 作业管理（assignments） | test_assignments.py | 13 |
| 收费管理（billing） | test_billing.py | 17 |
| 资料管理（resources） | test_resources.py | 19 |
| 集成测试 | test_integration.py | 12 |
| 老师端 V2 聚合接口 | test_teacher_workbench.py | 4 |
| **合计** | **8 个文件** | **121 个用例** |

---

## 用户故事验收情况

| 用户故事 ID | 描述 | 验收标准覆盖 | 测试状态 |
|------------|------|-------------|---------|
| US-001 | 老师账号登录 | AC1:正常登录返回Token、AC2:错误密码401、AC3:过期Token跳转 | 已覆盖 |
| US-101 | 添加学生 | AC1:必填字段422、AC2:创建后出现在列表 | 已覆盖 |
| US-102 | 编辑学生信息 | AC2:保存后数据同步更新 | 已覆盖 |
| US-103 | 删除学生 | AC2:软删除保留历史数据、AC3:从列表消失 | 已覆盖 |
| US-104 | 搜索和筛选学生 | AC1:模糊搜索、AC3:无结果显示空列表 | 已覆盖 |
| US-105 | 查看学生详情 | AC1:包含统计数据（课程/作业/收费） | 已覆盖 |
| US-201 | 添加课程 | AC1:必填字段422、AC3:时长计算 | 已覆盖 |
| US-202 | 上课时间冲突检测 | AC1:冲突警告含冲突信息、AC2:三种重叠情况、AC3:边界时间不冲突 | 已覆盖 |
| US-203 | 日历视图查看课程 | AC1:按日期分组返回 | 已覆盖 |
| US-204 | 标记课程状态 | AC1:三种状态切换、AC2:取消课程不参与冲突检测 | 已覆盖 |
| US-205 | 编辑和删除课程 | AC1:编辑时仍触发冲突检测 | 部分覆盖 |
| US-301 | 布置作业 | AC2:多选学生各获独立记录、缺少字段422 | 已覆盖 |
| US-302 | 查看作业完成情况 | AC1:列表含完成率统计 | 已覆盖 |
| US-303 | 批改作业 | AC1:评分0-100、AC3:修改覆盖 | 已覆盖 |
| US-304 | 作业统计 | 分页列表含统计字段 | 部分覆盖 |
| US-501 | 设置科目课时单价 | AC1:新增/修改单价、AC3:单价列表展示 | 已覆盖 |
| US-502 | 自动计算应收费用 | AC1:应收=课时×单价 | 已覆盖（集成测试） |
| US-503 | 记录收款 | AC1:收款字段完整、AC2:欠费实时更新 | 已覆盖 |
| US-504 | 查看收费汇总报表 | AC2:展示应收/已收/未收及学生明细 | 已覆盖 |
| US-505 | 欠费提醒 | AC1:欠费学生有视觉标识（API层验证列表准确性） | 已覆盖 |
| V2-WB | 老师工作台 | 今日课程、待补记录、待收费、待批改聚合及精确断言 | 已覆盖 |
| V2-ACC | 学生预收账户 | 充值、余额、最近收款/扣费、收费提醒解除 | 已覆盖 |
| V2-STUDENT-ACCOUNT | 学生端账户承接 | 学生/家长端只读查看当前余额、下一节课扣费风险、最近收款/扣费 | 已覆盖 |
| V2-AUTO-CHARGE | 完成课程自动扣费 | 完成课程后生成扣费记录并更新余额；重复完成不重复扣费；已扣费课程取消或删除后回滚自动扣费 | 已覆盖 |
| V2-COURSE-DETAIL | 课程详情闭环 | 详情聚合、课后记录、可选作业、保存并完成、自动扣费 | 已覆盖 |
| V2-MAKEUP | 请假与待补课池 | 学生/老师请假转待补课池、安排补课、原课程移出待补池 | 已覆盖 |
| V2-COPY-WEEK | 复制上一周课程 | 预览冲突/收费风险、确认复制、冲突跳过 | 已覆盖 |
| US-701 | 上传教学资料 | AC1:支持类型/50MB限制、AC3:文件类型错误400 | 已覆盖 |
| US-702 | 分类管理资料 | AC1:按科目筛选、AC3:删除后不可访问 | 已覆盖 |
| US-703 | 分享资料给学生 | AC1:多选分享、AC2:分享后可见、AC3:撤销分享后403 | 已覆盖 |

---

## API 接口测试清单

### 认证模块 `/api/auth`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/auth/login | POST | 正常登录、错误密码、不存在用户、禁用用户 | test_auth.py |
| /api/auth/me | GET | 有效Token、无Token、无效Token | test_auth.py |
| /api/auth/refresh | POST | 正常刷新、无Token、过期Token | test_auth.py |

### 学生管理 `/api/students`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/students | GET | 分页列表、按姓名搜索、无结果、按 is_active 筛选 | test_students.py |
| /api/students | POST | 正常创建、缺少必填字段、未认证 | test_students.py |
| /api/students/{id} | GET | 正常详情（含统计）、不存在404 | test_students.py |
| /api/students/{id} | PUT | 正常更新、不存在404 | test_students.py |
| /api/students/{id} | DELETE | 软删除验证、从列表消失、不存在404 | test_students.py |

### 课程管理 `/api/courses`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/courses | GET | 列表分页、按学生过滤 | test_courses.py |
| /api/courses | POST | 正常创建、冲突409、学生不存在404、缺字段422 | test_courses.py |
| /api/courses/check-conflict | POST | 冲突检测（有冲突/无冲突） | test_courses.py |
| /api/courses/calendar | GET | 日历格式验证、缺参数422 | test_courses.py |
| /api/courses/{id}/status | PATCH | completed/cancelled/invalid_status | test_courses.py |
| /api/courses/week | GET | 周视图、周末标识、收费风险 | test_teacher_workbench.py |
| /api/courses/copy-week-preview | POST | 复制周预览、冲突和收费风险 | test_courses.py |
| /api/courses/copy-week-confirm | POST | 选择复制、冲突跳过 | test_courses.py |
| **冲突边界** | - | 完全重叠/部分重叠/包含/边界相邻/完全前置/取消课程不冲突 | test_courses.py |

### 作业管理 `/api/assignments`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/assignments | GET | 分页列表含统计字段 | test_assignments.py |
| /api/assignments | POST | 单生/多生/无学生/不存在学生/缺标题 | test_assignments.py |
| /api/assignments/{id} | GET | 详情含所有学生提交状态 | test_assignments.py |
| /api/assignments/{id}/grade/{sid} | POST | 正常批改、重复批改覆盖、分数越界、不存在作业/学生 | test_assignments.py |

### 收费管理 `/api/billing`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/billing/subject-prices | GET | 获取列表 | test_billing.py |
| /api/billing/subject-prices/{subject} | PUT | 新建单价、修改已有单价 | test_billing.py |
| /api/billing/records | GET | 分页列表 | test_billing.py |
| /api/billing/records | POST | 正常创建、学生不存在404 | test_billing.py |
| /api/billing/records/{id}/pay | PATCH | 全额→paid、部分→partial | test_billing.py |
| /api/billing/records/{id} | DELETE | 正常删除 | test_billing.py |
| /api/billing/recharge | POST | 预收充值增加学生账户余额 | test_billing.py |
| /api/billing/students/{id}/account | GET | 当前余额、下一节课扣费风险、最近收款/扣费 | test_teacher_workbench.py |
| /api/billing/my/account | GET | 当前登录学生只读查看余额、下一节课扣费风险、最近收款/扣费 | test_billing.py |
| /api/billing/summary | GET | 应收/已收/欠费合计、按学生明细 | test_billing.py |
| /api/billing/outstanding | GET | 欠费列表、已付清学生不出现 | test_billing.py |

### 老师工作台 `/api/dashboard`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/dashboard/workbench | GET | 今日课程、待补记录、待收费提醒、待批改作业精确聚合 | test_teacher_workbench.py |

### 资料管理 `/api/resources`

| 接口 | 方法 | 测试场景 | 测试文件 |
|------|------|---------|---------|
| /api/resources | GET | 分页列表、按科目筛选 | test_resources.py |
| /api/resources/upload | POST | PDF成功、PNG成功、>50MB→413、.exe→400、缺title→422、未认证→401 | test_resources.py |
| /api/resources/{id} | GET | 详情含分享学生列表 | test_resources.py |
| /api/resources/{id} | DELETE | 正常删除后404 | test_resources.py |
| /api/resources/{id}/share | POST | 单生/多生分享、幂等性 | test_resources.py |
| /api/resources/{id}/share/{sid} | DELETE | 撤销分享、撤销不存在分享404 | test_resources.py |
| /api/resources/{id}/download | GET | admin可下载、学生下载已分享、403（未分享）、401（未认证） | test_resources.py |

---

## 集成测试场景清单

| 场景 | 测试文件 | 覆盖内容 |
|------|---------|---------|
| 完整排课流程 | test_integration.py::TestCourseWorkflow | 创建学生→排课→冲突→紧邻排课→完成 |
| 日历展示已创建课程 | test_integration.py::TestCourseWorkflow | 日历接口包含新创建的课程 |
| 完整作业流程 | test_integration.py::TestAssignmentWorkflow | 布置→查看pending→批改→查看graded |
| 手工收费记录闭环 | test_integration.py::TestBillingWorkflow | 设单价→创收费→汇总→付款→欠费列表 |
| V2 自动扣费目标闭环 | test_integration.py::TestTeacherV2AccountCourseFlow | 充值→排课→完成→自动扣费→余额更新；重复完成幂等；取消或删除已完成课程回滚自动扣费 |
| V2 课程详情闭环 | test_integration.py::TestTeacherV2AccountCourseFlow | 课程详情聚合→保存课后记录→可选布置作业→完成课程→自动扣费 |
| V2 请假待补闭环 | test_integration.py::TestTeacherV2AccountCourseFlow | 请假→进入待补课池→安排补课→原课程关闭待补状态 |
| 学生详情统计 | test_integration.py::TestStudentDetailWorkflow | 课程数/完成数反映在统计中 |
| 冲突详情内容 | test_integration.py::TestConflictDetectionEdgeCases | 冲突响应包含冲突课程信息 |
| 搜索创建后可见 | test_integration.py::TestSearchAndFilterWorkflow | 创建后立即可通过姓名搜索 |

---

## 测试注意事项

1. **数据库隔离**：测试使用 SQLite 内存数据库，通过 `conftest.py` 中的猴子补丁将 PostgreSQL `ARRAY(String)` 类型替换为 SQLite 兼容的 `JSONEncodedList`，完全不影响开发/生产数据库。

2. **测试独立性**：每个测试函数使用独立的 `db` fixture（通过 `rollback()` 隔离），理论上不互相依赖。但由于 SQLite 内存数据库是 session 级共享的，如果测试间有数据状态依赖，建议在测试中用 `delete` 语句手动清理关联表数据（如 `test_billing.py` 中的做法）。

3. **文件上传测试**：使用 `io.BytesIO` 模拟文件对象，生成 PDF 文件头使其能通过 MIME 检测（实际 MIME 类型由请求携带，`file_handler.py` 以 `content_type` 字段为准，无需真正的 PDF 内容）。

4. **下载测试的特殊性**：文件下载测试在本地 SQLite 环境中，真实文件不存在于磁盘，因此下载接口预期返回 200（文件存在）或 404（文件不在磁盘但权限检查通过）。权限拒绝测试（403）是核心断言。

5. **`ARRAY` 类型兼容**：`Student.subjects` 在 PostgreSQL 中是 `ARRAY(String)`，在测试环境被替换为 JSON 字符串存储。查询时 `Student.subjects.any(subject)` 这类 PostgreSQL 特有的数组操作在 SQLite 中**不可用**，因此 `test_students.py` 未测试按 subject 参数的筛选功能（该功能需在 PostgreSQL 环境下集成测试）。

---

## 已知限制（无法自动化测试的部分）

| 功能 | 原因 | 手动验收要点 |
|------|------|------------|
| 微信登录（/api/auth/wechat） | 需要微信服务器鉴权，无法在 CI 环境模拟 | 在微信开发者工具中使用真实 code 测试，验证 openid 绑定和 Token 颁发 |
| 课前自动提醒推送（通知模块） | 依赖微信订阅消息 API | 在小程序端测试接收通知消息，验证跳转到正确页面 |
| PDF 导出（/api/progress/report） | 前端 jsPDF 渲染，依赖浏览器环境 | 在管理端点击"导出报告"，验证下载文件命名格式和内容完整性 |
| 文件下载实际内容验证 | 测试环境无真实上传目录 | 在开发环境上传真实文件后验证下载内容一致性 |
| 仪表盘数据准确性（/api/dashboard/overview） | 依赖多表聚合，需要真实数据分布 | 手动创建课程/作业/收款后，验证仪表盘数字与手动汇总一致 |
| 小程序端 UI 交互 | 原生微信小程序，无 Web 测试工具支持 | 在微信开发者工具中逐页验证 US-801 ~ US-806 验收标准 |
| 连续失败5次锁定账户 | 系统尚未实现该逻辑（US-001 AC2） | 待实现后补充自动化测试 |
