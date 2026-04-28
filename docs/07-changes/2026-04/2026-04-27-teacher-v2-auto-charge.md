# 老师端 V2 完成课程自动扣费

> 状态：当前
> 范围：backend、docs
> 更新：2026-04-27
> 日期：2026-04-27
> 类型：实现

## 背景

老师端 V2 的 MVP 验收要求老师完成课程后，系统基于课时单价和课程时长自动扣减学生预收余额。此前后端已有目标集成测试，但以 `strict xfail` 标记，实际状态接口只更新课程状态。

## 变更内容

- `PATCH /api/courses/{id}/status` 在课程状态更新为 `completed` 时生成自动扣费记录。
- 自动扣费金额按 `课程 hourly_rate * duration / 60` 计算；若课程未保存单价，则回退查询科目单价。
- 重复将同一课程标记为 `completed` 不重复生成扣费记录。
- 已完成课程改为 `cancelled` 时，删除对应自动扣费记录，学生账户余额随之回滚。
- 删除已自动扣费课程时，也会删除对应自动扣费记录，避免孤立扣费影响余额。
- 后端集成测试移除自动扣费 `xfail`，新增重复完成幂等、取消回滚和删除回滚断言。

## 影响范围

- 学生账户余额：自动扣费记录参与 `total_charged` 和 `current_balance` 计算。
- 最近扣费记录：自动扣费记录会出现在学生账户 `recent_charges`。
- 课程状态：完成/取消课程仍通过原状态接口完成。

## 验证方式

- `cd backend && pytest tests/test_integration.py::TestTeacherV2AccountCourseFlow -q`
- `cd backend && pytest --collect-only -q`

## 后续注意

- 请假 / 待补课池和课程详情闭环已在后续 `2026-04-27-teacher-v2-main-closure.md` 中收口。
