# 技术选型文档

> 状态：参考
> 范围：全项目
> 更新：2026-04-26
> 说明：技术栈与总体架构参考；依赖版本和真实实现以各子项目配置文件为准。

## 1. 整体架构图

```mermaid
graph TB
    subgraph 客户端层
        WEB["Web 管理端<br/>React 18 + Ant Design<br/>浏览器访问"]
        MP["微信小程序<br/>原生开发<br/>学生/家长使用"]
    end

    subgraph 阿里云 2核2G 服务器
        NGINX["Nginx 1.24<br/>反向代理 + 静态文件服务<br/>SSL 终止"]

        subgraph 应用进程
            API["FastAPI 应用<br/>Python 3.11<br/>uvicorn + gunicorn<br/>端口 8000"]
        end

        subgraph 数据层
            PG["PostgreSQL 16<br/>Docker 容器<br/>端口 5432"]
            FS["本地文件系统<br/>/data/uploads/<br/>≤10GB"]
        end

        subgraph 进程管理
            SV["Supervisor<br/>进程守护"]
        end
    end

    subgraph 微信平台
        WXLOGIN["微信登录 API<br/>code2session"]
        WXPUSH["微信订阅消息<br/>消息推送"]
    end

    WEB -->|"HTTPS 443"| NGINX
    MP -->|"HTTPS 443"| NGINX
    MP -->|"微信 OAuth"| WXLOGIN
    NGINX -->|"反向代理 /api"| API
    NGINX -->|"静态文件 /static"| FS
    API -->|"SQLAlchemy ORM"| PG
    API -->|"文件读写"| FS
    API -->|"HTTP 调用"| WXPUSH
    SV -->|"守护"| API
```

---

## 2. 前端技术选型（Web 管理端）

### 选型结果

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Ant Design | 5.x | UI 组件库 |
| Vite | 5.x | 构建工具 |
| React Router | 6.x | 前端路由 |
| Axios | 1.x | HTTP 请求 |
| ReactQuill | 2.x | 富文本编辑器 |
| Recharts | 2.x | 数据可视化图表 |
| jsPDF | 2.x | PDF 导出 |
| dayjs | 1.x | 日期处理 |
| Zustand | 4.x | 全局状态管理 |

### 选型理由

**React 18 + TypeScript**
- React 生态成熟，组件复用性强，适合快速构建管理端界面
- TypeScript 提供类型安全，减少运行时错误，提升代码可维护性
- 对比 Vue：React 在管理系统领域更主流，开发者资源更丰富

**Ant Design 5**
- 专为管理系统设计的企业级组件库，提供表格、表单、日历、图表等开箱即用组件
- 与本系统需求高度匹配：学生列表（Table）、排课日历（Calendar）、作业表单（Form）
- 主题定制能力强，组件文档完善

**Vite**
- 开发环境启动速度极快（ESM 原生支持），显著优于 Webpack/CRA
- 构建产物体积小，适合部署在低配服务器

**Recharts**
- 基于 React 的声明式图表库，API 简洁
- 满足成绩趋势折线图、收费统计柱状图需求
- 打包体积比 ECharts 小，适合 2核2G 服务器部署

**Zustand**
- 轻量全局状态管理（相比 Redux 代码量减少 80%）
- 管理登录态（JWT token）、用户信息、全局通知

**构建产物部署策略**
- `npm run build` 产出静态文件，由 Nginx 直接服务
- 无需 Node.js 进程，节省服务器内存

---

## 3. 后端技术选型（API 服务）

### 选型结果

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11 | 运行时语言 |
| FastAPI | 0.110.x | Web 框架 |
| SQLAlchemy | 2.x | ORM |
| Alembic | 1.x | 数据库迁移 |
| Pydantic | 2.x | 数据验证 |
| uvicorn | 0.29.x | ASGI 服务器 |
| gunicorn | 21.x | 进程管理器（多 worker） |
| python-jose | 3.x | JWT 生成与验证 |
| passlib[bcrypt] | 1.x | 密码哈希 |
| httpx | 0.27.x | 调用微信 API |
| python-multipart | 0.0.x | 文件上传处理 |
| APScheduler | 3.x | 定时任务（课前提醒） |
| loguru | 0.7.x | 结构化日志 |

### 选型理由

**FastAPI**
- 异步支持（async/await），在 IO 密集型操作（数据库查询、文件读写、微信 API 调用）中性能优秀
- 自动生成 OpenAPI 文档（/api/docs），极大降低前后端联调成本
- Pydantic 集成，请求/响应数据验证零额外代码
- 对比 Django：FastAPI 轻量，内存占用更低（适合 2G 服务器）；对比 Flask：FastAPI 内置异步支持和类型验证

**SQLAlchemy 2.x + Alembic**
- 成熟的 Python ORM，支持关系查询、事务管理
- Alembic 管理数据库版本迁移，支持平滑升级/回滚
- 2.x 版本原生支持 asyncio，与 FastAPI 异步模式配合良好

**gunicorn + uvicorn workers**
- gunicorn 负责多进程管理，uvicorn 作为 worker 处理 ASGI 请求
- 2核2G 服务器建议配置：`--workers 2 --worker-class uvicorn.workers.UvicornWorker`
- 单进程内存占用约 80-100MB，2个 worker 约 200MB，在内存预算内

**APScheduler**
- 进程内定时任务调度，无需额外部署 Celery/Redis
- 用于：课前 X 小时推送提醒、每日汇总通知
- 适合小规模系统，避免引入额外中间件

**目录结构**
```
backend/
├── main.py                 # 应用入口
├── config.py               # 配置管理（读取 .env）
├── database.py             # 数据库连接池
├── deps.py                 # 依赖注入（获取 DB session、当前用户）
├── models/                 # SQLAlchemy 模型
│   ├── user.py
│   ├── student.py
│   ├── course.py
│   ├── assignment.py
│   ├── feedback.py
│   ├── resource.py
│   ├── billing.py
│   ├── progress.py
│   ├── notification.py
│   └── exam.py
├── schemas/                # Pydantic 请求/响应模型
├── routers/                # 路由处理器（每个模块一个文件）
├── services/               # 业务逻辑层
├── utils/
│   ├── auth.py             # JWT 工具
│   ├── wechat.py           # 微信 API 封装
│   ├── file.py             # 文件处理工具
│   └── scheduler.py        # 定时任务注册
├── migrations/             # Alembic 迁移文件
├── uploads/                # 文件上传目录（软链接到 /data/uploads）
└── requirements.txt
```

---

## 4. 数据库选型

### 选型结果：PostgreSQL 16（Docker 部署）

### 选型理由

**选择 PostgreSQL 而非 MySQL/SQLite**

| 对比点 | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| JSON 支持 | 原生 JSONB，高效查询 | JSON 支持较弱 | 无 |
| 并发控制 | MVCC，读写不阻塞 | 行锁，高并发下较优 | 写锁，不适合并发 |
| 全文搜索 | 内置 tsvector | 需插件 | 无 |
| 数组类型 | 支持 | 不支持 | 不支持 |
| 适合规模 | 本系统完全满足 | 满足 | 并发写入有风险 |

- JSONB 用于存储灵活的知识点掌握情况、反馈模板内容
- 本系统并发量极低（单教师），PostgreSQL 在此规模下稳定可靠
- Docker 部署简化安装和版本管理

**Docker 配置**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    container_name: tutoring_db
    environment:
      POSTGRES_DB: tutoring_assistant
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /data/postgres:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "127.0.0.1:5432:5432"  # 仅绑定本地，不暴露公网
    restart: unless-stopped
    shm_size: 128mb
```

**连接池配置（针对 2核2G）**
```python
# database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,        # 基础连接数
    max_overflow=5,     # 最大溢出连接数
    pool_timeout=30,    # 等待连接超时
    pool_recycle=1800,  # 连接复用时间（秒）
)
```

---

## 5. 微信小程序技术方案

### 开发方式：微信原生开发（WXML + WXSS + JS）

**选型理由**
- 原生开发对微信 API（登录、支付、消息推送）支持最完整，无适配问题
- 项目规模小（8个页面），无需跨平台框架
- 无 uni-app/Taro 的编译层额外体积，包体积更小（≤2MB 限制内）

**小程序架构**
```
miniprogram/
├── app.js              # 全局逻辑（初始化、全局 token 管理）
├── app.json            # 全局配置（页面路由、底部 tab）
├── app.wxss            # 全局样式
├── pages/
│   ├── index/          # 登录页（微信 oauth 登录）
│   ├── courses/        # 课程列表（日历/列表切换）
│   ├── assignments/    # 作业列表
│   ├── assignment-detail/  # 作业详情
│   ├── feedback/       # 反馈列表
│   ├── feedback-detail/ # 反馈详情
│   ├── progress/       # 学习进度（成绩图表）
│   └── resources/      # 资料列表/下载
├── utils/
│   ├── request.js      # 封装 wx.request，统一加 token 头
│   └── auth.js         # 登录态管理
└── components/         # 公共组件
```

**微信登录流程**
```
小程序端                   后端 API                微信服务器
   │                         │                        │
   │── wx.login() ──────────▶│                        │
   │◀──── code ──────────────│                        │
   │                         │                        │
   │── POST /api/auth/wechat │                        │
   │   { code: "xxx" } ────▶│                        │
   │                         │── code2session ───────▶│
   │                         │◀── openid + session ───│
   │                         │                        │
   │                         │ 查询/创建用户           │
   │                         │ 生成 JWT token          │
   │◀── { token, userInfo } ─│                        │
   │                         │                        │
   │ 存储 token 到 Storage   │                        │
```

**订阅消息推送流程**
1. 小程序端调用 `wx.requestSubscribeMessage` 获取用户授权
2. 后端存储用户 openid 和订阅状态
3. 触发推送时，后端调用 `POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send`

**关键配置**
```json
// app.json
{
  "tabBar": {
    "list": [
      { "pagePath": "pages/courses/courses", "text": "课程" },
      { "pagePath": "pages/assignments/assignments", "text": "作业" },
      { "pagePath": "pages/feedback/feedback", "text": "反馈" },
      { "pagePath": "pages/progress/progress", "text": "进度" },
      { "pagePath": "pages/resources/resources", "text": "资料" }
    ]
  }
}
```

---

## 6. 文件存储方案

### 方案：本地文件系统 + Nginx 直接服务

**目录结构**
```
/data/uploads/
├── resources/          # 教学资料（文档、PDF、图片）
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── {uuid}_filename.pdf
│   │   │   └── {uuid}_filename.docx
│   │   └── 02/
├── avatars/            # 用户头像
└── temp/               # 临时文件（处理完后清理）
```

**文件命名规则**
- 格式：`{uuid4}_{原始文件名}`
- 示例：`550e8400-e29b-41d4-a716-446655440000_数学讲义.pdf`
- 避免中文路径，uuid 保证唯一性

**Nginx 文件服务配置**
```nginx
# 需鉴权的文件访问（通过 API 代理）
location /api/resources/download/ {
    proxy_pass http://127.0.0.1:8000;
    # FastAPI 验证 JWT 后返回文件
}

# 内部文件路径（不直接对外暴露）
location /internal/uploads/ {
    internal;  # 仅允许 X-Accel-Redirect 内部重定向
    alias /data/uploads/;
}
```

**FastAPI 文件下载实现**
```python
# 验证权限后使用 X-Accel-Redirect 让 Nginx 直接发送文件（高效）
from fastapi.responses import Response

@router.get("/resources/{resource_id}/download")
async def download_resource(resource_id: int, current_user = Depends(get_current_user)):
    resource = await get_resource(resource_id)
    # 验证该用户是否有权访问此资料
    check_access(current_user, resource)

    response = Response()
    response.headers["X-Accel-Redirect"] = f"/internal/uploads/{resource.file_path}"
    response.headers["Content-Disposition"] = f'attachment; filename="{resource.original_name}"'
    return response
```

**容量管理**
- 单文件限制：50MB（Nginx client_max_body_size 配置）
- 总容量预算：10GB
- 定期清理孤立文件（数据库中已删除的资源对应的文件）
- 监控脚本：每周统计 /data/uploads 目录大小并告警

**文件上传流程**
```
客户端 ──[multipart/form-data]──▶ Nginx ──▶ FastAPI
FastAPI 验证文件类型和大小
保存到 /data/uploads/resources/{year}/{month}/
在数据库 resources 表记录文件元数据
返回资源 ID 和访问路径
```

---

## 7. 部署方案

### 方案：Docker（数据库）+ 直接部署（应用）

**选择混合部署的理由**
- PostgreSQL 使用 Docker 保证环境一致性，数据持久化到宿主机目录
- FastAPI 应用直接部署（非 Docker），避免 Docker 网络层额外延迟，内存占用更低
- 2核2G 服务器资源有限，减少 Docker 层开销

**服务器软件栈**
```
操作系统: Ubuntu 22.04 LTS
├── Nginx 1.24（系统包管理器安装）
├── Python 3.11（系统安装 + conda/pyenv 虚拟环境）
├── Docker + Docker Compose（仅用于 PostgreSQL）
└── Supervisor（进程守护）
```

**端口规划**
| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80/443 | 对外入口，自动 HTTP→HTTPS 跳转 |
| FastAPI | 127.0.0.1:8000 | 仅本地访问，不暴露公网 |
| PostgreSQL | 127.0.0.1:5432 | 仅本地访问，不暴露公网 |

**SSL 证书**
- 使用 Let's Encrypt 免费证书，certbot 自动续期
- 证书路径：`/etc/letsencrypt/live/{domain}/`

**资源估算**
| 组件 | 内存占用 |
|------|---------|
| 系统 | ~300MB |
| Nginx | ~20MB |
| PostgreSQL（Docker）| ~150MB |
| FastAPI（2 workers）| ~200MB |
| 合计 | ~670MB |
| 剩余 | ~1.3GB（缓冲足够）|

---

## 8. 安全方案

### 8.1 认证方案（JWT）

**管理端（用户名密码登录）**
```
POST /api/auth/login
{ username, password }
  ↓
bcrypt.verify(password, hashed_password)
  ↓
生成 JWT: { sub: user_id, role: "admin", exp: now+7days }
  ↓
返回 { access_token, token_type: "bearer" }
```

**小程序端（微信登录）**
```
POST /api/auth/wechat
{ code: wx.login() 返回的 code }
  ↓
微信 code2session → openid
  ↓
查找/创建用户记录
  ↓
生成 JWT: { sub: user_id, role: "student", openid: xxx, exp: now+30days }
  ↓
返回 { access_token }
```

**JWT 配置**
```python
# config.py
SECRET_KEY = os.getenv("SECRET_KEY")  # 从环境变量读取，不硬编码
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 管理端 7 天
WECHAT_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 小程序 30 天
```

**Token 刷新策略**
- 每次请求在 Response Header 中返回剩余有效期
- 前端检测到剩余 < 1 天时自动调用 `/api/auth/refresh` 续期

### 8.2 接口权限控制

```python
# 角色权限矩阵
ROLE_PERMISSIONS = {
    "admin": ["*"],  # 所有权限
    "student": [
        "GET /api/courses/my",
        "GET /api/assignments/my",
        "GET /api/feedback/my",
        "GET /api/progress/my",
        "GET /api/resources/shared",
        "GET /api/resources/download/{id}",
    ],
    "parent": [
        "GET /api/courses/student/{id}",
        "GET /api/assignments/student/{id}",
        # ...与 student 相似但查子女数据
    ]
}
```

### 8.3 数据安全

**传输安全**
- 全站 HTTPS（Let's Encrypt）
- HSTS 头部（`Strict-Transport-Security: max-age=31536000`）
- PostgreSQL 只绑定 127.0.0.1，不暴露公网端口

**存储安全**
- 密码：bcrypt 哈希存储（cost factor = 12）
- 敏感配置：存储在 `.env` 文件，不提交 git
- 上传文件：存储在 Web 根目录之外，通过 API 鉴权后才能访问

**请求安全**
- Nginx 层限制请求频率（防暴力破解）：
  ```nginx
  limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
  limit_req zone=login burst=3 nodelay;  # 应用于 /api/auth/login
  ```
- 文件上传白名单（MIME 类型验证）：
  ```python
  ALLOWED_MIME_TYPES = {
      "application/pdf", "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "image/jpeg", "image/png", "image/gif",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  }
  ```

**环境变量清单（.env）**
```env
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@127.0.0.1:5432/tutoring_assistant
DB_PASSWORD=<强密码>
SECRET_KEY=<64位随机字符串>
WECHAT_APPID=<小程序 AppID>
WECHAT_SECRET=<小程序 AppSecret>
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE=52428800  # 50MB
```

### 8.4 跨域配置（CORS）

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",  # 生产环境限定域名
        "http://localhost:3000",     # 开发环境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
