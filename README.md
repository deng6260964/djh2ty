# English Tutoring System

一个现代化的英语辅导系统，支持在线课程管理、作业布置、题库管理和移动端学习。

## 项目概述

本系统采用前后端分离架构，为英语教学提供完整的数字化解决方案。支持管理员、教师和学生三种角色，提供课程管理、作业系统、题库管理、文件上传等核心功能。

## 技术栈

### 后端 (Backend)
- **框架**: Flask 3.0+
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **认证**: JWT (JSON Web Tokens)
- **ORM**: SQLAlchemy
- **API文档**: 待集成 Swagger/OpenAPI
- **测试**: pytest
- **代码质量**: flake8

### 前端 (Frontend)
- **框架**: Vue.js 3 + TypeScript
- **构建工具**: Vite
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI框架**: Tailwind CSS
- **HTTP客户端**: Axios
- **测试**: Vitest + Vue Test Utils
- **代码质量**: ESLint + Prettier

## 项目结构

```
english-tutoring-system/
├── backend/                 # Flask后端项目
│   ├── app/                # 应用核心代码
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API路由
│   │   └── utils/          # 工具函数
│   ├── config/             # 配置文件
│   ├── migrations/         # 数据库迁移
│   ├── tests/              # 测试文件
│   ├── requirements.txt    # Python依赖
│   ├── app.py             # 应用工厂
│   └── run.py             # 启动脚本
├── frontend/               # Vue.js前端项目
│   ├── src/               # 源代码
│   │   ├── components/    # Vue组件
│   │   ├── pages/         # 页面组件
│   │   ├── stores/        # Pinia状态管理
│   │   ├── services/      # API服务
│   │   └── utils/         # 工具函数
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   └── vite.config.ts     # Vite配置
└── README.md              # 项目说明
```

## 环境要求

### 后端环境
- Python 3.9+
- pip 或 conda

### 前端环境
- Node.js 20.19.0+
- npm 或 yarn

## 安装和运行

### 1. 克隆项目

```bash
git clone <repository-url>
cd english-tutoring-system
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境 (可选，推荐使用conda)
conda create -n english-tutoring python=3.9
conda activate english-tutoring

# 或使用venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 启动后端服务
python run.py
```

后端服务将在 `http://localhost:5000` 启动

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 确保使用正确的Node.js版本
nvm use 20  # 如果使用nvm

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 文件，设置API地址等配置

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

## 开发指南

### 后端开发

1. **API开发**: 在 `backend/app/routes/` 目录下创建新的路由文件
2. **数据模型**: 在 `backend/app/models/` 目录下定义数据模型
3. **数据库迁移**: 使用 `flask db migrate` 和 `flask db upgrade`
4. **测试**: 在 `backend/tests/` 目录下编写测试用例

### 前端开发

1. **组件开发**: 在 `frontend/src/components/` 目录下创建可复用组件
2. **页面开发**: 在 `frontend/src/pages/` 目录下创建页面组件
3. **状态管理**: 使用 Pinia 管理应用状态
4. **API调用**: 使用 `src/services/api.ts` 中的封装方法

### 代码质量

```bash
# 后端代码检查
cd backend
flake8 .

# 前端代码检查和格式化
cd frontend
npm run lint
npm run format
```

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test:unit
```

## API文档

后端API遵循RESTful设计原则，主要端点包括：

- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息
- `GET /api/users` - 获取用户列表
- `GET /api/courses` - 获取课程列表
- `GET /api/assignments` - 获取作业列表
- `GET /api/health` - 健康检查

详细的API文档将在后续版本中通过Swagger提供。

## 部署

### 生产环境部署

1. **后端部署**:
   - 使用 Gunicorn 作为WSGI服务器
   - 配置 Nginx 作为反向代理
   - 使用 PostgreSQL 作为生产数据库

2. **前端部署**:
   - 使用 `npm run build` 构建生产版本
   - 部署到静态文件服务器或CDN

### Docker部署 (计划中)

项目将支持Docker容器化部署，包括docker-compose配置文件。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](https://github.com/your-username/english-tutoring-system/issues)
- 邮箱: your-email@example.com

## 更新日志

### v1.0.0 (开发中)
- 项目初始化
- 基础架构搭建
- 用户认证系统
- 基础API端点
- 前端项目框架