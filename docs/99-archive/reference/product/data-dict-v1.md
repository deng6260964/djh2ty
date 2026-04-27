# 家教辅助系统 - 数据字典

> 状态：归档
> 范围：全项目
> 更新：2026-04-26
> 版本：1.0
> 日期：2026-02-27
> 说明：列出系统核心实体、字段定义及实体关系；当前真实模型以 `backend/app/models/` 为准。

---

## 目录

1. [实体关系概览](#1-实体关系概览)
2. [实体：用户（users）](#2-实体用户users)
3. [实体：学生（students）](#3-实体学生students)
4. [实体：课程（courses）](#4-实体课程courses)
5. [实体：作业（assignments）](#5-实体作业assignments)
6. [实体：作业提交记录（assignment_submissions）](#6-实体作业提交记录assignment_submissions)
7. [实体：课堂反馈（feedback）](#7-实体课堂反馈feedback)
8. [实体：反馈模板（feedback_templates）](#8-实体反馈模板feedback_templates)
9. [实体：成绩记录（grades）](#9-实体成绩记录grades)
10. [实体：知识点（knowledge_points）](#10-实体知识点knowledge_points)
11. [实体：学生知识点掌握（student_knowledge_points）](#11-实体学生知识点掌握student_knowledge_points)
12. [实体：收费科目配置（billing_subjects）](#12-实体收费科目配置billing_subjects)
13. [实体：收款记录（billing_records）](#13-实体收款记录billing_records)
14. [实体：资料（resources）](#14-实体资料resources)
15. [实体：资料分享（resource_shares）](#15-实体资料分享resource_shares)
16. [实体：通知（notifications）](#16-实体通知notifications)
17. [枚举值定义](#17-枚举值定义)

---

## 1. 实体关系概览

```
users (老师账号)
  │
  ├── 管理 → students (学生)
  │             │
  │             ├── 关联 → courses (课程)  ←── 关联 → feedback (课堂反馈)
  │             │
  │             ├── 关联 → assignment_submissions (作业提交)
  │             │                  │
  │             │                  └── 属于 → assignments (作业)
  │             │
  │             ├── 关联 → grades (成绩记录)
  │             │
  │             ├── 关联 → student_knowledge_points (知识点掌握)
  │             │                  │
  │             │                  └── 属于 → knowledge_points (知识点)
  │             │
  │             ├── 关联 → billing_records (收款记录)
  │             │
  │             └── 关联 → resource_shares (资料分享)
  │                              │
  │                              └── 属于 → resources (资料文件)
  │
  ├── 管理 → feedback_templates (反馈模板)
  ├── 管理 → billing_subjects (科目单价配置)
  └── 发送 → notifications (通知)
```

**关系说明：**

| 关系 | 说明 |
|------|------|
| users → students | 一对多（一名老师管理多名学生） |
| students → courses | 一对多（一名学生有多节课程记录） |
| courses → feedback | 一对一（每节课可有一条课堂反馈） |
| assignments → assignment_submissions | 一对多（一份作业对应多个学生的提交记录） |
| students → assignment_submissions | 一对多（一名学生有多条提交记录） |
| students → grades | 一对多（一名学生有多条成绩记录） |
| knowledge_points → student_knowledge_points | 一对多 |
| students → student_knowledge_points | 一对多 |
| resources → resource_shares | 一对多（一份资料可分享给多个学生） |
| students → resource_shares | 一对多（一名学生可收到多份资料） |

---

## 2. 实体：用户（users）

**说明：** 系统账号表，当前为单老师模式，预留多老师扩展字段。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| username | VARCHAR(50) | 登录用户名 | 是 | UNIQUE，不可重复 |
| password_hash | VARCHAR(255) | bcrypt 加密后的密码 | 是 | 不存储明文密码 |
| display_name | VARCHAR(100) | 显示名称（如"张老师"） | 否 | 用于界面展示 |
| role | VARCHAR(20) | 角色：admin / student / parent | 是 | 默认 admin |
| wechat_openid | VARCHAR(100) | 微信 OpenID（小程序登录用） | 否 | UNIQUE，学生/家长微信绑定 |
| phone | VARCHAR(20) | 手机号 | 否 | 用于通知 |
| is_active | BOOLEAN | 账号是否启用 | 是 | 默认 true |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 3. 实体：学生（students）

**说明：** 学生基本信息档案，由老师创建和维护。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| name | VARCHAR(50) | 学生姓名 | 是 | |
| grade | VARCHAR(50) | 年级（如"初二"、"高三"） | 是 | |
| subjects | VARCHAR(200) | 辅导科目（逗号分隔，如"数学,英语"） | 是 | 多科目支持 |
| parent_phone | VARCHAR(20) | 家长手机号 | 是 | 11位数字，用于联系和推送 |
| parent_name | VARCHAR(50) | 家长姓名 | 否 | |
| school | VARCHAR(100) | 就读学校 | 否 | |
| notes | TEXT | 备注（性格特点、学习弱点等） | 否 | |
| wechat_openid | VARCHAR(100) | 学生微信 OpenID | 否 | 绑定小程序登录 |
| parent_openid | VARCHAR(100) | 家长微信 OpenID | 否 | 绑定小程序登录 |
| is_deleted | BOOLEAN | 软删除标志 | 是 | 默认 false |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 4. 实体：课程（courses）

**说明：** 每一节已安排或已完成的课程记录。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| subject | VARCHAR(50) | 上课科目 | 是 | 如"数学"、"英语" |
| start_time | TIMESTAMP | 上课开始时间（日期+时间） | 是 | 冲突检测基准字段 |
| end_time | TIMESTAMP | 上课结束时间 | 是 | 由 start_time + duration 计算 |
| duration | DECIMAL(4,1) | 课时时长（小时） | 是 | 精确到 0.5 小时，如 1.5 |
| status | VARCHAR(20) | 课程状态 | 是 | 枚举：pending / completed / cancelled |
| notes | TEXT | 备注 | 否 | 老师对本节课的备注 |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

**冲突检测规则：** 新课程的时间段 [start_time, end_time) 与已有"pending"或"completed"状态课程的时间段存在重叠，则视为冲突。

---

## 5. 实体：作业（assignments）

**说明：** 老师发布的作业主体信息，一条记录对应一次作业布置（可关联多个学生）。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| title | VARCHAR(200) | 作业标题 | 是 | |
| content | TEXT | 作业内容（富文本 HTML） | 是 | 支持富文本格式 |
| due_date | DATE | 截止日期 | 是 | |
| subject | VARCHAR(50) | 作业科目 | 是 | |
| created_at | TIMESTAMP | 布置时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 6. 实体：作业提交记录（assignment_submissions）

**说明：** 每个学生针对一份作业的独立记录，包含提交内容和批改结果。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| assignment_id | INTEGER | 关联作业 ID | 是 | FOREIGN KEY → assignments.id |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| status | VARCHAR(20) | 提交状态 | 是 | 枚举：pending / submitted / graded |
| submitted_content | TEXT | 学生提交内容（富文本，小程序端提交时使用） | 否 | |
| submitted_at | TIMESTAMP | 提交时间 | 否 | 学生提交后自动填充 |
| score | INTEGER | 老师评分（0-100） | 否 | NULL 表示未批改 |
| comment | TEXT | 老师评语（富文本） | 否 | |
| graded_at | TIMESTAMP | 批改时间 | 否 | 老师批改后自动填充 |
| created_at | TIMESTAMP | 记录创建时间 | 是 | 作业布置时即创建 |

**唯一约束：** (assignment_id, student_id) 组合唯一。

---

## 7. 实体：课堂反馈（feedback）

**说明：** 老师每节课后填写的课堂反馈记录，与课程一一关联。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| course_id | INTEGER | 关联课程 ID | 是 | FOREIGN KEY → courses.id，UNIQUE |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id，冗余字段，方便查询 |
| performance | TEXT | 本节课表现（富文本） | 否 | |
| knowledge_mastery | TEXT | 知识点掌握情况（富文本） | 否 | |
| issues | TEXT | 存在的问题（富文本） | 否 | |
| next_plan | TEXT | 下节课计划（富文本） | 否 | |
| is_pushed | BOOLEAN | 是否已推送给家长/学生 | 是 | 默认 false |
| pushed_at | TIMESTAMP | 推送时间 | 否 | |
| push_targets | VARCHAR(50) | 推送对象 | 否 | 枚举：student / parent / both |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 8. 实体：反馈模板（feedback_templates）

**说明：** 老师预设的课堂反馈模板，用于快速填写重复性内容。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| title | VARCHAR(100) | 模板名称 | 是 | 如"优秀课堂模板"、"基础薄弱模板" |
| performance | TEXT | 预设表现内容 | 否 | |
| knowledge_mastery | TEXT | 预设知识点掌握内容 | 否 | |
| issues | TEXT | 预设问题描述内容 | 否 | |
| next_plan | TEXT | 预设下节课计划内容 | 否 | |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 9. 实体：成绩记录（grades）

**说明：** 记录学生每次课后测验或正式考试的成绩。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| subject | VARCHAR(50) | 科目 | 是 | |
| exam_name | VARCHAR(200) | 考试/测验名称 | 否 | 如"第3次月考"、"期中考试" |
| exam_date | DATE | 考试日期 | 是 | |
| score | DECIMAL(6,2) | 实际得分 | 是 | |
| full_score | DECIMAL(6,2) | 满分 | 是 | 默认 100 |
| score_percentage | DECIMAL(5,2) | 得分率（score/full_score*100） | 否 | 计算字段，便于跨满分比较 |
| notes | TEXT | 备注 | 否 | |
| created_at | TIMESTAMP | 记录创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 10. 实体：知识点（knowledge_points）

**说明：** 知识点库，按科目分类，由老师维护。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| subject | VARCHAR(50) | 所属科目 | 是 | |
| category | VARCHAR(100) | 知识点大类（如"代数"、"几何"） | 否 | 用于分组展示 |
| name | VARCHAR(200) | 知识点名称 | 是 | 如"一元二次方程求解" |
| description | TEXT | 详细说明 | 否 | |
| sort_order | INTEGER | 排序权重 | 否 | 默认 0，越小越靠前 |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |

---

## 11. 实体：学生知识点掌握（student_knowledge_points）

**说明：** 记录每名学生对每个知识点的掌握状态，多对多关联中间表（含附加字段）。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| knowledge_point_id | INTEGER | 关联知识点 ID | 是 | FOREIGN KEY → knowledge_points.id |
| status | VARCHAR(20) | 掌握状态 | 是 | 枚举：not_started / learning / mastered |
| notes | TEXT | 针对该学生该知识点的备注 | 否 | |
| updated_at | TIMESTAMP | 状态最后更新时间 | 是 | 自动更新 |

**唯一约束：** (student_id, knowledge_point_id) 组合唯一。

---

## 12. 实体：收费科目配置（billing_subjects）

**说明：** 老师设置的各科目课时单价，用于自动计算应收费用。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| subject | VARCHAR(50) | 科目名称 | 是 | UNIQUE，每科目只有一个单价 |
| price_per_hour | DECIMAL(10,2) | 课时单价（元/小时） | 是 | 精确到分，如 150.00 |
| effective_date | DATE | 单价生效日期 | 是 | 用于历史价格追溯 |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

---

## 13. 实体：收款记录（billing_records）

**说明：** 老师每次向学生/家长收款的记录，每条对应一次实际收款行为。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| amount | DECIMAL(10,2) | 实际收款金额（元） | 是 | 精确到分 |
| payment_date | DATE | 收款日期 | 是 | |
| payment_method | VARCHAR(20) | 支付方式 | 是 | 枚举：cash / wechat / alipay / bank_transfer |
| notes | TEXT | 备注（如"11月课时费"） | 否 | |
| is_deleted | BOOLEAN | 软删除标志 | 是 | 默认 false |
| created_at | TIMESTAMP | 记录创建时间 | 是 | 自动填充 |
| updated_at | TIMESTAMP | 最后更新时间 | 是 | 自动更新 |

**欠费计算逻辑：**
- 应收金额 = SUM(已完成课程的 duration × 对应科目 price_per_hour)
- 已收金额 = SUM(该学生所有 billing_records.amount，is_deleted=false)
- 欠费金额 = 应收金额 - 已收金额

---

## 14. 实体：资料（resources）

**说明：** 老师上传的教学资料文件信息。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| name | VARCHAR(200) | 资料名称（显示用） | 是 | |
| file_name | VARCHAR(255) | 原始文件名 | 是 | 含扩展名 |
| file_path | VARCHAR(500) | 服务器存储路径 | 是 | 相对于 uploads 根目录 |
| file_size | INTEGER | 文件大小（字节） | 是 | |
| file_type | VARCHAR(50) | 文件类型 | 是 | 枚举：pdf / doc / docx / image / excel / other |
| mime_type | VARCHAR(100) | MIME 类型 | 是 | 如 application/pdf |
| subject | VARCHAR(50) | 所属科目 | 否 | |
| grade | VARCHAR(50) | 适用年级 | 否 | |
| category | VARCHAR(50) | 资料类型 | 否 | 枚举：lecture / exam / reference / other |
| description | TEXT | 资料说明 | 否 | |
| is_deleted | BOOLEAN | 软删除标志 | 是 | 默认 false |
| created_at | TIMESTAMP | 上传时间 | 是 | 自动填充 |

---

## 15. 实体：资料分享（resource_shares）

**说明：** 记录老师将哪份资料分享给了哪个学生，多对多关联中间表。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| resource_id | INTEGER | 关联资料 ID | 是 | FOREIGN KEY → resources.id |
| student_id | INTEGER | 关联学生 ID | 是 | FOREIGN KEY → students.id |
| is_active | BOOLEAN | 分享是否有效（撤销时置为 false） | 是 | 默认 true |
| shared_at | TIMESTAMP | 分享时间 | 是 | 自动填充 |
| revoked_at | TIMESTAMP | 撤销时间 | 否 | 撤销时填充 |

**唯一约束：** (resource_id, student_id) 组合唯一。

---

## 16. 实体：通知（notifications）

**说明：** 系统发出的所有通知记录，包括课程提醒、作业提醒、欠费提醒等。

| 字段名 | 类型 | 说明 | 必填 | 约束/备注 |
|--------|------|------|------|-----------|
| id | INTEGER | 主键，自增 | 是 | PRIMARY KEY |
| student_id | INTEGER | 目标学生 ID | 是 | FOREIGN KEY → students.id |
| type | VARCHAR(50) | 通知类型 | 是 | 枚举：course_reminder / assignment_reminder / feedback_push / overdue_fee / custom |
| title | VARCHAR(200) | 通知标题 | 是 | |
| content | TEXT | 通知内容 | 是 | |
| target | VARCHAR(20) | 推送目标 | 是 | 枚举：student / parent / both |
| channel | VARCHAR(20) | 推送渠道 | 是 | 枚举：wechat / system |
| send_status | VARCHAR(20) | 发送状态 | 是 | 枚举：pending / sent / failed |
| send_at | TIMESTAMP | 实际发送时间 | 否 | 发送成功后填充 |
| scheduled_at | TIMESTAMP | 计划发送时间 | 否 | 定时通知使用 |
| related_id | INTEGER | 关联业务对象 ID | 否 | 如 course_id、assignment_id |
| related_type | VARCHAR(50) | 关联业务对象类型 | 否 | 如 course、assignment |
| created_at | TIMESTAMP | 创建时间 | 是 | 自动填充 |

---

## 17. 枚举值定义

### 课程状态（courses.status）

| 值 | 中文含义 | 说明 |
|----|---------|------|
| pending | 待上课 | 课程已安排，尚未开始 |
| completed | 已完成 | 课程已正常结束，纳入计费 |
| cancelled | 已取消 | 课程已取消，不纳入计费 |

### 作业提交状态（assignment_submissions.status）

| 值 | 中文含义 | 说明 |
|----|---------|------|
| pending | 待提交 | 作业已布置，学生未提交 |
| submitted | 已提交 | 学生已提交，老师未批改 |
| graded | 已批改 | 老师已完成批改评分 |

### 知识点掌握状态（student_knowledge_points.status）

| 值 | 中文含义 | 显示颜色建议 |
|----|---------|-------------|
| not_started | 待学习 | 灰色 |
| learning | 学习中 | 黄色 |
| mastered | 已掌握 | 绿色 |

### 支付方式（billing_records.payment_method）

| 值 | 中文含义 |
|----|---------|
| cash | 现金 |
| wechat | 微信支付 |
| alipay | 支付宝 |
| bank_transfer | 银行转账 |

### 资料类型（resources.category）

| 值 | 中文含义 |
|----|---------|
| lecture | 讲义 |
| exam | 试题/试卷 |
| reference | 参考资料 |
| other | 其他 |

### 通知类型（notifications.type）

| 值 | 中文含义 |
|----|---------|
| course_reminder | 课程提醒 |
| assignment_reminder | 作业截止提醒 |
| feedback_push | 课堂反馈推送 |
| overdue_fee | 欠费提醒 |
| custom | 自定义通知 |

### 用户角色（users.role）

| 值 | 中文含义 | 说明 |
|----|---------|------|
| admin | 管理员（老师）| 全部权限 |
| student | 学生 | 只读小程序端自己数据 |
| parent | 家长 | 只读小程序端子女数据 |

---

*文档结束*
