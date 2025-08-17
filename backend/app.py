"""Flask应用启动模块"""

from app import create_app
import os

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)