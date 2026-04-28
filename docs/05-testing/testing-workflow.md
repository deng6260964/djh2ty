# 测试流程指南

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

本文沉淀近期老师端 V2 改造中的测试经验，用于指导后续需求、修复、回归和文档归集。目标是让测试不是最后补一笔，而是贯穿“理解需求 -> 编写用例 -> 执行动作 -> 定位问题 -> 更新文档 -> 交接”的完整闭环。

## 1. 测试分层

当前项目按风险和执行方式分为四层测试。

| 层级 | 主要对象 | 首选方式 | 文档位置 |
| --- | --- | --- | --- |
| 后端 API 自动化 | 接口、业务规则、余额/扣费/回滚、鉴权、数据边界 | `pytest` | `docs/05-testing/backend/` |
| 管理端集成回归 | 登录、导航、表单、弹窗、跨模块流程 | Codex in-app browser + browser-use | `docs/05-testing/browser-use/` |
| 人工专项验收 | 文件上传下载、删除、微信、小程序、真实浏览器导出 | 手动执行并记录 | 对应 `*.verification.md` |
| 文档与交接校验 | 测试策略、执行结果、未执行项、变更影响 | 更新当前测试文档、变更记录和状态文档 | `docs/05-testing/`、`docs/07-changes/` |

## 2. 需求开始前

开始非琐碎改动前，先确认测试边界。

1. 阅读当前事实源：
   - `docs/01-product/teacher-v2/status.md`
   - `docs/01-product/current.md`
   - `docs/01-product/teacher-v2/prd.md`
   - `docs/02-design/teacher-v2/prototype.md`
   - `docs/04-implementation/teacher-v2/plan.md`
2. 判断影响端：
   - `backend`
   - `admin-web`
   - `student-web`
   - `miniprogram`
   - 纯文档
3. 判断测试类型：
   - 只改后端规则：优先补 pytest。
   - 只改页面展示：至少跑前端 build，并补 browser-use 用例或执行记录。
   - 改跨模块主链路：pytest + browser-use 回归都要覆盖。
   - 改文档或流程：更新入口文档、文档地图和必要的变更记录。
4. 明确验收标准：
   - 正常路径是什么。
   - 空数据状态是什么。
   - 表单必填、非法值和权限失败是什么。
   - 是否涉及扣费、余额、删除、回滚等高风险动作。

## 3. 用例编写规则

### 3.1 后端 pytest 用例

适合写后端自动化的场景：

- 新增或修改 API 入参、返回值、状态码。
- 修改余额、扣费、充值、回滚、冲突检测、请假/补课等业务规则。
- 修改鉴权、权限、软删除、分页、筛选。
- 修复一个可用 API 稳定复现的 bug。

用例至少覆盖：

- 成功路径：返回状态码、核心字段和数据库状态。
- 失败路径：缺字段、非法值、不存在资源、未认证。
- 边界路径：重复提交、取消后再操作、删除已有关联数据、时间边界。
- 幂等或回滚：例如完成课程不重复扣费，取消或删除已完成课程应回滚自动扣费。

命名建议：

- 测试文件：`backend/tests/test_*.py`
- 测试函数：`test_*`
- 业务闭环可放入现有集成测试类，例如 `TestTeacherV2AccountCourseFlow`

老师端 V2 后端改动优先关注：

- `/api/dashboard/workbench`
- `/api/courses/week`
- `/api/courses/{id}/detail-v2`
- `/api/courses/{id}/complete`
- `/api/courses/{id}/leave`
- `/api/courses/makeup-pool`
- `/api/courses/{id}/makeup`
- `/api/courses/copy-week-preview`
- `/api/courses/copy-week-confirm`
- `/api/billing/students/{id}/account`
- `/api/billing/recharge`

### 3.2 browser-use 用例

适合写 browser-use 的场景：

- 页面结构、导航、弹窗、抽屉、表单校验。
- 需要验证真实前端状态流转。
- 需要串联多个页面确认业务闭环。
- 后端测试已经覆盖规则，但仍需要确认老师端是否能顺利完成操作。

用例格式建议：

```md
### BU-MODULE-001 用例名称

步骤：

1. 访问页面或打开弹窗。
2. 输入或选择测试数据。
3. 点击明确按钮。

预期：

- 页面出现明确文案、状态、表格行或提示。
- 关键业务数据可追踪。
- 弹窗关闭或保持打开的行为符合预期。
```

定位规则：

- 优先使用按钮文本、弹窗标题、输入框 placeholder、表格行业务文本。
- 对重复按钮先确认目标行或当前可见区域。
- 删除、上传、提交类动作执行前确认测试数据范围。
- 对富文本、复杂组件和异步加载，要记录实际 DOM 可断言的内容，不要只写“感觉成功”。

测试数据建议：

- 使用 `BU测试` 前缀，便于筛选和清理。
- 每轮全量回归使用唯一后缀，例如 `BU测试学生-YYYYMMDD-HHMM`。
- 删除类用例只针对 `BU测试` 数据执行。
- 真实上传测试提前准备小体积文件，并记录文件名、类型、大小。

### 3.3 人工专项用例

以下场景可以先不强行自动化，但必须记录未执行原因和后续验收点：

- 删除真实业务数据。
- 文件真实上传、下载、分享和撤销。
- 小程序或微信登录。
- PDF 导出、浏览器下载内容校验。
- 依赖学生端提交态或微信推送的流程。

记录时要写清：

- 为什么未执行。
- 执行需要哪些准备条件。
- 后续执行时的验收标准。
- 是否阻塞当前发布或只是残余风险。

## 4. 执行动作

### 4.1 后端验证

常用命令：

```bash
cd backend
pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q
```

完整后端回归：

```bash
cd backend
pytest -q
```

执行后记录：

- 命令。
- 是否通过。
- 失败用例名称。
- 失败原因和修复结果。
- 是否需要更新 `docs/05-testing/backend/test-report.md`。

### 4.2 管理端构建验证

常用命令：

```bash
cd admin-web
npm run build
```

构建失败时先区分：

- TypeScript 类型错误。
- API 类型与真实返回不一致。
- 未使用变量或导入错误。
- 打包体积警告。

只要代码行为已改动，构建结果应写入交接说明；如果修改了页面主链路，应继续执行 browser-use。

### 4.3 browser-use 回归

推荐顺序：

1. 启动后端和前端。
2. 先执行 `docs/05-testing/browser-use/dashboard-workbench.spec.md` 作为 smoke test。
3. 再按 `docs/05-testing/browser-use/full-regression.spec.md` 执行：
   - P0：登录、工作台、课程完成、自动扣费、收费提醒、学生账户。
   - P1：课程复制、请假/补课、调课、取消/删除回滚。
   - P2：作业、反馈、学习复盘、资料、设置。
   - P3：空状态、表单校验、筛选搜索。
   - P4：删除、真实上传下载、跨端专项。
4. 每个失败先判断是产品缺陷、测试数据问题、定位问题，还是异步等待问题。
5. 修复后只重跑相关失败用例，再视风险补跑相邻链路。

执行记录必须包含：

- 前端和后端地址。
- 登录账号。
- 测试数据。
- 结果汇总。
- 已通过用例。
- 失败用例。
- 未执行用例。
- 失败截图、控制台报错或 DOM 关键断言。

### 4.4 高风险动作确认

以下动作执行前需要特别确认测试范围：

- 删除学生、课程、作业、反馈、成绩、资料。
- 真实上传文件。
- 批量复制课程。
- 会改变余额的充值、完成课程、取消已完成课程、删除已完成课程。
- 可能影响现有本地数据的清理脚本。

默认策略：

- 自动化和 browser-use 优先使用隔离测试数据。
- 破坏性 browser-use 用例只操作 `BU测试` 前缀数据。
- 如果要操作非测试数据，必须先单独确认。

## 5. 失败处理流程

失败不要直接改代码，先做最小定位。

1. 记录失败现象：
   - URL。
   - 操作步骤。
   - 页面文案或空白状态。
   - 控制台报错。
   - API 响应。
2. 判断失败类型：
   - 用例过期：页面真实设计已变，但文档未更新。
   - 数据不足：没有满足前置条件的数据。
   - 前端缺陷：白屏、类型错误、状态未刷新、按钮不可用。
   - 后端缺陷：状态码、返回结构或业务规则不符合预期。
   - 测试工具问题：等待过早、定位到错误按钮、DOM 名称与用例描述不一致。
3. 找到最小复现：
   - 后端问题优先用 pytest 或 API 请求复现。
   - 前端问题优先定位到具体页面、接口返回和状态更新。
4. 修复后补用例：
   - bug 能用 API 复现，补 pytest。
   - bug 只在页面交互暴露，补 browser-use 用例或验证步骤。
5. 更新验证记录：
   - 写明原失败、修复方式、重跑结果和残余风险。

## 6. 文档归集

### 6.1 测试文档归属

| 内容 | 放置位置 |
| --- | --- |
| 测试流程、策略、索引 | `docs/05-testing/README.md`、`docs/05-testing/testing-workflow.md` |
| 后端覆盖报告 | `docs/05-testing/backend/test-report.md` |
| 管理端测试用例 | `docs/05-testing/browser-use/*.spec.md` |
| 管理端执行记录 | `docs/05-testing/browser-use/*.verification.md` |
| 重要测试文档新增/变更 | `docs/07-changes/YYYY-MM/YYYY-MM-DD-*.md` |
| AI 会话中的可复用测试经验 | `docs/06-ai-worklogs/`，仅当不适合放入正式测试文档时使用 |

### 6.2 什么时候更新文档

需要更新测试文档的情况：

- 新增或调整用例。
- 重新执行回归。
- 发现失败并定位原因。
- 修复失败后重跑。
- 测试环境、测试数据或执行方式发生变化。
- 旧验证记录已经不代表当前实现。

需要更新其他文档的情况：

- 当前状态或下一步变化：更新 `docs/01-product/teacher-v2/status.md`。
- 实施阶段推进：更新 `docs/04-implementation/teacher-v2/plan.md`。
- 新增长期 Markdown 文档：更新 `docs/04-implementation/doc-map.md`。
- 形成重要测试流程或目录变更：新增 `docs/07-changes/` 记录。

### 6.3 验证记录模板

```md
# 用例名称验证记录

> 状态：参考
> 范围：管理端
> 更新：YYYY-MM-DD
> 验证时间：YYYY-MM-DD
> 验证目标：docs/05-testing/browser-use/xxx.spec.md
> 验证方式：Codex in-app browser + browser-use

## 环境

- 前端：
- 后端：
- 登录账号：

## 测试数据

- 学生：
- 课程：
- 充值：
- 文件：

## 结果汇总

| 分类 | 结果 |
| --- | --- |
| 认证与路由守卫 | 通过/失败/未执行 |

## 已通过用例

- `BU-XXX-001` 说明

## 失败用例

### `BU-XXX-002` 用例名称

- 现象：
- 原因：
- 影响：
- 修复或建议：
- 重跑结果：

## 未执行用例

- `BU-XXX-003`：原因和后续条件

## 测试执行备注

- 异步等待、定位差异、测试数据污染、残余风险等。
```

## 7. 交接清单

一次测试或开发结束前，至少回答：

- 后端相关 pytest 是否执行，结果是什么。
- 管理端是否执行 `npm run build`，结果是什么。
- 是否需要 browser-use smoke 或全量回归。
- 新增或修改了哪些用例。
- 哪些用例失败，是否已修复和重跑。
- 哪些用例未执行，为什么。
- 是否影响余额、扣费、删除、上传等高风险数据。
- 是否更新 `docs/05-testing/`。
- 是否需要更新 `docs/01-product/teacher-v2/status.md` 或 `docs/04-implementation/teacher-v2/plan.md`。
- 是否需要新增 `docs/07-changes/`。

推荐最终交接格式：

```text
改动范围：
验证命令：
browser-use：
测试数据：
失败/未执行：
文档更新：
后续事项：
```

## 8. 当前建议

结合当前老师端 V2 状态，近期优先级建议为：

1. 按最新代码重新执行 `docs/05-testing/browser-use/full-regression.spec.md`，重点确认学习复盘白屏修复后的结果。
2. 将全量回归结果刷新到 `docs/05-testing/browser-use/full-regression.verification.md`，把旧失败记录改为最新事实。
3. 对自动扣费、取消回滚、删除回滚、请假补课、复制上一周继续保持后端 pytest 覆盖。
4. 对上传下载、删除和学生端联动建立专项验证记录，避免长期停留在“未执行但不知道怎么补”的状态。
