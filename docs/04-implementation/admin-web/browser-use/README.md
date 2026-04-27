# Browser-use 测试用例目录

> 状态：当前
> 范围：管理端
> 更新：2026-04-26
> 说明：老师端 V2 browser-use 集成测试用例和验证记录入口。

本目录存放基于 Codex in-app browser + `browser-use` 技能执行的集成测试用例与验证记录。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `dashboard-workbench.spec.md` | 工作台专项用例，覆盖登录守卫、工作台结构、快速排课、快速操作跳转 |
| `dashboard-workbench.verification.md` | 工作台专项用例的本地 browser-use 验证记录 |
| `full-regression.spec.md` | 老师端 V2 全量回归用例，覆盖认证、工作台、学生、课程、收费、作业、反馈、学习复盘、资料、设置、跨模块闭环、异常态和删除功能专项 |

## 推荐执行策略

1. 先执行 `dashboard-workbench.spec.md` 作为 smoke test。
2. 再按 `full-regression.spec.md` 的 P0/P1/P2/P3/P4 优先级分批执行。
3. 每次执行后新增或更新对应 `*.verification.md`，记录环境、数据、结果和失败截图/DOM 关键断言。
4. 删除类 `BU-DEL-*` 用例仅针对 `BU测试` 数据执行；由 Codex 操作时，最终确认删除前需要用户确认。
