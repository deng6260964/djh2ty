from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import timedelta

from config import Config
from routes.auth import auth_bp
from routes.courses import courses_bp
from routes.questions import questions_bp
from routes.homework import homework_bp
from routes.exams import exams_bp
from routes.students import students_bp
from routes.statistics import statistics_bp
from routes.course_management import course_management_bp
from models.user import User
from models.course import Course
from models.question import Question
from models.homework import Homework
from models.exam import Exam
from models.student import Student
from models.course_student import CourseStudent
from models.homework_answer import HomeworkAnswer
from models.exam_answer import ExamAnswer
# from models.course_management import CourseManagement

app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
cors = CORS(app)
jwt = JWTManager(app)

# 数据库初始化
def init_db():
    # 按依赖顺序创建表
    try:
        User.create_table()
        Student.create_table()
        Course.create_table()
        CourseStudent.create_table()  # 创建课程学生关联表
        Question.create_table()
        Homework.create_table()
        Exam.create_table()
        HomeworkAnswer.create_table()  # 创建作业答案表
        ExamAnswer.create_table()  # 创建考试答案表
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise

# 注册蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(questions_bp)
app.register_blueprint(homework_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(students_bp)
app.register_blueprint(statistics_bp)
app.register_blueprint(course_management_bp)

# 健康检查
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '英语家教教学管理系统运行正常'
    })



if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)