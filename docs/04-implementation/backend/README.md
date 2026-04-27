# 家教辅助系统 - 后端服务

> 状态：参考
> 范围：后端
> 更新：2026-04-26
> 说明：后端启动与开发参考；当前 V2 业务进度以当前 V2 文档和后端测试为准。

## 技术栈
- Python 3.11+
- FastAPI 0.115
- SQLAlchemy 2.x (异步模式)
- PostgreSQL 15 (via Docker)
- JWT 鉴权

## 快速启动

### 1. 启动数据库
```bash
cd /path/to/project
docker-compose up -d
```

### 2. 安装依赖
```bash
cd backend
conda activate tutoring-assistant  # 或使用 venv
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 按需修改 .env 中的配置
```

### 4. 启动服务
```bash
python main.py
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 默认账户
- 用户名: `admin`
- 密码: `admin123`

## API 端点概览

### 认证
- `POST /api/auth/login` - 账号密码登录
- `POST /api/auth/wechat` - 微信登录
- `POST /api/auth/refresh` - 刷新 Token
- `GET /api/auth/me` - 获取当前用户

### 学生管理
- `GET /api/students` - 学生列表
- `POST /api/students` - 创建学生
- `GET /api/students/{id}` - 学生详情
- `PUT /api/students/{id}` - 更新学生
- `DELETE /api/students/{id}` - 软删除
- `GET /api/students/{id}/courses` - 学生课程历史
- `GET /api/students/{id}/billing-summary` - 收费汇总

### 课程管理
- `GET /api/courses` - 课程列表
- `POST /api/courses` - 创建课程（含冲突检测）
- `GET /api/courses/calendar` - 日历视图
- `POST /api/courses/check-conflict` - 冲突检测
- `GET /api/courses/{id}` - 课程详情
- `PUT /api/courses/{id}` - 更新课程
- `DELETE /api/courses/{id}` - 删除课程
- `PATCH /api/courses/{id}/status` - 更新状态

### 作业管理
- `GET /api/assignments` - 作业列表
- `POST /api/assignments` - 布置作业
- `GET /api/assignments/{id}` - 作业详情
- `PUT /api/assignments/{id}` - 更新作业
- `DELETE /api/assignments/{id}` - 删除作业
- `POST /api/assignments/{id}/grade/{student_id}` - 批改作业

### 课堂反馈
- `GET /api/feedback` - 反馈列表
- `POST /api/feedback` - 创建反馈
- `GET /api/feedback/{id}` - 反馈详情
- `PUT /api/feedback/{id}` - 更新反馈
- `POST /api/feedback/{id}/push` - 推送反馈
- `GET /api/feedback/templates` - 模板列表
- `POST /api/feedback/templates` - 创建模板

### 收费管理
- `GET /api/billing/subject-prices` - 科目单价
- `PUT /api/billing/subject-prices/{subject}` - 更新单价
- `GET /api/billing/records` - 收费记录
- `POST /api/billing/records` - 创建记录
- `PATCH /api/billing/records/{id}/pay` - 记录收款
- `DELETE /api/billing/records/{id}` - 删除记录
- `GET /api/billing/summary` - 收费汇总
- `GET /api/billing/outstanding` - 欠费学生

### 学习进度
- `GET /api/progress/grades` - 成绩列表
- `POST /api/progress/grades` - 添加成绩
- `GET /api/progress/grades/trend` - 成绩趋势
- `GET /api/progress/knowledge-points` - 知识点列表
- `POST /api/progress/knowledge-points` - 创建知识点
- `GET /api/progress/report/{student_id}` - 学习报告

### 资料管理
- `GET /api/resources` - 资料列表
- `POST /api/resources/upload` - 上传文件
- `GET /api/resources/{id}` - 资料详情
- `DELETE /api/resources/{id}` - 删除资料
- `POST /api/resources/{id}/share` - 分享资料
- `DELETE /api/resources/{id}/share/{student_id}` - 撤销分享
- `GET /api/resources/{id}/download` - 下载资料

### 通知
- `GET /api/notifications` - 通知列表
- `POST /api/notifications` - 创建通知
- `PATCH /api/notifications/{id}/read` - 标记已读
- `PATCH /api/notifications/read-all` - 全部已读
- `GET /api/notifications/unread-count` - 未读数量

### 考试辅导
- `GET /api/exam/questions` - 题目列表
- `POST /api/exam/questions` - 添加题目
- `PUT /api/exam/questions/{id}` - 更新题目
- `DELETE /api/exam/questions/{id}` - 删除题目
- `GET /api/exam/vocabulary` - 词汇列表
- `POST /api/exam/vocabulary` - 添加词汇
- `POST /api/exam/mock-exams` - 创建模拟考试
- `GET /api/exam/mock-exams/{id}` - 模拟考试详情

### 仪表盘
- `GET /api/dashboard/overview` - 总览数据

## 目录结构
```
backend/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   ├── dependencies.py  # 依赖注入
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/         # Pydantic 模型
│   ├── routers/         # API 路由
│   └── utils/           # 工具函数
├── alembic/             # 数据库迁移
├── uploads/             # 文件上传目录
├── requirements.txt
├── .env
└── main.py              # 启动入口
```
