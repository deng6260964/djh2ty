# API 接口设计文档

> 状态：归档
> 范围：后端
> 更新：2026-04-26
> 说明：接口风格和历史 API 设计归档参考；当前真实接口以 `backend/app/routers/` 和测试为准，V2 老师端接口优先参考当前 V2 文档。

## 1. API 设计风格

### 基本规范

- **风格**：RESTful API
- **Base URL**：`https://your-domain.com/api`
- **协议**：HTTPS only（HTTP 重定向到 HTTPS）
- **数据格式**：JSON（`Content-Type: application/json`）
- **字符编码**：UTF-8
- **API 版本**：当前版本无版本前缀，未来扩展时加 `/v2` 前缀

### URL 命名规则

```
GET    /api/{资源}          列表查询
POST   /api/{资源}          创建
GET    /api/{资源}/{id}     详情查询
PUT    /api/{资源}/{id}     全量更新
PATCH  /api/{资源}/{id}     部分更新
DELETE /api/{资源}/{id}     删除

# 嵌套资源
GET    /api/students/{id}/courses     某学生的课程列表
GET    /api/assignments/{id}/students 某作业的学生完成情况

# 动作型接口
POST   /api/courses/{id}/complete     标记课程完成
POST   /api/assignments/{id}/grade    批改作业
POST   /api/feedback/{id}/push        推送反馈
```

### 分页规范

所有列表接口统一使用以下参数：

```
GET /api/students?page=1&page_size=20&search=张三&subject=数学

# 响应格式
{
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
}
```

---

## 2. 认证方案

### 2.1 认证方式：Bearer Token（JWT）

所有需要登录的接口，在请求头中携带 JWT Token：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.2 JWT Payload 结构

```json
{
    "sub": "1",            // user_id（字符串）
    "role": "admin",       // 角色：admin | student | parent
    "openid": null,        // 微信 openid（微信登录用户）
    "exp": 1735689600,     // 过期时间（Unix 时间戳）
    "iat": 1735084800      // 签发时间
}
```

### 2.3 无需认证的接口

```
POST /api/auth/login          管理端登录
POST /api/auth/wechat         小程序微信登录
GET  /api/health              健康检查
```

### 2.4 Token 刷新

- 响应头中返回 `X-Token-Remaining-Days` 字段
- 前端检测剩余 < 1 天时调用 `POST /api/auth/refresh` 续期

---

## 3. 错误码规范

### HTTP 状态码使用

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 | OK | 请求成功（GET / PUT / PATCH） |
| 201 | Created | 创建成功（POST） |
| 204 | No Content | 删除成功（DELETE） |
| 400 | Bad Request | 请求参数错误、业务规则违反 |
| 401 | Unauthorized | 未登录或 Token 失效 |
| 403 | Forbidden | 已登录但权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突（如课程时间冲突） |
| 413 | Payload Too Large | 文件超出大小限制 |
| 422 | Unprocessable Entity | 数据格式验证失败（FastAPI 默认） |
| 429 | Too Many Requests | 请求频率限制 |
| 500 | Internal Server Error | 服务器内部错误 |

### 错误响应格式

```json
{
    "code": "COURSE_TIME_CONFLICT",
    "message": "该时间段已有其他课程安排",
    "detail": {
        "conflict_course_id": 42,
        "conflict_student": "张三",
        "conflict_time": "2024-01-15 14:00-16:00"
    }
}
```

### 业务错误码清单

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `TOKEN_EXPIRED` | 401 | Token 已过期 |
| `TOKEN_INVALID` | 401 | Token 格式无效 |
| `PERMISSION_DENIED` | 403 | 无权操作此资源 |
| `STUDENT_NOT_FOUND` | 404 | 学生不存在 |
| `COURSE_NOT_FOUND` | 404 | 课程不存在 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |
| `COURSE_TIME_CONFLICT` | 409 | 课程时间冲突 |
| `DUPLICATE_STUDENT` | 409 | 学生信息重复 |
| `FILE_TOO_LARGE` | 413 | 文件超过 50MB 限制 |
| `FILE_TYPE_NOT_ALLOWED` | 400 | 不支持的文件类型 |
| `STORAGE_QUOTA_EXCEEDED` | 400 | 存储空间不足 |
| `WECHAT_LOGIN_FAILED` | 400 | 微信登录失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 4. 各模块 API 端点详细设计

### 4.1 认证模块（/api/auth）

#### POST /api/auth/login — 管理端登录

**请求**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**响应** `200 OK`
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 604800,
    "user": {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "display_name": "李老师"
    }
}
```

---

#### POST /api/auth/wechat — 小程序微信登录

**请求**
```json
{
    "code": "wx.login() 返回的临时 code",
    "user_info": {
        "nickName": "张三",
        "avatarUrl": "https://thirdwx.qlogo.cn/..."
    }
}
```

**响应** `200 OK`
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 2592000,
    "user": {
        "id": 5,
        "role": "student",
        "display_name": "张三",
        "student_id": 3
    }
}
```

---

#### POST /api/auth/refresh — 刷新 Token

**请求头**：`Authorization: Bearer <current_token>`

**响应** `200 OK`
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 604800
}
```

---

### 4.2 学生管理（/api/students）

#### GET /api/students — 学生列表

**请求参数**
```
?page=1&page_size=20&search=张&subject=数学&grade=初二&is_active=true
```

**响应** `200 OK`
```json
{
    "items": [
        {
            "id": 1,
            "name": "张小明",
            "grade": "初二",
            "subjects": ["数学", "英语"],
            "parent_name": "张爸爸",
            "parent_phone": "13800138000",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "total": 25,
    "page": 1,
    "page_size": 20,
    "pages": 2
}
```

---

#### POST /api/students — 创建学生

**请求**
```json
{
    "name": "李小红",
    "grade": "高一",
    "subjects": ["数学", "物理"],
    "parent_name": "李妈妈",
    "parent_phone": "13900139000",
    "school": "第一中学",
    "notes": "基础较薄弱，需要从初中知识补起"
}
```

**响应** `201 Created`
```json
{
    "id": 26,
    "name": "李小红",
    "grade": "高一",
    "subjects": ["数学", "物理"],
    "parent_name": "李妈妈",
    "parent_phone": "13900139000",
    "school": "第一中学",
    "notes": "基础较薄弱，需要从初中知识补起",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00"
}
```

---

#### GET /api/students/{id} — 学生详情

**响应** `200 OK`
```json
{
    "id": 1,
    "name": "张小明",
    "grade": "初二",
    "subjects": ["数学", "英语"],
    "parent_name": "张爸爸",
    "parent_phone": "13800138000",
    "school": "实验中学",
    "notes": "",
    "is_active": true,
    "user_id": null,
    "parent_user_id": null,
    "created_at": "2024-01-01T00:00:00",
    "stats": {
        "total_courses": 24,
        "completed_courses": 20,
        "pending_assignments": 3,
        "total_paid": 3600.00,
        "outstanding": 300.00
    }
}
```

---

#### PUT /api/students/{id} — 更新学生信息

**请求** — 同创建，全量更新

---

#### DELETE /api/students/{id} — 删除学生

将 `is_active` 设为 `false`（软删除），保留历史数据。

**响应** `204 No Content`

---

#### GET /api/students/{id}/courses — 某学生的课程历史

**请求参数**：`?status=completed&page=1&page_size=10`

---

#### GET /api/students/{id}/assignments — 某学生的作业情况

---

#### GET /api/students/{id}/billing-summary — 某学生的收费汇总

---

### 4.3 课程管理（/api/courses）

#### GET /api/courses — 课程列表

**请求参数**
```
?start_date=2024-01-01&end_date=2024-01-31&student_id=1&status=scheduled&page=1&page_size=50
```

**响应** `200 OK`
```json
{
    "items": [
        {
            "id": 10,
            "student_id": 1,
            "student_name": "张小明",
            "subject": "数学",
            "start_time": "2024-01-15T14:00:00",
            "end_time": "2024-01-15T16:00:00",
            "duration": 120,
            "status": "scheduled",
            "location": "线上",
            "hourly_rate": 150.00,
            "notes": ""
        }
    ],
    "total": 12,
    "page": 1,
    "page_size": 50,
    "pages": 1
}
```

---

#### POST /api/courses — 创建课程

**请求**
```json
{
    "student_id": 1,
    "subject": "数学",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00",
    "location": "线上",
    "notes": "复习二次方程"
}
```

**响应** `201 Created` 或 `409 Conflict`（时间冲突时）

---

#### POST /api/courses/check-conflict — 冲突检测（不创建）

在用户选择时间后立即检测，给出即时反馈。

**请求**
```json
{
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T16:00:00",
    "exclude_id": null
}
```

**响应** `200 OK`
```json
{
    "has_conflict": true,
    "conflict": {
        "course_id": 8,
        "student_name": "王小华",
        "start_time": "2024-01-15T15:00:00",
        "end_time": "2024-01-15T17:00:00"
    }
}
```

---

#### PATCH /api/courses/{id}/status — 更新课程状态

**请求**
```json
{
    "status": "completed"
}
```

---

#### GET /api/courses/calendar — 日历视图数据

**请求参数**：`?year=2024&month=1`

**响应** `200 OK` — 按日期分组，方便日历渲染
```json
{
    "2024-01-15": [
        {
            "id": 10,
            "student_name": "张小明",
            "subject": "数学",
            "start_time": "14:00",
            "end_time": "16:00",
            "status": "scheduled"
        }
    ],
    "2024-01-17": [...]
}
```

---

### 4.4 作业管理（/api/assignments）

#### GET /api/assignments — 作业列表

**请求参数**：`?subject=数学&status=graded&page=1&page_size=20`

**响应** `200 OK`
```json
{
    "items": [
        {
            "id": 5,
            "title": "第三章练习题",
            "subject": "数学",
            "due_date": "2024-01-20",
            "created_at": "2024-01-15T10:00:00",
            "student_count": 3,
            "submitted_count": 2,
            "graded_count": 1
        }
    ],
    "total": 8,
    "page": 1,
    "page_size": 20,
    "pages": 1
}
```

---

#### POST /api/assignments — 布置作业

**请求**
```json
{
    "title": "第三章练习题",
    "subject": "数学",
    "content": "<p>完成课本 P52-P55 练习题 1-10</p>",
    "due_date": "2024-01-20",
    "student_ids": [1, 2, 3]
}
```

---

#### GET /api/assignments/{id} — 作业详情（含所有学生完成情况）

**响应** `200 OK`
```json
{
    "id": 5,
    "title": "第三章练习题",
    "content": "<p>完成课本 P52-P55 练习题 1-10</p>",
    "subject": "数学",
    "due_date": "2024-01-20",
    "students": [
        {
            "student_id": 1,
            "student_name": "张小明",
            "status": "submitted",
            "submitted_at": "2024-01-18T20:00:00",
            "score": null,
            "comment": null
        },
        {
            "student_id": 2,
            "student_name": "李小红",
            "status": "graded",
            "submitted_at": "2024-01-17T19:00:00",
            "score": 85,
            "comment": "整体掌握较好，第8题计算有误"
        }
    ]
}
```

---

#### POST /api/assignments/{id}/grade — 批改作业

**请求**
```json
{
    "student_id": 1,
    "score": 90,
    "comment": "完成质量很好，思路清晰"
}
```

---

#### GET /api/assignments/my — 小程序端：我的作业列表

**权限**：student / parent

**请求参数**：`?status=pending`

---

### 4.5 课堂反馈（/api/feedback）

#### GET /api/feedback — 反馈列表

**请求参数**：`?student_id=1&is_pushed=false&page=1&page_size=20`

---

#### POST /api/feedback — 创建反馈

**请求**
```json
{
    "course_id": 10,
    "student_id": 1,
    "performance": "今天表现很认真，课堂参与度高",
    "knowledge_mastery": "二次方程求根公式掌握良好，图像理解还需加强",
    "problems": "在复杂计算中容易出现符号错误",
    "next_plan": "下节课重点练习带根号的计算，引入因式分解法",
    "rating": 4
}
```

---

#### POST /api/feedback/{id}/push — 推送反馈给学生/家长

触发微信订阅消息推送。

**响应** `200 OK`
```json
{
    "pushed": true,
    "pushed_to": ["openid_student", "openid_parent"],
    "pushed_at": "2024-01-15T17:30:00"
}
```

---

#### GET /api/feedback/templates — 反馈模板列表

#### POST /api/feedback/templates — 创建模板

#### DELETE /api/feedback/templates/{id} — 删除模板

#### GET /api/feedback/my — 小程序端：我的反馈列表

**权限**：student / parent

---

### 4.6 学习进度（/api/progress）

#### GET /api/progress/grades — 成绩列表

**请求参数**：`?student_id=1&subject=数学&page=1&page_size=20`

---

#### POST /api/progress/grades — 添加成绩

**请求**
```json
{
    "student_id": 1,
    "subject": "数学",
    "exam_type": "midterm",
    "exam_name": "2024年春季期中考试",
    "score": 88,
    "full_score": 120,
    "exam_date": "2024-04-15",
    "notes": "排名班级第3名"
}
```

---

#### GET /api/progress/grades/trend — 成绩趋势数据（图表用）

**请求参数**：`?student_id=1&subject=数学`

**响应** `200 OK`
```json
{
    "student_name": "张小明",
    "subject": "数学",
    "data": [
        { "exam_date": "2024-01-10", "score": 75, "full_score": 100, "percentage": 75.0, "exam_name": "月测" },
        { "exam_date": "2024-02-20", "score": 82, "full_score": 100, "percentage": 82.0, "exam_name": "月测" },
        { "exam_date": "2024-04-15", "score": 88, "full_score": 120, "percentage": 73.3, "exam_name": "期中" }
    ]
}
```

---

#### GET /api/progress/knowledge-points — 知识点列表

**请求参数**：`?student_id=1&subject=数学&status=learning`

---

#### POST /api/progress/knowledge-points — 添加/更新知识点

**请求**
```json
{
    "student_id": 1,
    "subject": "数学",
    "chapter": "第三章 二次函数",
    "point_name": "二次函数图像的顶点公式",
    "status": "mastered",
    "notes": ""
}
```

---

#### GET /api/progress/report/{student_id} — 生成学习报告（PDF 源数据）

**响应** `200 OK` — 返回用于前端 jsPDF 渲染的完整数据
```json
{
    "student": { "name": "张小明", "grade": "初二" },
    "report_period": { "start": "2024-01-01", "end": "2024-06-30" },
    "course_summary": { "total": 24, "completed": 22, "total_hours": 44 },
    "grade_trend": [...],
    "knowledge_points": {
        "mastered": 15,
        "learning": 8,
        "todo": 5,
        "details": [...]
    },
    "assignment_stats": { "total": 30, "submitted": 28, "avg_score": 82 }
}
```

---

### 4.7 收费管理（/api/billing）

#### GET /api/billing/subject-prices — 科目单价列表

**响应** `200 OK`
```json
[
    { "id": 1, "subject": "数学", "price_per_hour": 150.00 },
    { "id": 2, "subject": "英语", "price_per_hour": 150.00 }
]
```

---

#### PUT /api/billing/subject-prices/{subject} — 更新科目单价

**请求**
```json
{ "price_per_hour": 180.00 }
```

---

#### GET /api/billing/records — 收费记录列表

**请求参数**：`?student_id=1&status=unpaid&start_date=2024-01-01&end_date=2024-01-31&page=1&page_size=20`

---

#### POST /api/billing/records — 手动创建收费记录

```json
{
    "student_id": 1,
    "course_id": 10,
    "amount": 300.00,
    "notes": "2小时数学课"
}
```

---

#### PATCH /api/billing/records/{id}/pay — 记录收款

**请求**
```json
{
    "paid_amount": 300.00,
    "payment_method": "wechat",
    "paid_at": "2024-01-15T18:00:00"
}
```

---

#### GET /api/billing/summary — 收费汇总报表

**请求参数**：`?start_date=2024-01-01&end_date=2024-01-31`

**响应** `200 OK`
```json
{
    "period": { "start": "2024-01-01", "end": "2024-01-31" },
    "total_receivable": 8400.00,
    "total_paid": 7200.00,
    "total_outstanding": 1200.00,
    "by_student": [
        {
            "student_id": 1,
            "student_name": "张小明",
            "receivable": 1200.00,
            "paid": 1200.00,
            "outstanding": 0
        }
    ],
    "by_subject": [
        { "subject": "数学", "total": 3600.00 }
    ],
    "monthly_trend": [
        { "month": "2024-01", "paid": 7200.00 }
    ]
}
```

---

#### GET /api/billing/outstanding — 欠费学生列表

---

### 4.8 资料管理（/api/resources）

#### GET /api/resources — 资料列表

**请求参数**：`?subject=数学&grade=初二&page=1&page_size=20`

---

#### POST /api/resources/upload — 上传资料（文件上传接口，见第5节）

---

#### GET /api/resources/{id} — 资料详情

---

#### DELETE /api/resources/{id} — 删除资料

同时删除文件系统中的文件。

---

#### POST /api/resources/{id}/share — 分享资料给学生

**请求**
```json
{
    "student_ids": [1, 2, 3]
}
```

---

#### DELETE /api/resources/{id}/share/{student_id} — 取消分享

---

#### GET /api/resources/shared — 小程序端：我能看到的资料列表

**权限**：student / parent

---

#### GET /api/resources/{id}/download — 下载资料

**权限**：admin（所有）/ student（仅分享给自己的）

服务器端验证权限后，通过 `X-Accel-Redirect` 让 Nginx 直接发送文件。

---

### 4.9 通知管理（/api/notifications）

#### GET /api/notifications — 通知列表

**请求参数**：`?is_read=false&page=1&page_size=20`

---

#### GET /api/notifications/unread-count — 未读通知数量

**响应** `200 OK`
```json
{ "count": 5 }
```

---

#### PATCH /api/notifications/{id}/read — 标记已读

#### PATCH /api/notifications/read-all — 全部已读

#### POST /api/notifications/send — 手动发送通知

**请求**
```json
{
    "user_ids": [5, 6],
    "title": "明天上课提醒",
    "content": "明天下午2点数学课，请准时参加",
    "send_wechat": true
}
```

---

### 4.10 考试辅导（/api/exam）

#### GET /api/exam/questions — 真题列表

**请求参数**：`?subject=英语&year=2023&question_type=choice&difficulty=3&tags=词汇&page=1&page_size=20`

---

#### POST /api/exam/questions — 添加真题

**请求**
```json
{
    "subject": "英语",
    "year": 2023,
    "question_type": "choice",
    "content": "Choose the correct answer: He ___ to school every day.",
    "options": { "A": "go", "B": "goes", "C": "going", "D": "gone" },
    "answer": "B",
    "explanation": "第三人称单数动词加 -s",
    "difficulty": 2,
    "tags": ["语法", "动词时态"]
}
```

---

#### GET /api/exam/vocabulary — 词汇列表

**请求参数**：`?level=高考&search=abandon&page=1&page_size=50`

---

#### POST /api/exam/vocabulary — 添加词汇

---

#### POST /api/exam/mock-exams — 创建模拟考试

**请求**
```json
{
    "student_id": 1,
    "title": "2024年英语模拟测验",
    "subject": "英语",
    "question_count": 20,
    "question_types": ["choice"],
    "difficulty_range": [2, 4],
    "tags": ["语法", "词汇"]
}
```

后端从题库随机抽取符合条件的题目。

---

#### GET /api/exam/mock-exams/{id} — 模拟考试详情（含题目）

---

### 4.11 仪表盘（/api/dashboard）

#### GET /api/dashboard/overview — 总览数据

**响应** `200 OK`
```json
{
    "today_courses": [
        {
            "id": 10,
            "student_name": "张小明",
            "subject": "数学",
            "start_time": "14:00",
            "end_time": "16:00",
            "status": "scheduled"
        }
    ],
    "stats": {
        "active_students": 15,
        "this_month_courses": 28,
        "this_month_income": 4200.00,
        "pending_grading": 5,
        "outstanding_fee": 1500.00,
        "unread_notifications": 3
    },
    "upcoming_courses": [...],
    "recent_feedback": [...]
}
```

---

## 5. 文件上传接口设计

### 5.1 上传资料

```
POST /api/resources/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**表单字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 文件本体，≤50MB |
| `title` | string | 是 | 资料标题 |
| `subject` | string | 否 | 科目 |
| `grade` | string | 否 | 适用年级 |
| `description` | string | 否 | 描述 |

**Nginx 配置**（限制上传大小）
```nginx
client_max_body_size 52m;  # 略大于 50MB，留出 multipart 开销
```

**FastAPI 实现**
```python
@router.post("/resources/upload", status_code=201)
async def upload_resource(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    grade: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. 验证文件大小
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE"})

    # 2. 验证文件类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail={"code": "FILE_TYPE_NOT_ALLOWED"})

    # 3. 生成唯一文件名
    ext = Path(file.filename).suffix
    unique_name = f"{uuid4()}{ext}"
    year_month = datetime.now().strftime("%Y/%m")
    relative_path = f"resources/{year_month}/{unique_name}"
    abs_path = Path(settings.UPLOAD_DIR) / relative_path

    # 4. 确保目录存在
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. 写入文件
    async with aiofiles.open(abs_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 6. 写入数据库
    resource = Resource(
        title=title,
        subject=subject,
        grade=grade,
        description=description,
        file_type=file.content_type,
        original_name=file.filename,
        file_path=relative_path,
        file_size=len(content),
    )
    db.add(resource)
    await db.commit()

    return resource
```

**响应** `201 Created`
```json
{
    "id": 15,
    "title": "初二数学第三章讲义",
    "subject": "数学",
    "grade": "初二",
    "file_type": "application/pdf",
    "original_name": "第三章讲义.pdf",
    "file_size": 2097152,
    "created_at": "2024-01-15T10:30:00"
}
```

### 5.2 下载文件

```
GET /api/resources/{id}/download
Authorization: Bearer <token>
```

**实现**：FastAPI 验证权限后返回 `X-Accel-Redirect` 响应头，Nginx 直接读取文件发送给客户端，避免文件流经 Python 进程（节省内存和 CPU）。

```python
@router.get("/resources/{resource_id}/download")
async def download_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(404)

    # 权限检查：admin 可以下载所有，student 只能下载分享给自己的
    if current_user.role != "admin":
        student = await get_student_by_user_id(db, current_user.id)
        share = await db.execute(
            select(ResourceShare).where(
                ResourceShare.resource_id == resource_id,
                ResourceShare.student_id == student.id
            )
        )
        if not share.scalar_one_or_none():
            raise HTTPException(403)

    # 使用 Nginx X-Accel-Redirect 高效发送文件
    encoded_name = urllib.parse.quote(resource.original_name)
    return Response(
        headers={
            "X-Accel-Redirect": f"/internal/uploads/{resource.file_path}",
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
            "Content-Type": resource.file_type,
        }
    )
```

---

## 6. 小程序端 API 特别说明

小程序端使用相同的 Base URL 和认证方式，但以下接口仅返回当前用户相关数据：

| 接口 | 说明 |
|------|------|
| `GET /api/courses/my` | 当前学生的课程（按 student_id 过滤） |
| `GET /api/assignments/my` | 当前学生的作业 |
| `GET /api/feedback/my` | 当前学生的反馈 |
| `GET /api/progress/my` | 当前学生的进度数据 |
| `GET /api/resources/shared` | 分享给当前学生的资料 |
| `GET /api/notifications` | 当前用户的通知 |

家长账号访问时，自动关联子女的 student_id 进行数据过滤。

---

## 7. 全局响应头约定

```http
Content-Type: application/json; charset=utf-8
X-Token-Remaining-Days: 5          # Token 剩余有效天数（前端据此决定是否刷新）
X-Request-Id: uuid4-string          # 请求 ID（方便日志追踪）
```
