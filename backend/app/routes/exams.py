from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import json
from app.database import db
from app.models.exam import Exam, ExamQuestion, ExamSubmission, ExamAnswer
from app.models.question import Question
from app.models.user import User
from app.models.course import Course
from app.utils.permissions import (
    require_permission,
    require_auth,
    Permission,
    exam_management_required,
    exam_read_required,
)
from sqlalchemy import or_, and_, func
import json

exams_bp = Blueprint("exams", __name__)

# ==================== 考试管理API ====================


@exams_bp.route("/", methods=["GET"], strict_slashes=False)
@require_auth
def get_exams(current_user=None):
    """获取考试列表"""
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        course_id = request.args.get("course_id", type=int)
        status = request.args.get("status")
        search = request.args.get("search", "").strip()
        is_public = request.args.get("is_public", type=bool)

        # 构建查询
        query = Exam.query

        # 权限过滤
        if current_user.role == "student":
            # 学生只能看到公开的考试或分配给自己的考试
            query = query.filter(
                or_(
                    Exam.is_public == True,
                    Exam.allowed_students.like(f"%{current_user.id}%"),
                )
            )
        elif current_user.role == "teacher":
            # 教师可以看到自己创建的考试和公开的考试
            query = query.filter(
                or_(Exam.created_by == current_user.id, Exam.is_public == True)
            )
        # 管理员可以看到所有考试

        # 课程过滤
        if course_id:
            query = query.filter(Exam.course_id == course_id)

        # 状态过滤
        if status:
            valid_statuses = ["draft", "published", "in_progress", "ended", "graded"]
            if status in valid_statuses:
                query = query.filter(Exam.status == status)

        # 公开状态过滤
        if is_public is not None:
            query = query.filter(Exam.is_public == is_public)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Exam.title.ilike(f"%{search}%"),
                    Exam.description.ilike(f"%{search}%"),
                )
            )

        # 排序
        query = query.order_by(Exam.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        exams = [exam.to_dict() for exam in pagination.items]

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "exams": exams,
                        "pagination": {
                            "page": pagination.page,
                            "pages": pagination.pages,
                            "per_page": pagination.per_page,
                            "total": pagination.total,
                            "has_next": pagination.has_next,
                            "has_prev": pagination.has_prev,
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取考试列表失败: {str(e)}",
                }
            ),
            500,
        )


# ==================== 在线考试API ====================


@exams_bp.route("/<int:exam_id>/start", methods=["GET"], strict_slashes=False)
@require_auth
def start_exam(exam_id, current_user=None):
    """学生开始考试"""
    try:
        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "考试不存在",
                    }
                ),
                404,
            )

        # 权限检查：学生只能参加分配给自己的考试
        if current_user.role == "student":
            if not exam.is_public and str(current_user.id) not in (
                exam.allowed_students or ""
            ):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "您没有权限参加此考试",
                        }
                    ),
                    403,
                )

        # 检查考试状态
        if exam.status != "published":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_AVAILABLE",
                        "message": "考试尚未发布或已结束",
                    }
                ),
                400,
            )

        # 检查考试时间
        now = datetime.utcnow()
        if now < exam.start_time:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_STARTED",
                        "message": "考试尚未开始",
                        "start_time": exam.start_time.isoformat(),
                    }
                ),
                400,
            )

        if now > exam.end_time:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_ENDED",
                        "message": "考试已结束",
                        "end_time": exam.end_time.isoformat(),
                    }
                ),
                400,
            )

        # 检查是否已有提交记录
        existing_submission = ExamSubmission.query.filter_by(
            exam_id=exam_id, student_id=current_user.id
        ).first()

        if existing_submission:
            if existing_submission.status == "submitted":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "EXAM_ALREADY_SUBMITTED",
                            "message": "您已提交过此考试",
                        }
                    ),
                    400,
                )
            elif existing_submission.status == "in_progress":
                # 返回现有的考试会话
                return (
                    jsonify(
                        {
                            "success": True,
                            "data": {
                                "submission": existing_submission.to_dict(),
                                "exam": exam.to_dict(),
                                "message": "继续进行中的考试",
                            },
                        }
                    ),
                    200,
                )

        # 检查考试尝试次数
        submission_count = ExamSubmission.query.filter_by(
            exam_id=exam_id, student_id=current_user.id
        ).count()

        if submission_count >= exam.max_attempts:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MAX_ATTEMPTS_EXCEEDED",
                        "message": f"已达到最大尝试次数 ({exam.max_attempts})",
                    }
                ),
                400,
            )

        # 创建考试提交记录
        submission = ExamSubmission(
            exam_id=exam_id,
            student_id=current_user.id,
            started_at=now,
            status="in_progress",
        )

        db.session.add(submission)
        db.session.commit()

        # 获取考试题目
        exam_questions = (
            ExamQuestion.query.filter_by(exam_id=exam_id)
            .order_by(ExamQuestion.order_index)
            .all()
        )

        questions_data = []
        for eq in exam_questions:
            question_data = eq.question.to_dict()
            question_data["points"] = eq.points
            question_data["order_index"] = eq.order_index
            question_data["is_required"] = eq.is_required
            # 移除答案信息（学生不应看到正确答案）
            if "correct_answer" in question_data:
                del question_data["correct_answer"]
            questions_data.append(question_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "submission": submission.to_dict(),
                        "exam": exam.to_dict(),
                        "questions": questions_data,
                        "message": "考试已开始",
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"开始考试失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route('/<int:exam_id>/submit', methods=['POST'])
@require_auth
def submit_exam(exam_id, current_user=None):
    """提交考试答案"""
    try:
        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "考试不存在",
                    }
                ),
                404,
            )
        
        # 检查考试是否存在提交记录
        submission = ExamSubmission.query.filter_by(
            exam_id=exam_id,
            student_id=current_user.id
        ).first()
        
        if not submission:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "NO_EXAM_SESSION",
                        "message": "未找到考试会话，请先开始考试",
                    }
                ),
                400,
            )
            
        # 检查是否已经提交
        if submission.status == 'submitted':
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_ALREADY_SUBMITTED",
                        "message": "考试已经提交",
                    }
                ),
                400,
            )
            
        # 检查考试是否超时
        current_time = datetime.utcnow()
        exam_end_time = submission.started_at + timedelta(minutes=exam.duration_minutes)
        if current_time > exam_end_time:
            # 自动提交超时考试
            submission.status = 'submitted'
            submission.submitted_at = exam_end_time
            db.session.commit()
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_TIME_EXPIRED",
                        "message": "考试时间已到，已自动提交",
                    }
                ),
                400,
            )
            
        # 获取提交的答案数据
        data = request.get_json()
        if not data or 'answers' not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_ANSWERS",
                        "message": "缺少答案数据",
                    }
                ),
                400,
            )
            
        answers = data['answers']
        if not isinstance(answers, dict):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_ANSWERS_FORMAT",
                        "message": "答案格式错误，应为字典格式",
                    }
                ),
                400,
            )
            
        # 获取考试题目
        exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
        
        # 验证答案格式并保存
        total_score = 0
        max_score = 0
        
        for exam_question in exam_questions:
            question_id = exam_question.question_id
            question = Question.query.get(question_id)
            max_score += exam_question.points
            
            # 获取用户答案
            user_answer = answers.get(str(question_id), '')
            
            # 将答案转换为字符串格式以便存储到数据库
            if isinstance(user_answer, list):
                answer_content = ','.join([str(ans).strip() for ans in user_answer if str(ans).strip()])
            else:
                answer_content = str(user_answer) if user_answer else ''
            
            # 保存答案到ExamAnswer表
            exam_answer = ExamAnswer.query.filter_by(
                submission_id=submission.id,
                question_id=question_id
            ).first()
            
            if exam_answer:
                # 更新现有答案
                exam_answer.answer_content = answer_content
                exam_answer.updated_at = current_time
            else:
                # 创建新答案记录
                exam_answer = ExamAnswer(
                    submission_id=submission.id,
                    question_id=question_id,
                    answer_content=answer_content,
                    max_score=exam_question.points
                )
                db.session.add(exam_answer)
            
            # 自动评分（仅针对客观题）
            if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
                if question.question_type == 'multiple_choice':
                    # 多选题评分
                    correct_answers = set(question.correct_answer.split(',')) if question.correct_answer else set()
                    # 处理用户答案，支持列表和字符串格式
                    if isinstance(user_answer, list):
                        user_answers = set([str(ans).strip() for ans in user_answer if str(ans).strip()])
                    elif isinstance(user_answer, str):
                        user_answers = set(user_answer.split(',')) if user_answer else set()
                    else:
                        user_answers = set()
                    
                    if correct_answers == user_answers:
                        score = exam_question.points
                    else:
                        score = 0
                else:
                    # 单选题和判断题评分
                    if str(user_answer) == question.correct_answer:
                        score = exam_question.points
                    else:
                        score = 0
                        
                total_score += score
        
        # 更新提交状态
        submission.status = 'submitted'
        submission.submitted_at = current_time
        submission.total_score = total_score
        
        db.session.commit()
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "submission_id": submission.id,
                        "score": total_score,
                        "max_score": max_score,
                        "submitted_at": submission.submitted_at.isoformat(),
                    },
                    "message": "考试提交成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"提交考试失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route('/<int:exam_id>/submission', methods=['GET'])
@require_auth
def get_exam_submission(exam_id, current_user=None):
    """获取考试提交状态"""
    try:
        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "考试不存在",
                    }
                ),
                404,
            )
        
        # 获取考试提交记录
        submission = ExamSubmission.query.filter_by(
            exam_id=exam_id,
            student_id=current_user.id
        ).first()
        
        if not submission:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "NO_SUBMISSION_FOUND",
                        "message": "未找到考试提交记录",
                    }
                ),
                404,
            )
        
        # 计算考试时间信息
        current_time = datetime.utcnow()
        exam_end_time = submission.started_at + timedelta(minutes=exam.duration_minutes)
        time_remaining = max(0, int((exam_end_time - current_time).total_seconds()))
        
        # 获取考试题目信息
        exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
        total_questions = len(exam_questions)
        
        # 获取已保存的答案（从ExamAnswer表中获取）
        exam_answers = ExamAnswer.query.filter_by(submission_id=submission.id).all()
        saved_answers = {}
        for exam_answer in exam_answers:
            saved_answers[str(exam_answer.question_id)] = exam_answer.answer_content
        
        # 计算答题进度
        answered_questions = len([answer for answer in saved_answers.values() if answer and str(answer).strip()])
        
        # 构建返回数据
        submission_data = {
            "submission_id": submission.id,
            "exam_id": exam_id,
            "exam_title": exam.title,
            "status": submission.status,
            "start_time": submission.started_at.isoformat(),
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "duration_minutes": exam.duration_minutes,
            "time_remaining_seconds": time_remaining if submission.status != 'submitted' else 0,
            "progress": {
                "total_questions": total_questions,
                "answered_questions": answered_questions,
                "completion_rate": round((answered_questions / total_questions * 100), 2) if total_questions > 0 else 0
            },
            "answers": saved_answers,
            "score": submission.total_score,
            "is_expired": time_remaining <= 0 and submission.status != 'submitted'
        }
        
        # 如果考试已超时但未提交，自动提交
        if submission.status != 'submitted' and time_remaining <= 0:
            submission.status = 'submitted'
            submission.submitted_at = exam_end_time
            
            # 计算自动评分
            total_score = 0
            for exam_question in exam_questions:
                question_id = exam_question.question_id
                question = Question.query.get(question_id)
                user_answer = saved_answers.get(str(question_id), '')
                
                # 自动评分（仅针对客观题）
                if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
                    if question.question_type == 'multiple_choice':
                        correct_answers = set(question.correct_answer.split(',')) if question.correct_answer else set()
                        # 处理用户答案，支持列表和字符串格式
                        if isinstance(user_answer, list):
                            user_answers = set([str(ans).strip() for ans in user_answer if str(ans).strip()])
                        elif isinstance(user_answer, str):
                            user_answers = set(user_answer.split(',')) if user_answer else set()
                        else:
                            user_answers = set()
                        
                        if correct_answers == user_answers:
                            total_score += exam_question.points
                    else:
                        if str(user_answer) == question.correct_answer:
                            total_score += exam_question.points
            
            submission.score = total_score
            db.session.commit()
            
            submission_data["status"] = 'submitted'
            submission_data["submitted_at"] = exam_end_time.isoformat()
            submission_data["score"] = total_score
            submission_data["time_remaining_seconds"] = 0
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": submission_data,
                    "message": "获取考试提交状态成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取考试提交状态失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route('/<int:exam_id>/answers', methods=['POST'])
@require_auth
def save_question_answer(exam_id, current_user=None):
    """保存单题答案"""
    try:
        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "考试不存在",
                    }
                ),
                404,
            )
        
        # 获取考试提交记录
        submission = ExamSubmission.query.filter_by(
            exam_id=exam_id,
            student_id=current_user.id
        ).first()
        
        if not submission:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "NO_SUBMISSION_FOUND",
                        "message": "未找到考试提交记录，请先开始考试",
                    }
                ),
                400,
            )
        
        # 检查考试是否已提交
        if submission.status == 'submitted':
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_ALREADY_SUBMITTED",
                        "message": "考试已提交，无法修改答案",
                    }
                ),
                400,
            )
        
        # 检查考试是否超时
        current_time = datetime.utcnow()
        exam_end_time = submission.started_at + timedelta(minutes=exam.duration_minutes)
        if current_time > exam_end_time:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_TIME_EXPIRED",
                        "message": "考试时间已到，无法保存答案",
                    }
                ),
                400,
            )
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_DATA",
                        "message": "缺少请求数据",
                    }
                ),
                400,
            )
        
        question_id = data.get('question_id')
        answer = data.get('answer', '')
        
        if not question_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_QUESTION_ID",
                        "message": "缺少题目ID",
                    }
                ),
                400,
            )
        
        # 验证题目是否属于该考试
        exam_question = ExamQuestion.query.filter_by(
            exam_id=exam_id,
            question_id=question_id
        ).first()
        
        if not exam_question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_NOT_IN_EXAM",
                        "message": "题目不属于该考试",
                    }
                ),
                400,
            )
        
        # 获取题目信息进行答案格式验证
        question = Question.query.get(question_id)
        if not question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_NOT_FOUND",
                        "message": "题目不存在",
                    }
                ),
                404,
            )
        
        # 验证答案格式
        if question.question_type == 'multiple_choice' and answer:
            # 多选题答案处理
            try:
                if isinstance(answer, list):
                    # 如果答案是列表，直接处理
                    answer_list = [str(opt).strip() for opt in answer if str(opt).strip()]
                    answer = ','.join(answer_list)
                elif isinstance(answer, str):
                    # 如果答案是字符串，按逗号分隔
                    answer_list = answer.split(',')
                    answer = ','.join([opt.strip() for opt in answer_list if opt.strip()])
                else:
                    answer = str(answer)
            except Exception:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_ANSWER_FORMAT",
                            "message": "多选题答案格式错误",
                        }
                    ),
                    400,
                )
        
        # 查找或创建答案记录
        from app.models.exam import ExamAnswer
        
        exam_answer = ExamAnswer.query.filter_by(
            submission_id=submission.id,
            question_id=question_id
        ).first()
        
        if exam_answer:
            # 更新现有答案
            exam_answer.answer_content = answer
            exam_answer.updated_at = current_time
        else:
            # 创建新答案记录
            exam_answer = ExamAnswer(
                submission_id=submission.id,
                question_id=question_id,
                answer_content=answer,
                max_score=exam_question.points
            )
            db.session.add(exam_answer)
        
        # 更新提交记录时间
        submission.updated_at = current_time
        
        db.session.commit()
        
        # 计算答题进度
        exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
        total_questions = len(exam_questions)
        
        # 统计已回答的题目数量
        answered_questions = ExamAnswer.query.filter_by(
            submission_id=submission.id
        ).filter(
            ExamAnswer.answer_content.isnot(None),
            ExamAnswer.answer_content != ''
        ).count()
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "question_id": question_id,
                        "answer": answer,
                        "saved_at": current_time.isoformat(),
                        "progress": {
                            "total_questions": total_questions,
                            "answered_questions": answered_questions,
                            "completion_rate": round((answered_questions / total_questions * 100), 2) if total_questions > 0 else 0
                        }
                    },
                    "message": "答案保存成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"保存答案失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route('/<int:exam_id>/time-remaining', methods=['GET'])
@require_auth
def get_exam_time_remaining(exam_id, current_user=None):
    """获取考试剩余时间"""
    try:
        # 获取考试信息
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "考试不存在",
                    }
                ),
                404,
            )
        
        # 获取考试提交记录
        submission = ExamSubmission.query.filter_by(
            exam_id=exam_id,
            student_id=current_user.id
        ).first()
        
        if not submission:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "NO_SUBMISSION_FOUND",
                        "message": "未找到考试提交记录，请先开始考试",
                    }
                ),
                400,
            )
        
        # 检查考试是否已提交
        if submission.status == 'submitted':
            return (
                jsonify(
                    {
                        "success": True,
                        "data": {
                            "time_remaining_seconds": 0,
                            "time_remaining_minutes": 0,
                            "exam_status": "submitted",
                            "message": "考试已提交"
                        },
                        "message": "考试已提交",
                    }
                ),
                200,
            )
        
        current_time = datetime.utcnow()
        exam_end_time = submission.started_at + timedelta(minutes=exam.duration_minutes)
        
        # 计算剩余时间
        if current_time >= exam_end_time:
            # 考试时间已到，自动提交
            if submission.status != 'submitted':
                # 自动评分客观题
                score = 0
                total_score = 0
                answers = {}
                
                if submission.answers:
                    try:
                        answers = json.loads(submission.answers) if isinstance(submission.answers, str) else submission.answers
                    except (json.JSONDecodeError, TypeError):
                        answers = {}
                
                # 获取考试题目进行评分
                exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
                for eq in exam_questions:
                    question = Question.query.get(eq.question_id)
                    if question:
                        total_score += eq.score
                        
                        # 自动评分客观题
                        if question.question_type in ['single_choice', 'multiple_choice', 'true_false']:
                            student_answer = answers.get(str(question.id), '')
                            if student_answer and question.correct_answer:
                                if question.question_type == 'multiple_choice':
                                    # 多选题需要完全匹配
                                    student_choices = set(student_answer.split(',')) if student_answer else set()
                                    correct_choices = set(question.correct_answer.split(',')) if question.correct_answer else set()
                                    if student_choices == correct_choices:
                                        score += eq.score
                                else:
                                    # 单选题和判断题
                                    if student_answer.strip() == question.correct_answer.strip():
                                        score += eq.score
                
                # 更新提交记录
                submission.status = 'submitted'
                submission.submitted_at = current_time
                submission.score = score
                submission.total_score = total_score
                
                db.session.commit()
            
            return (
                jsonify(
                    {
                        "success": True,
                        "data": {
                            "time_remaining_seconds": 0,
                            "time_remaining_minutes": 0,
                            "exam_status": "time_expired",
                            "message": "考试时间已到，已自动提交"
                        },
                        "message": "考试时间已到，已自动提交",
                    }
                ),
                200,
            )
        
        # 计算剩余时间（秒）
        time_remaining = exam_end_time - current_time
        remaining_seconds = int(time_remaining.total_seconds())
        remaining_minutes = remaining_seconds // 60
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "time_remaining_seconds": remaining_seconds,
                        "time_remaining_minutes": remaining_minutes,
                        "exam_status": "in_progress",
                        "start_time": submission.started_at.isoformat(),
                        "end_time": exam_end_time.isoformat(),
                        "duration_minutes": exam.duration_minutes
                    },
                    "message": "获取剩余时间成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取剩余时间失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route("/<int:exam_id>", methods=["GET"], strict_slashes=False)
@require_auth
def get_exam(exam_id, current_user=None):
    """获取考试详情"""
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "Exam not found",
                    }
                ),
                404,
            )

        # 权限检查
        if current_user.role == "student":
            if not exam.is_public and str(current_user.id) not in (
                exam.allowed_students or ""
            ):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "Access denied",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not exam.is_public and exam.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "Access denied",
                        }
                    ),
                    403,
                )

        exam_data = exam.to_dict()

        # 获取题目列表（可选）
        include_questions = (
            request.args.get("include_questions", "false").lower() == "true"
        )
        if include_questions:
            exam_questions = (
                ExamQuestion.query.filter_by(exam_id=exam_id)
                .order_by(ExamQuestion.order_index)
                .all()
            )
            exam_data["questions"] = [eq.to_dict() for eq in exam_questions]

        return jsonify({"success": True, "data": {"exam": exam_data}}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取考试详情失败: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route("/", methods=["POST"], strict_slashes=False)
@require_permission(Permission.EXAM_CREATE)
def create_exam(current_user=None):
    """创建考试"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = [
            "title",
            "course_id",
            "start_time",
            "end_time",
            "duration_minutes",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_REQUIRED_FIELDS",
                        "message": f'Missing required fields: {", ".join(missing_fields)}',
                    }
                ),
                400,
            )

        # 验证课程是否存在
        course = Course.query.get(data["course_id"])
        if not course:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "COURSE_NOT_FOUND",
                        "message": "Course not found",
                    }
                ),
                404,
            )

        # 验证时间格式和逻辑
        try:
            start_time = datetime.fromisoformat(
                data["start_time"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
        except ValueError:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_TIME_FORMAT",
                        "message": "时间格式无效，请使用ISO格式",
                    }
                ),
                400,
            )

        if start_time >= end_time:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_TIME_RANGE",
                        "message": "开始时间必须早于结束时间",
                    }
                ),
                400,
            )

        # 验证考试时长
        duration_minutes = data["duration_minutes"]
        if duration_minutes <= 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DURATION",
                        "message": "Duration must be greater than 0",
                    }
                ),
                400,
            )

        # 创建考试
        exam = Exam(
            title=data["title"],
            description=data.get("description", ""),
            course_id=data["course_id"],
            created_by=current_user.id,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            total_points=data.get("total_points", 100),
            passing_score=data.get("passing_score", 60),
            max_attempts=data.get("max_attempts", 1),
            shuffle_questions=data.get("shuffle_questions", False),
            show_results=data.get("show_results", True),
            is_public=data.get("is_public", False),
            allowed_students=json.dumps(data.get("allowed_students", []))
            if data.get("allowed_students")
            else None,
        )

        db.session.add(exam)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"exam": exam.to_dict()},
                    "message": "Exam created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to create exam: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route("/<int:exam_id>", methods=["PUT"], strict_slashes=False)
@require_permission(Permission.EXAM_UPDATE)
def update_exam(exam_id, current_user=None):
    """更新考试"""
    try:
        data = request.get_json()

        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_FOUND",
                        "message": "Exam not found",
                    }
                ),
                404,
            )

        # 权限检查：只有创建者或管理员可以修改
        if current_user.role != "admin" and exam.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "Permission denied to modify this exam",
                    }
                ),
                403,
            )

        # 检查考试状态：已发布的考试限制修改
        if exam.status in ["in_progress", "ended", "graded"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_EDITABLE",
                        "message": "Exam has started or ended, cannot be modified",
                    }
                ),
                400,
            )

        # 更新字段
        if "title" in data:
            exam.title = data["title"]

        if "description" in data:
            exam.description = data["description"]

        if "course_id" in data:
            course = Course.query.get(data["course_id"])
            if not course:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "COURSE_NOT_FOUND",
                            "message": "课程不存在",
                        }
                    ),
                    404,
                )
            exam.course_id = data["course_id"]

        # 更新时间
        if "start_time" in data or "end_time" in data:
            try:
                start_time = datetime.fromisoformat(
                    data.get("start_time", exam.start_time.isoformat()).replace(
                        "Z", "+00:00"
                    )
                )
                end_time = datetime.fromisoformat(
                    data.get("end_time", exam.end_time.isoformat()).replace(
                        "Z", "+00:00"
                    )
                )

                if start_time >= end_time:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "INVALID_TIME_RANGE",
                                "message": "开始时间必须早于结束时间",
                            }
                        ),
                        400,
                    )

                exam.start_time = start_time
                exam.end_time = end_time
            except ValueError:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_TIME_FORMAT",
                            "message": "时间格式无效，请使用ISO格式",
                        }
                    ),
                    400,
                )

        # 更新其他配置
        if "duration_minutes" in data:
            if data["duration_minutes"] <= 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_DURATION",
                            "message": "Duration must be greater than 0",
                        }
                    ),
                    400,
                )
            exam.duration_minutes = data["duration_minutes"]

        if "total_points" in data:
            exam.total_points = data["total_points"]

        if "passing_score" in data:
            exam.passing_score = data["passing_score"]

        if "max_attempts" in data:
            exam.max_attempts = data["max_attempts"]

        if "shuffle_questions" in data:
            exam.shuffle_questions = data["shuffle_questions"]

        if "show_results" in data:
            exam.show_results = data["show_results"]

        if "is_public" in data:
            exam.is_public = data["is_public"]

        if "allowed_students" in data:
            exam.allowed_students = (
                json.dumps(data["allowed_students"])
                if data["allowed_students"]
                else None
            )

        if "status" in data:
            valid_statuses = ["draft", "published", "in_progress", "ended", "graded"]
            if data["status"] in valid_statuses:
                exam.status = data["status"]

        exam.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"exam": exam.to_dict()},
                    "message": "Exam updated successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to update exam: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route("/<int:exam_id>", methods=["DELETE"], strict_slashes=False)
@require_permission(Permission.EXAM_DELETE)
def delete_exam(exam_id, current_user=None):
    """删除考试"""
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {"success": False, "error": "EXAM_NOT_FOUND", "message": "考试不存在"}
                ),
                404,
            )

        # 权限检查：只有创建者或管理员可以删除
        if current_user.role != "admin" and exam.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "Permission denied to delete this exam",
                    }
                ),
                403,
            )

        # 检查考试状态：有提交记录的考试不能删除
        submission_count = ExamSubmission.query.filter_by(exam_id=exam_id).count()
        if submission_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_HAS_SUBMISSIONS",
                        "message": "考试已有提交记录，无法删除",
                    }
                ),
                400,
            )

        # 删除相关的考试题目
        ExamQuestion.query.filter_by(exam_id=exam_id).delete()

        # 删除考试
        db.session.delete(exam)
        db.session.commit()

        return jsonify({"success": True, "message": "Exam deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to delete exam: {str(e)}",
                }
            ),
            500,
        )


# ==================== 考试题目管理API ====================


@exams_bp.route("/<int:exam_id>/questions", methods=["GET"], strict_slashes=False)
@require_auth
def get_exam_questions(exam_id, current_user=None):
    """获取考试题目列表"""
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {"success": False, "error": "EXAM_NOT_FOUND", "message": "考试不存在"}
                ),
                404,
            )

        # 权限检查
        if current_user.role == "student":
            if not exam.is_public and str(current_user.id) not in (
                exam.allowed_students or ""
            ):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "无权限访问此考试",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not exam.is_public and exam.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "无权限访问此考试",
                        }
                    ),
                    403,
                )

        # 获取考试题目
        exam_questions = (
            ExamQuestion.query.filter_by(exam_id=exam_id)
            .order_by(ExamQuestion.order_index)
            .all()
        )

        questions_data = []
        for eq in exam_questions:
            question_data = eq.to_dict()
            if eq.question:
                question_data["question_detail"] = eq.question.to_dict()
            questions_data.append(question_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "exam_id": exam_id,
                        "questions": questions_data,
                        "total_questions": len(questions_data),
                        "total_points": sum(q["points"] for q in questions_data),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to get exam questions: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route("/<int:exam_id>/questions", methods=["POST"], strict_slashes=False)
@require_permission(Permission.EXAM_MANAGE_QUESTIONS)
def add_question_to_exam(exam_id, current_user=None):
    """添加题目到考试"""
    try:
        data = request.get_json()

        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {"success": False, "error": "EXAM_NOT_FOUND", "message": "考试不存在"}
                ),
                404,
            )

        # 权限检查：只有创建者或管理员可以管理题目
        if current_user.role != "admin" and exam.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "Permission denied to manage exam questions",
                    }
                ),
                403,
            )

        # 检查考试状态，已开始或结束的考试不能修改题目
        if exam.status in ["published", "in_progress", "ended", "graded"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_EDITABLE",
                        "message": "Exam has started or ended, cannot modify questions",
                    }
                ),
                400,
            )

        # 验证必填字段
        required_fields = ["question_id", "points"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_REQUIRED_FIELDS",
                        "message": f'Missing required fields: {", ".join(missing_fields)}',
                    }
                ),
                400,
            )

        # 验证题目是否存在
        question = Question.query.get(data["question_id"])
        if not question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_NOT_FOUND",
                        "message": "Question not found",
                    }
                ),
                404,
            )

        # 检查题目是否已存在于考试中
        existing = ExamQuestion.query.filter_by(
            exam_id=exam_id, question_id=data["question_id"]
        ).first()
        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_ALREADY_EXISTS",
                        "message": "Question already exists in exam",
                    }
                ),
                400,
            )

        # 获取下一个顺序号
        max_order = (
            db.session.query(func.max(ExamQuestion.order_index))
            .filter_by(exam_id=exam_id)
            .scalar()
            or 0
        )

        # 创建考试题目关联
        exam_question = ExamQuestion(
            exam_id=exam_id,
            question_id=data["question_id"],
            points=data["points"],
            order_index=data.get("order_index", max_order + 1),
            is_required=data.get("is_required", True),
        )

        db.session.add(exam_question)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"exam_question": exam_question.to_dict()},
                    "message": "Question added to exam successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to add question: {str(e)}",
                }
            ),
            500,
        )


@exams_bp.route(
    "/<int:exam_id>/questions/<int:question_id>",
    methods=["DELETE"],
    strict_slashes=False,
)
@require_permission(Permission.EXAM_MANAGE_QUESTIONS)
def remove_question_from_exam(exam_id, question_id, current_user=None):
    """从考试中移除题目"""
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return (
                jsonify(
                    {"success": False, "error": "EXAM_NOT_FOUND", "message": "考试不存在"}
                ),
                404,
            )

        # 权限检查：只有创建者或管理员可以管理题目
        if current_user.role != "admin" and exam.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "Permission denied to manage exam questions",
                    }
                ),
                403,
            )

        # 检查考试状态
        if exam.status in ["published", "in_progress", "ended", "graded"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_NOT_EDITABLE",
                        "message": "Exam has started or ended, cannot modify questions",
                    }
                ),
                400,
            )

        # 查找考试题目关联
        exam_question = ExamQuestion.query.filter_by(
            exam_id=exam_id, question_id=question_id
        ).first()

        if not exam_question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "EXAM_QUESTION_NOT_FOUND",
                        "message": "Question not found in exam",
                    }
                ),
                404,
            )

        # 删除考试题目关联
        db.session.delete(exam_question)
        db.session.commit()

        return (
            jsonify(
                {"success": True, "message": "Question removed from exam successfully"}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"Failed to remove question: {str(e)}",
                }
            ),
            500,
        )