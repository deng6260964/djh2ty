# 英语家教教学管理系统

一个基于Vue.js和Flask的英语家教教学管理系统，支持教师和学生的课程管理、作业管理、考试管理等功能。

## 项目结构

```
djh2ty/
├── frontend/                 # 前端代码目录
│   ├── src/                  # Vue.js源码
│   │   ├── components/       # 组件
│   │   ├── pages/           # 页面
│   │   ├── router/          # 路由配置
│   │   ├── services/        # API服务
│   │   └── main.ts          # 入口文件
│   ├── public/              # 静态资源
│   ├── package.json         # 前端依赖配置
│   ├── vite.config.ts       # Vite配置
│   ├── tsconfig.json        # TypeScript配置
│   └── index.html           # HTML模板
├── backend/                 # 后端代码目录
│   ├── app.py              # Flask应用主文件
│   ├── models.py           # 数据模型
│   ├── routes/             # API路由
│   └── database.db         # SQLite数据库
└── README.md               # 项目说明文档
```

## 技术栈

### 前端
- Vue.js 3 + TypeScript
- Vant UI 组件库
- Vue Router 4
- Axios
- Vite

### 后端
- Flask 2.3
- SQLite
- Flask-CORS
- Werkzeug

## 功能特性

- 用户认证（教师/学生登录注册）
- 课程管理（创建、编辑、删除课程）
- 题目管理（题目库管理）
- 作业管理（布置、提交、批改作业）
- 考试管理（创建考试、在线答题）
- 学生管理（学生信息管理）
- 数据统计（学习进度、成绩统计）

## 快速开始

### 启动后端服务

```bash
# 进入项目根目录
cd djh2ty

# 启动Flask后端服务
python app.py
```

后端服务将在 http://localhost:5000 启动

### 启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:5173 启动

## API接口

后端提供RESTful API接口，主要包括：

- `/api/auth/*` - 用户认证相关
- `/api/courses/*` - 课程管理相关
- `/api/questions/*` - 题目管理相关
- `/api/assignments/*` - 作业管理相关
- `/api/exams/*` - 考试管理相关
- `/api/students/*` - 学生管理相关
- `/api/statistics/*` - 数据统计相关

## 开发说明

1. 前端使用Vite作为构建工具，支持热重载
2. 后端使用Flask框架，数据库使用SQLite
3. 前后端通过HTTP API进行通信
4. 前端已配置代理，开发时API请求会自动转发到后端服务

## 部署说明

1. 后端部署：确保Python环境，安装依赖后运行app.py
2. 前端部署：执行`npm run build`构建生产版本，部署dist目录到Web服务器

## 许可证

MIT License