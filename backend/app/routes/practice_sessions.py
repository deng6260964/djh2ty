from flask import Blueprint, request, jsonify
from app.models.practice import Practice
from app.models.practice_session import PracticeSession
from app.models.practice_question import PracticeQuestion
from app.models.practice_answer import PracticeAnswer
from app.models.user import User
from app.models.question import Question
from app.utils.permissions import require_auth, require_permission, Permission
from app.utils.logger import logger_manager
from app.utils.validation import validate_uuid
from app import db
from datetime import datetime, timedelta
import uuid
import json

practice_sessions_bp = Blueprint('practice_sessions', __name__)
logger = logger_manager.get_logger("practice_sessions")

@practice_sessions_bp.route('/api/practice-sessions/', methods=['POST'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def start_practice(current_user):
    """
    开始练习会话
    
    请求体:
    {
        "practice_id": "练习ID"
    }
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "会话ID",
            "practice": {...},
            "questions": [...],
            "started_at": "开始时间",
            "time_limit": 时间限制(分钟)
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'practice_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: practice_id'
            }), 400
        
        # 获取练习信息
        practice = db.session.get(Practice, data['practice_id'])
        if not practice:
            return jsonify({
                'success': False,
                'message': '练习不存在'
            }), 404
        
        # 检查练习状态
        if practice.status != 'published':
            return jsonify({
                'success': False,
                'message': '练习未发布，无法开始'
            }), 400
        
        # 检查是否已有进行中的会话
        existing_session = PracticeSession.query.filter_by(
            practice_id=practice.id,
            user_id=current_user.id,
            status='in_progress'
        ).first()
        
        if existing_session:
            return jsonify({
                'success': False,
                'message': '已有进行中的练习会话',
                'data': {
                    'session_id': existing_session.id,
                    'started_at': existing_session.started_at.isoformat()
                }
            }), 409
        
        # 获取练习题目
        practice_questions = PracticeQuestion.query.filter_by(
            practice_id=practice.id
        ).order_by(PracticeQuestion.order_index).all()
        
        if not practice_questions:
            return jsonify({
                'success': False,
                'message': '练习中没有题目，无法开始'
            }), 400
        
        # 创建新的练习会话
        session = PracticeSession(
            id=str(uuid.uuid4()),
            practice_id=practice.id,
            user_id=current_user.id,
            status='in_progress',
            started_at=datetime.utcnow(),
            current_question_index=0,
            total_questions=len(practice_questions)
        )
        
        db.session.add(session)
        db.session.commit()
        
        # 构建题目列表
        questions = [{
            'id': pq.question.id,
            'title': pq.question.title,
            'content': pq.question.content,
            'question_type': pq.question.question_type,
            'options': pq.question.options if hasattr(pq.question, 'options') else None,
            'order_index': pq.order_index
        } for pq in practice_questions]
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session.id,
                'practice': {
                    'id': practice.id,
                    'title': practice.title,
                    'description': practice.description,
                    'settings': practice.settings
                },
                'questions': questions,
                'started_at': session.started_at.isoformat(),
                'time_limit': practice.settings.get('time_limit') if practice.settings else None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"开始练习失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '开始练习失败，请稍后重试'
        }), 500

@practice_sessions_bp.route('/api/practice-sessions/<session_id>', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def get_session_status(session_id, current_user):
    """
    获取练习会话状态
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "会话ID",
            "status": "会话状态",
            "current_question_index": 当前题目索引,
            "total_questions": 总题目数,
            "started_at": "开始时间",
            "paused_at": "暂停时间",
            "completed_at": "完成时间",
            "elapsed_time": 已用时间(秒),
            "answers": [...]
        }
    }
    """
    try:
        # 获取会话信息
        session = db.session.get(PracticeSession, session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': '练习会话不存在'
            }), 404
        
        # 权限检查：学生只能查看自己的会话，教师和管理员可以查看所有
        if current_user.role == 'student' and session.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权访问此练习会话'
            }), 403
        
        # 计算已用时间
        elapsed_time = 0
        if session.started_at:
            end_time = session.completed_at or datetime.utcnow()
            elapsed_time = int((end_time - session.started_at).total_seconds())
        
        # 获取已提交的答案
        answers = [{
            'question_id': answer.question_id,
            'answer_content': answer.answer_content,
            'is_correct': answer.is_correct,
            'submitted_at': answer.submitted_at.isoformat() if answer.submitted_at else None
        } for answer in session.answers]
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session.id,
                'status': session.status,
                'current_question_index': session.current_question_index,
                'total_questions': session.total_questions,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'elapsed_time': elapsed_time,
                'answers': answers
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取会话状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取会话状态失败，请稍后重试'
        }), 500

@practice_sessions_bp.route('/api/practice-sessions/<session_id>/pause', methods=['PUT'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def pause_practice(session_id, current_user):
    """
    暂停练习会话
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "会话ID",
            "status": "paused",
            "paused_at": "暂停时间"
        }
    }
    """
    try:
        # 获取会话信息
        session = db.session.get(PracticeSession, session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': '练习会话不存在'
            }), 404
        
        # 权限检查：只有会话所属学生可以暂停
        if session.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权操作此练习会话'
            }), 403
        
        # 检查会话状态
        if session.status != 'in_progress':
            return jsonify({
                'success': False,
                'message': f'无法暂停{session.status}状态的会话'
            }), 400
        
        # 暂停会话
        session.pause_session()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session.id,
                'status': session.status,
                'paused_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"暂停练习失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '暂停练习失败，请稍后重试'
        }), 500

@practice_sessions_bp.route('/api/practice-sessions/<session_id>/resume', methods=['PUT'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def resume_practice(session_id, current_user):
    """
    恢复练习会话
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "会话ID",
            "status": "in_progress",
            "resumed_at": "恢复时间"
        }
    }
    """
    try:
        # 获取会话信息
        session = db.session.get(PracticeSession, session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': '练习会话不存在'
            }), 404
        
        # 权限检查：只有会话所属学生可以恢复
        if session.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权操作此练习会话'
            }), 403
        
        # 检查会话状态
        if session.status != 'paused':
            return jsonify({
                'success': False,
                'message': f'无法恢复{session.status}状态的会话'
            }), 400
        
        # 恢复会话
        session.resume_session()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session.id,
                'status': session.status,
                'resumed_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"恢复练习失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '恢复练习失败，请稍后重试'
        }), 500

@practice_sessions_bp.route('/api/practice-sessions/<session_id>/complete', methods=['PUT'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def complete_practice(session_id, current_user):
    """
    完成练习会话
    
    响应:
    {
        "success": true,
        "data": {
            "session_id": "会话ID",
            "status": "completed",
            "completed_at": "完成时间",
            "score": 得分,
            "total_questions": 总题目数,
            "correct_answers": 正确答案数
        }
    }
    """
    try:
        # 获取会话信息
        session = db.session.get(PracticeSession, session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': '练习会话不存在'
            }), 404
        
        # 权限检查：只有会话所属学生可以完成
        if session.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': '无权操作此练习会话'
            }), 403
        
        # 检查会话状态
        if session.status not in ['in_progress', 'paused']:
            return jsonify({
                'success': False,
                'message': f'无法完成{session.status}状态的会话'
            }), 400
        
        # 计算得分
        correct_answers = sum(1 for answer in session.answers if answer.is_correct)
        total_questions = session.total_questions
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # 完成会话
        session.complete_session()
        session.correct_answers = correct_answers
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session.id,
                'status': session.status,
                'completed_at': session.completed_at.isoformat(),
                'score': score,
                'total_questions': total_questions,
                'correct_answers': correct_answers
            }
        }), 200
        
    except Exception as e:
        logger.error(f"完成练习失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '完成练习失败，请稍后重试'
        }), 500


@practice_sessions_bp.route('/api/practice-sessions/<session_id>/submit-answer', methods=['POST'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def submit_answer(session_id, current_user):
    """提交答案"""
    try:
        # 验证session_id格式
        if not validate_uuid(session_id):
            return jsonify({"error": "无效的会话ID格式"}), 400

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        question_id = data.get("question_id")
        user_answer = data.get("user_answer")

        if not question_id:
            return jsonify({"error": "题目ID不能为空"}), 400
        if user_answer is None or user_answer == "":
            return jsonify({"error": "答案不能为空"}), 400

        # 获取练习会话
        session = PracticeSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        if not session:
            return jsonify({"error": "练习会话不存在或无权限访问"}), 404

        # 检查会话状态
        if session.status not in ["in_progress", "paused"]:
            return jsonify({"error": "练习会话未激活，无法提交答案"}), 400

        # 获取题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "题目不存在"}), 404

        # 验证题目是否属于当前练习
        practice_question = PracticeQuestion.query.filter_by(
            practice_id=session.practice_id, question_id=question_id
        ).first()
        if not practice_question:
            return jsonify({"error": "题目不属于当前练习"}), 400

        # 检查是否已经回答过
        existing_answer = PracticeAnswer.query.filter_by(
            practice_session_id=session_id, practice_question_id=practice_question.id
        ).first()

        if existing_answer:
            # 更新已有答案
            existing_answer.answer_content = str(user_answer)
            existing_answer.submitted_at = datetime.utcnow()
            # 重新评分
            is_correct = question.check_answer(user_answer)
            if is_correct is not None:
                existing_answer.is_correct = is_correct
        else:
            # 创建新答案记录
            answer = PracticeAnswer(
                practice_session_id=session_id,
                practice_question_id=practice_question.id,
                user_id=current_user.id,
                answer_content=str(user_answer),
                submitted_at=datetime.utcnow()
            )
            # 自动评分
            is_correct = question.check_answer(user_answer)
            if is_correct is not None:
                answer.is_correct = is_correct
                answer.score = practice_question.points if is_correct else 0.0
                answer.max_score = practice_question.points
            
            db.session.add(answer)

        db.session.commit()

        # 返回即时反馈
        current_answer = existing_answer if existing_answer else answer
        feedback = {
            "question_id": question_id,
            "is_correct": current_answer.is_correct,
            "score": current_answer.score,
            "max_score": current_answer.max_score,
            "explanation": question.explanation if hasattr(question, 'explanation') and question.explanation else None,
            "correct_answer": question.correct_answer if current_answer.is_correct is False else None
        }

        return jsonify({
            "message": "答案提交成功",
            "feedback": feedback
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"提交答案失败: {str(e)}"}), 500


@practice_sessions_bp.route('/api/practice-sessions/<session_id>/get-hint', methods=['POST'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def get_hint(session_id, current_user):
    """获取题目提示"""
    try:
        # 验证session_id格式
        if not validate_uuid(session_id):
            return jsonify({"error": "无效的会话ID格式"}), 400

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        question_id = data.get("question_id")
        if not question_id:
            return jsonify({"error": "题目ID不能为空"}), 400

        # 获取练习会话
        session = PracticeSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        if not session:
            return jsonify({"error": "练习会话不存在或无权限访问"}), 404

        # 检查会话状态
        if session.status not in ["in_progress", "paused"]:
            return jsonify({"error": "练习会话未激活，无法获取提示"}), 400

        # 获取题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "题目不存在"}), 404

        # 验证题目是否属于当前练习
        practice_question = PracticeQuestion.query.filter_by(
            practice_id=session.practice_id, question_id=question_id
        ).first()
        if not practice_question:
            return jsonify({"error": "题目不属于当前练习"}), 400

        # 检查是否已经回答过
        existing_answer = PracticeAnswer.query.filter_by(
            practice_session_id=session_id, practice_question_id=practice_question.id
        ).first()
        if existing_answer:
            return jsonify({"error": "该题目已经回答过，无法获取提示"}), 400

        # 生成提示内容
        hint_content = "提示：仔细阅读题目，注意关键信息"
        if hasattr(question, 'question_type'):
            if question.question_type == "multiple_choice":
                hint_content = "提示：仔细阅读题目，注意关键词"
            elif question.question_type == "fill_blank":
                hint_content = "提示：仔细阅读上下文，注意语法结构"

        return jsonify({
            "message": "提示获取成功",
            "hint": hint_content
        }), 200

    except Exception as e:
        return jsonify({"error": f"获取提示失败: {str(e)}"}), 500


@practice_sessions_bp.route('/api/practice-sessions/<session_id>/skip-question', methods=['POST'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def skip_question(session_id, current_user):
    """跳过题目"""
    try:
        # 验证session_id格式
        if not validate_uuid(session_id):
            return jsonify({"error": "无效的会话ID格式"}), 400

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        question_id = data.get("question_id")
        if not question_id:
            return jsonify({"error": "题目ID不能为空"}), 400

        # 获取练习会话
        session = PracticeSession.query.filter_by(
            id=session_id, user_id=current_user.id
        ).first()
        if not session:
            return jsonify({"error": "练习会话不存在或无权限访问"}), 404

        # 检查会话状态
        if session.status not in ["in_progress", "paused"]:
            return jsonify({"error": "练习会话未激活，无法跳过题目"}), 400

        # 获取题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({"error": "题目不存在"}), 404

        # 验证题目是否属于当前练习
        practice_question = PracticeQuestion.query.filter_by(
            practice_id=session.practice_id, question_id=question_id
        ).first()
        if not practice_question:
            return jsonify({"error": "题目不属于当前练习"}), 400

        # 检查是否已经回答过
        existing_answer = PracticeAnswer.query.filter_by(
            practice_session_id=session_id, practice_question_id=practice_question.id
        ).first()
        if existing_answer:
            return jsonify({"error": "该题目已经处理过，无法跳过"}), 400

        # 创建跳题记录
        skip_answer = PracticeAnswer(
            practice_session_id=session_id,
            practice_question_id=practice_question.id,
            user_id=current_user.id,
            answer_content="SKIPPED",
            submitted_at=datetime.utcnow()
        )
        db.session.add(skip_answer)

        # 更新会话的当前题目索引
        if session.current_question_index < session.total_questions - 1:
            session.current_question_index += 1
        
        db.session.commit()

        return jsonify({
            "message": "题目跳过成功",
            "question_id": question_id,
            "current_question_index": session.current_question_index
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"跳过题目失败: {str(e)}"}), 500