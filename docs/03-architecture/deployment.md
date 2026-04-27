# 部署架构文档

> 状态：参考
> 范围：部署
> 更新：2026-04-26
> 说明：部署方案参考；实际部署前需结合当前代码、环境变量和服务器状态校准。

## 概述

- **服务器**：阿里云 ECS 2核2G（Ubuntu 22.04 LTS）
- **部署模式**：PostgreSQL 使用 Docker 容器，FastAPI 应用直接部署，Nginx 作为反向代理
- **域名**：需提前备案并解析到服务器公网 IP
- **SSL**：Let's Encrypt 免费证书，certbot 自动续期

---

## 1. 服务器目录结构

```
/
├── data/
│   ├── uploads/                    # 用户上传文件（≤10GB）
│   │   ├── resources/
│   │   │   └── 2024/01/            # 按年月分目录
│   │   ├── avatars/
│   │   └── temp/                   # 临时文件（定时清理）
│   ├── postgres/                   # PostgreSQL 数据持久化目录
│   └── backups/                    # 数据库备份
│       ├── daily/                  # 每日备份（保留 7 天）
│       └── weekly/                 # 每周备份（保留 4 周）
│
├── www/
│   └── admin-web/                  # React 管理端打包产物（静态文件）
│       ├── index.html
│       └── assets/
│
├── app/
│   └── tutoring-assistant/         # 后端应用代码
│       ├── main.py
│       ├── config.py
│       ├── .env                    # 环境变量（权限 600，不提交 git）
│       ├── requirements.txt
│       ├── venv/                   # Python 虚拟环境
│       ├── logs/                   # 应用日志
│       │   ├── app.log
│       │   ├── app.log.1           # logrotate 轮转
│       │   └── error.log
│       ├── models/
│       ├── routers/
│       ├── services/
│       ├── schemas/
│       └── migrations/
│
├── docker-compose.yml              # PostgreSQL 容器配置
│
└── scripts/                        # 运维脚本
    ├── backup-db.sh                # 数据库备份脚本
    ├── restore-db.sh               # 数据库恢复脚本
    ├── check-disk.sh               # 磁盘使用检查
    └── clean-temp.sh               # 清理临时文件
```

**目录权限设置**

```bash
# 应用目录
chown -R ubuntu:ubuntu /app/tutoring-assistant
chmod 750 /app/tutoring-assistant
chmod 600 /app/tutoring-assistant/.env

# 上传目录（Web 服务器和应用共享）
chown -R ubuntu:ubuntu /data/uploads
chmod 755 /data/uploads

# 备份目录
chown -R ubuntu:ubuntu /data/backups
chmod 700 /data/backups

# PostgreSQL 数据目录
chown -R 999:999 /data/postgres    # 999 是容器内 postgres 用户 UID
```

---

## 2. 进程管理方案

### 方案：Supervisor

选择 Supervisor 而非 systemd 的理由：
- 配置更简洁，日志管理内置
- 支持多进程组管理，方便后续扩展
- 重启策略灵活（自动重启、延迟重启）

### 安装

```bash
sudo apt install supervisor -y
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

### FastAPI 应用配置

```ini
# /etc/supervisor/conf.d/tutoring-assistant.conf

[program:tutoring-assistant]
command=/app/tutoring-assistant/venv/bin/gunicorn main:app
    --workers 2
    --worker-class uvicorn.workers.UvicornWorker
    --bind 127.0.0.1:8000
    --timeout 60
    --keepalive 5
    --access-logfile /app/tutoring-assistant/logs/access.log
    --error-logfile /app/tutoring-assistant/logs/gunicorn-error.log
    --log-level info
directory=/app/tutoring-assistant
user=ubuntu
autostart=true
autorestart=true
startretries=3
startsecs=5
stopwaitsecs=30
redirect_stderr=true
stdout_logfile=/app/tutoring-assistant/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=
    PYTHONUNBUFFERED="1",
    PYTHONPATH="/app/tutoring-assistant"
```

### 常用 Supervisor 命令

```bash
# 重新读取配置
sudo supervisorctl reread
sudo supervisorctl update

# 查看状态
sudo supervisorctl status

# 控制应用
sudo supervisorctl start tutoring-assistant
sudo supervisorctl stop tutoring-assistant
sudo supervisorctl restart tutoring-assistant

# 查看实时日志
sudo supervisorctl tail -f tutoring-assistant
```

### Worker 数量说明

```
# 2核 CPU：建议 workers = CPU核数
workers = 2

# 每个 worker 内存约 80-100MB
# 2 workers = ~200MB 内存
# 在 2G 服务器上留有充足余量
```

### 部署更新流程

```bash
#!/bin/bash
# /scripts/deploy.sh

set -e

echo "== 拉取最新代码 =="
cd /app/tutoring-assistant
git pull origin main

echo "== 安装/更新依赖 =="
./venv/bin/pip install -r requirements.txt --quiet

echo "== 执行数据库迁移 =="
./venv/bin/alembic upgrade head

echo "== 重启应用 =="
sudo supervisorctl restart tutoring-assistant

echo "== 更新前端静态文件 =="
# 假设前端在 CI 中已构建好，通过 scp 传输到服务器
# scp -r dist/* ubuntu@server:/www/admin-web/

echo "== 部署完成 =="
sudo supervisorctl status tutoring-assistant
```

---

## 3. Nginx 配置策略

### 安装

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
```

### 主配置文件

```nginx
# /etc/nginx/nginx.conf

user www-data;
worker_processes 2;          # 等于 CPU 核数
worker_rlimit_nofile 10240;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # 基础设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    server_tokens off;       # 隐藏 Nginx 版本号（安全）

    # MIME 类型
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" $request_time';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip 压缩（减少传输体积）
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain text/css text/javascript
        application/json application/javascript
        application/x-javascript application/xml
        image/svg+xml;

    # 限流区域（登录接口防暴力破解）
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    # 上传接口限流
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=10r/m;

    # 文件上传大小限制（略大于 50MB 留余量）
    client_max_body_size 55m;
    client_body_timeout 120s;

    include /etc/nginx/conf.d/*.conf;
}
```

### 站点配置

```nginx
# /etc/nginx/conf.d/tutoring.conf

# HTTP → HTTPS 跳转
server {
    listen 80;
    server_name your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 主站
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书（Let's Encrypt）
    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # 安全响应头
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # ========================
    # API 反向代理
    # ========================
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 大响应缓冲（学习报告等）
        proxy_buffer_size 16k;
        proxy_buffers 4 16k;
    }

    # 登录接口限流（每IP每分钟最多5次）
    location /api/auth/login {
        limit_req zone=login_limit burst=3 nodelay;
        limit_req_status 429;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传接口限流
    location /api/resources/upload {
        limit_req zone=upload_limit burst=5 nodelay;
        client_max_body_size 55m;
        client_body_timeout 120s;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # ========================
    # Nginx X-Accel-Redirect 文件服务
    # 仅允许内部重定向（FastAPI 鉴权后触发）
    # ========================
    location /internal/uploads/ {
        internal;
        alias /data/uploads/;

        # 文件下载优化
        sendfile on;
        tcp_nopush on;
        aio on;
    }

    # ========================
    # React 管理端静态文件
    # ========================
    location / {
        root /www/admin-web;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持

        # 静态资源强缓存（hash 文件名保证更新）
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # HTML 不缓存（保证能拿到最新版本）
        location = /index.html {
            expires -1;
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }
    }

    # ========================
    # API 文档（仅开发/内网访问，生产可关闭）
    # ========================
    location /api/docs {
        # 限制仅特定 IP 访问（改为你的 IP）
        # allow 你的IP地址;
        # deny all;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 日志
    access_log /var/log/nginx/tutoring-access.log main;
    error_log /var/log/nginx/tutoring-error.log warn;
}
```

### SSL 证书申请与自动续期

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx -y

# 首次申请证书
sudo certbot --nginx -d your-domain.com

# 验证自动续期（certbot 会自动创建 cron job）
sudo certbot renew --dry-run

# 查看 certbot 自动续期定时任务
cat /etc/cron.d/certbot
# 0 */12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && ...
```

---

## 4. 数据库备份策略

### 4.1 备份脚本

```bash
#!/bin/bash
# /scripts/backup-db.sh

set -e

# 配置
DB_NAME="tutoring_assistant"
DB_USER="postgres"
BACKUP_DIR="/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAILY=7   # 保留最近 7 天的每日备份
RETENTION_WEEKLY=4  # 保留最近 4 周的每周备份

# 备份类型（daily 或 weekly）
BACKUP_TYPE=${1:-daily}
BACKUP_SUBDIR="${BACKUP_DIR}/${BACKUP_TYPE}"

# 确保备份目录存在
mkdir -p "${BACKUP_SUBDIR}"

# 执行备份（使用 Docker exec 调用 pg_dump）
BACKUP_FILE="${BACKUP_SUBDIR}/backup_${DATE}.sql.gz"

echo "[$(date)] 开始备份 ${BACKUP_TYPE}..."
docker exec tutoring_db pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-password \
    | gzip > "${BACKUP_FILE}"

echo "[$(date)] 备份完成：${BACKUP_FILE}（大小：$(du -sh ${BACKUP_FILE} | cut -f1)）"

# 清理旧备份
if [ "${BACKUP_TYPE}" = "daily" ]; then
    find "${BACKUP_SUBDIR}" -name "backup_*.sql.gz" -mtime +${RETENTION_DAILY} -delete
    echo "[$(date)] 已清理超过 ${RETENTION_DAILY} 天的每日备份"
elif [ "${BACKUP_TYPE}" = "weekly" ]; then
    find "${BACKUP_SUBDIR}" -name "backup_*.sql.gz" -mtime +$((RETENTION_WEEKLY * 7)) -delete
    echo "[$(date)] 已清理超过 ${RETENTION_WEEKLY} 周的每周备份"
fi

echo "[$(date)] 备份任务完成"
```

### 4.2 恢复脚本

```bash
#!/bin/bash
# /scripts/restore-db.sh
# 用法：./restore-db.sh /data/backups/daily/backup_20240115_030000.sql.gz

set -e

BACKUP_FILE=$1
DB_NAME="tutoring_assistant"
DB_USER="postgres"

if [ -z "${BACKUP_FILE}" ]; then
    echo "用法：$0 <备份文件路径>"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "错误：备份文件不存在：${BACKUP_FILE}"
    exit 1
fi

echo "警告：此操作将覆盖现有数据库 ${DB_NAME}！"
read -p "确认继续？(输入 yes 确认) " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo "[$(date)] 开始恢复..."

# 停止应用（避免数据不一致）
sudo supervisorctl stop tutoring-assistant

# 删除并重建数据库
docker exec tutoring_db psql -U "${DB_USER}" -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec tutoring_db psql -U "${DB_USER}" -c "CREATE DATABASE ${DB_NAME};"

# 恢复数据
gunzip -c "${BACKUP_FILE}" | docker exec -i tutoring_db psql \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-password

echo "[$(date)] 数据库恢复完成"

# 重启应用
sudo supervisorctl start tutoring-assistant
echo "[$(date)] 应用已重启"
```

### 4.3 定时任务（crontab）

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下内容
# 每天凌晨 3:00 执行每日备份
0 3 * * * /scripts/backup-db.sh daily >> /var/log/backup.log 2>&1

# 每周日凌晨 4:00 执行每周备份
0 4 * * 0 /scripts/backup-db.sh weekly >> /var/log/backup.log 2>&1

# 每天凌晨 2:00 清理临时上传文件（超过 24 小时）
0 2 * * * find /data/uploads/temp -mtime +1 -delete

# 每周检查磁盘使用情况
0 9 * * 1 /scripts/check-disk.sh >> /var/log/disk-check.log 2>&1
```

### 4.4 磁盘使用检查脚本

```bash
#!/bin/bash
# /scripts/check-disk.sh

UPLOAD_DIR="/data/uploads"
UPLOAD_USAGE=$(du -sh "${UPLOAD_DIR}" 2>/dev/null | cut -f1)
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
DISK_AVAIL=$(df -h / | awk 'NR==2 {print $4}')

echo "[$(date)] 磁盘使用情况检查"
echo "  上传目录大小：${UPLOAD_USAGE}"
echo "  系统磁盘使用率：${DISK_USAGE}"
echo "  系统磁盘可用：${DISK_AVAIL}"

# 超过 8GB 时告警（10GB 限制的 80%）
UPLOAD_BYTES=$(du -sb "${UPLOAD_DIR}" 2>/dev/null | cut -f1)
LIMIT_BYTES=$((8 * 1024 * 1024 * 1024))

if [ "${UPLOAD_BYTES}" -gt "${LIMIT_BYTES}" ]; then
    echo "告警：上传目录已超过 8GB，请及时清理！"
    # 可以在这里添加邮件/微信告警
fi
```

---

## 5. 日志方案

### 5.1 应用日志（loguru）

```python
# /app/tutoring-assistant/utils/logger.py
from loguru import logger
import sys

def setup_logging():
    # 移除默认处理器
    logger.remove()

    # 控制台输出（开发环境）
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        colorize=True,
    )

    # 文件输出（生产环境）
    logger.add(
        "/app/tutoring-assistant/logs/app.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        rotation="50 MB",      # 单文件超过 50MB 自动轮转
        retention="30 days",   # 保留 30 天
        compression="gz",      # 压缩旧日志
        enqueue=True,          # 异步写入，不阻塞请求
    )

    # 错误日志单独存储
    logger.add(
        "/app/tutoring-assistant/logs/error.log",
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="gz",
        enqueue=True,
    )

    return logger
```

**在 FastAPI 中记录请求日志**

```python
# main.py
from fastapi import Request
import time
import uuid

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 请求日志
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"from {request.client.host}"
    )

    response = await call_next(request)

    # 响应日志
    duration = (time.time() - start_time) * 1000
    logger.info(
        f"[{request_id}] {response.status_code} "
        f"completed in {duration:.1f}ms"
    )

    response.headers["X-Request-Id"] = request_id
    return response
```

### 5.2 Nginx 日志

```nginx
# 日志格式（已在主配置中定义）
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" $request_time';

# 站点日志位置
access_log /var/log/nginx/tutoring-access.log main;
error_log  /var/log/nginx/tutoring-error.log warn;
```

**Nginx 日志轮转**（logrotate 自动处理）

```
# /etc/logrotate.d/nginx（Ubuntu 默认已配置）
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        [ -f /run/nginx.pid ] && kill -USR1 `cat /run/nginx.pid`
    endscript
}
```

### 5.3 系统日志

```bash
# 查看系统日志
journalctl -u nginx --since "1 hour ago"
journalctl -u docker --since "1 hour ago"

# 查看 supervisor 日志
supervisorctl tail tutoring-assistant
cat /app/tutoring-assistant/logs/supervisor.log
```

### 5.4 日志查询常用命令

```bash
# 查看最近 100 条应用日志
tail -100 /app/tutoring-assistant/logs/app.log

# 查看所有 ERROR 级别日志
grep "ERROR" /app/tutoring-assistant/logs/app.log

# 查看今天的 API 访问日志
grep "$(date +%d/%b/%Y)" /var/log/nginx/tutoring-access.log | tail -50

# 查看响应时间超过 1 秒的请求（$NF 是最后一列 request_time）
awk '$NF > 1.0' /var/log/nginx/tutoring-access.log

# 查看 500 错误
grep ' 500 ' /var/log/nginx/tutoring-access.log
```

---

## 6. 初始化部署步骤（从零开始）

### 步骤 1：服务器基础配置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y git curl wget unzip

# 创建应用目录
sudo mkdir -p /data/uploads/{resources,avatars,temp}
sudo mkdir -p /data/backups/{daily,weekly}
sudo mkdir -p /data/postgres
sudo mkdir -p /www/admin-web
sudo mkdir -p /app/tutoring-assistant
sudo mkdir -p /scripts

# 设置时区（上海）
sudo timedatectl set-timezone Asia/Shanghai
```

### 步骤 2：安装 Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# 启动 PostgreSQL
cd /  # 或 docker-compose.yml 所在目录
docker-compose up -d
docker ps  # 确认运行正常
```

### 步骤 3：安装 Python 环境

```bash
# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 创建虚拟环境
python3.11 -m venv /app/tutoring-assistant/venv

# 安装依赖
cd /app/tutoring-assistant
git clone https://github.com/your-repo/tutoring-assistant.git .
./venv/bin/pip install -r requirements.txt

# 配置 .env
cp .env.example .env
vim .env  # 填写所有必要配置

# 执行数据库迁移
./venv/bin/alembic upgrade head
```

### 步骤 4：安装并配置 Nginx

```bash
sudo apt install -y nginx
sudo cp /app/tutoring-assistant/deploy/nginx.conf /etc/nginx/conf.d/tutoring.conf
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

### 步骤 5：申请 SSL 证书

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 步骤 6：配置 Supervisor

```bash
sudo apt install -y supervisor
sudo cp /app/tutoring-assistant/deploy/supervisor.conf /etc/supervisor/conf.d/tutoring-assistant.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status  # 确认运行正常
```

### 步骤 7：设置定时任务

```bash
# 复制脚本
sudo cp /app/tutoring-assistant/deploy/scripts/* /scripts/
sudo chmod +x /scripts/*.sh

# 设置 crontab
sudo crontab -e
# 添加第 4 节中的定时任务内容
```

### 步骤 8：部署前端

```bash
# 在本地构建（或 CI/CD 中构建）
cd admin-web
npm run build

# 上传到服务器
scp -r dist/* ubuntu@your-server-ip:/www/admin-web/
```

### 步骤 9：验证部署

```bash
# 检查所有服务状态
docker ps
sudo supervisorctl status
sudo systemctl status nginx

# 测试 API
curl https://your-domain.com/api/health

# 测试登录
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 访问 API 文档
# 浏览器打开 https://your-domain.com/api/docs
```

---

## 7. 日常运维操作手册

### 查看系统整体状态

```bash
# 一键查看所有服务状态
docker ps && echo "---" && sudo supervisorctl status && echo "---" && sudo systemctl status nginx --no-pager -l
```

### 手动触发备份

```bash
/scripts/backup-db.sh daily
ls -lh /data/backups/daily/
```

### 查看磁盘使用

```bash
df -h
du -sh /data/uploads/
/scripts/check-disk.sh
```

### 紧急重启所有服务

```bash
sudo supervisorctl restart tutoring-assistant
sudo systemctl restart nginx
```

### 查看实时日志

```bash
# 应用日志
tail -f /app/tutoring-assistant/logs/app.log

# Nginx 访问日志
tail -f /var/log/nginx/tutoring-access.log

# 错误日志
tail -f /app/tutoring-assistant/logs/error.log
```
