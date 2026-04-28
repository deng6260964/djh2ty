# 家教辅助系统

> 状态：当前
> 范围：全项目
> 更新：2026-04-28

面向单个老师或小型家教工作室的教学工作台。当前活跃基线是老师端 V2，重点围绕“课程主线”打通排课、课后记录、作业、预收余额扣费和收费提醒。

## 当前状态

老师端 V2 已进入“老师端主链路基本收口”的阶段。

已落地的主链路包括：

- 老师工作台
- 课程 7 天周视图
- 复制上一周课程
- 课程编辑 / 完成 / 取消
- 课程详情中填写课后记录、可选布置作业并完成课程
- 完成课程自动扣费
- 取消 / 删除已完成课程后的自动扣费回滚
- 请假 / 待补课池 / 安排补课
- 学生详情账户、课后反馈、学习复盘 Tab
- 预收充值与收费提醒
- 收费与账户页
- 设置页
- 作业中心、反馈复盘、学习复盘的一轮页面收口

仍待继续收尾：

- 学生端按新版方案继续重构
- 管理端 browser-use 全量回归记录按最新实现重新执行并刷新

## 项目结构

```text
.
├── backend/       # FastAPI 后端服务
├── admin-web/     # React + Vite + TypeScript 老师/管理端
├── student-web/   # React + Vite + TypeScript 学生端
├── miniprogram/   # 微信小程序
├── docs/          # 产品、设计、架构、实现、测试和变更文档
└── docker-compose.yml
```

老师端 V2 关键代码位置：

- 工作台：`backend/app/routers/dashboard.py`、`admin-web/src/pages/Dashboard/`
- 课程周视图与复制上一周：`backend/app/routers/courses.py`、`admin-web/src/pages/Courses/`
- 学生账户与预收充值：`backend/app/routers/billing.py`、`admin-web/src/pages/Billing/`、`admin-web/src/pages/Students/`
- 设置页：`admin-web/src/pages/Settings/`

## 本地启动

### 1. 启动数据库

```bash
docker-compose up -d
```

默认会启动本地 PostgreSQL：

- host：`localhost`
- port：`5432`
- database：`tutoring_assistant`
- user：`postgres`
- password：`password`

### 2. 启动后端

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

- API：`http://localhost:8000`
- API 文档：`http://localhost:8000/api/docs`
- 健康检查：`http://localhost:8000/api/health`

开发环境首次启动会自动建表并创建默认管理员：

- 用户名：`admin`
- 密码：`admin123`

### 3. 启动老师端

```bash
cd admin-web
npm install
npm run dev
```

如需指定 API 地址，可在 `admin-web/.env.development` 中配置：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. 启动学生端

```bash
cd student-web
npm install
npm run dev
```

## 常用验证

后端完整测试：

```bash
cd backend
pytest
```

当前老师端 V2 常用后端验证：

```bash
cd backend
pytest tests/test_courses.py tests/test_billing.py tests/test_teacher_workbench.py -q
```

老师端构建：

```bash
cd admin-web
npm run build
```

学生端构建：

```bash
cd student-web
npm run build
```

文档进度检查：

```bash
node scripts/check-progress.mjs
```

保存未完成任务断点：

```bash
node scripts/create-checkpoint.mjs --workstream student-web-v2-rework --owner codex
```

详细使用说明见 `docs/08-progress/checkpoint-usage.md`。

## 文档入口

项目文档从 `docs/00-index.md` 开始读。当前老师端 V2 需求和进度优先参考：

- `docs/01-product/current.md`
- `docs/01-product/teacher-v2/status.md`
- `docs/01-product/teacher-v2/prd.md`
- `docs/02-design/teacher-v2/prototype.md`
- `docs/04-implementation/teacher-v2/plan.md`
- `docs/08-progress/project-status.md`

旧版 PRD、流程和线框已归档到 `docs/99-archive/`，只用于历史对照。

## 提交说明

敏感配置放在本地 `.env` 文件中，不要提交凭据、上传文件或构建产物。当前 `.gitignore` 已忽略：

- `node_modules/`
- `dist/`
- `.env*`
- `backend/uploads/`
- `.specstory/`
