# 测试文档入口

> 状态：当前
> 范围：全项目
> 更新：2026-04-27

本目录集中存放测试用例、测试报告和验证记录，作为项目测试资产的统一入口。

## 目录结构

| 目录 | 内容 |
| --- | --- |
| `backend/` | 后端 pytest 覆盖报告、API 测试清单和已知限制 |
| `bugfix-records/` | 缺陷修复与测试失败闭环记录 |
| `browser-use/` | 管理端 browser-use 集成测试用例和验证记录 |

## 当前测试文档

| 文档 | 状态 | 说明 |
| --- | --- | --- |
| `testing-workflow.md` | 当前 | 测试流程指南，覆盖用例编写、执行动作、失败处理和文档归集 |
| `backend/test-report.md` | 参考 | 后端自动化测试覆盖快照，真实结果以最新本地 `pytest` 为准 |
| `bugfix-records/2026-05-11-tdd-bugfix-workflow-validation.md` | 当前 | TDD 缺陷修复工作流在当前项目上的试运行记录 |
| `browser-use/README.md` | 当前 | browser-use 用例目录说明 |
| `browser-use/dashboard-workbench.spec.md` | 当前 | 老师工作台专项集成测试用例 |
| `browser-use/dashboard-workbench.verification.md` | 参考 | 工作台专项验证记录 |
| `browser-use/full-regression.spec.md` | 当前 | 老师端 V2 全量回归测试用例 |
| `browser-use/full-regression.verification.md` | 参考 | 全量回归验证记录 |
| `browser-use/student-web-smoke.verification.md` | 参考 | 学生端 V2 浏览器冒烟验证记录 |

## 使用建议

1. 先阅读 `testing-workflow.md`，按影响面决定 pytest、build、browser-use 或人工专项验收。
2. 后端改动优先运行 `cd backend && pytest -q`，并在必要时更新 `backend/test-report.md`。
3. 管理端流程改动优先对照 `browser-use/full-regression.spec.md` 执行相关用例。
4. 每次手动或 browser-use 回归后，更新对应 `*.verification.md`，记录环境、数据、结果和未执行项。
5. 新增测试文档时，同步更新 `docs/04-implementation/doc-map.md`。
