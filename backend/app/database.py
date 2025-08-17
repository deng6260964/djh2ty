from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 数据库实例
db = SQLAlchemy()
migrate = Migrate()
