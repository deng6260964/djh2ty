#!/usr/bin/env python3
"""Flask应用启动脚本"""

import os
from app import create_app

# 获取配置环境
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # 开发环境配置
    debug = config_name == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"Starting Flask app in {config_name} mode...")
    print(f"Server running on http://{host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )