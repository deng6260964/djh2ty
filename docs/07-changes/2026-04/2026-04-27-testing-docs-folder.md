# 测试文档目录归集

> 日期：2026-04-27
> 范围：文档、测试
> 状态：已完成

## 背景

测试相关文档原先分散在 `docs/04-implementation/backend/` 和 `docs/04-implementation/admin-web/browser-use/` 下，缺少统一入口。继续维护测试用例、测试报告和验证记录时，研发需要跨目录检索，容易遗漏。

## 变更内容

- 新增统一测试文档目录：`docs/05-testing/`。
- 新增测试文档入口：`docs/05-testing/README.md`。
- 后端测试报告迁移到：`docs/05-testing/backend/test-report.md`。
- 管理端 browser-use 用例和验证记录迁移到：`docs/05-testing/browser-use/`。
- 同步更新文档地图和文档工作流说明。

## 影响范围

- 测试文档查找入口统一为 `docs/05-testing/README.md`。
- 原测试文档内容未改变，仅调整归属目录和路径引用。
- 后端测试、前端构建和业务代码不受影响。

## 验证方式

- 检查旧路径引用已清理。
- 检查 `docs/04-implementation/doc-map.md` 已登记新测试文档目录。

## 后续注意

新增测试用例、测试报告或验证记录时，应优先放入 `docs/05-testing/`。
