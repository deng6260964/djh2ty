# 数据库模型模块
from .user import User
from .course import Course
from .question import Question
from .homework import Homework
from .exam import Exam
from .student import Student
from .course_management import CourseManagement
from .homework_answer import HomeworkAnswer
from .exam_answer import ExamAnswer
from .database import db

__all__ = [
    'User', 'Course', 'Question', 'Homework', 'Exam', 'Student',
    'CourseManagement', 'HomeworkAnswer', 'ExamAnswer', 'db'
]