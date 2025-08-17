#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练习统计分析API路由
实现练习统计报告、学生进度查询、错题统计等功能
"""

import random
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from sqlalchemy import func, and_, or_, desc
from app.database import db
from app.models.user import User
from app.models.course import Course
from app.models.practice import Practice
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.models.practice_question import PracticeQuestion
from app.models.question import Question
from app.utils.permissions import require_auth, require_permission, Permission
from app.utils.validation import validate_uuid

# 创建蓝图
practice_statistics_bp = Blueprint('practice_statistics', __name__, url_prefix='/api')

@practice_statistics_bp.route('/practices/<practice_id>/statistics', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_VIEW_STATS)
def get_practice_statistics(practice_id, current_user):
    """
    获取练习统计报告
    
    Args:
        practice_id: 练习ID
        current_user: 当前用户
    
    Returns:
        练习统计数据
    """
    try:
        # 验证练习ID格式
        if not _validate_uuid(practice_id):
            return jsonify({
                "success": False,
                "error": "INVALID_PRACTICE_ID",
                "message": "练习ID格式无效"
            }), 400
        
        # 查询练习
        practice = Practice.query.get(practice_id)
        if not practice:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_NOT_FOUND",
                        "message": "练习不存在",
                    }
                ),
                404,
            )
        
        # 权限检查
        if not _can_view_practice_stats(current_user, practice):
            return jsonify({
                "success": False,
                "error": "PERMISSION_DENIED",
                "message": "权限不足"
            }), 403
        
        # 获取统计数据
        stats = _calculate_practice_statistics(practice_id)
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        'practice_id': practice_id,
                        'practice_title': practice.title,
                        'statistics': stats
                    },
                    "message": "练习统计报告获取成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        current_app.logger.error(f"获取练习统计失败: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取练习统计失败: {str(e)}",
                }
            ),
            500,
        )

@practice_statistics_bp.route('/users/<user_id>/practice-statistics', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_VIEW_PROGRESS)
def get_user_practice_statistics(user_id, current_user):
    """
    获取用户练习统计
    
    Args:
        user_id: 用户ID
        current_user: 当前用户
    
    Returns:
        用户练习统计数据
    """
    try:
        # 验证用户ID格式
        if not _validate_uuid(user_id):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_USER_ID",
                        "message": "无效的用户ID格式",
                    }
                ),
                400,
            )
        
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "USER_NOT_FOUND",
                        "message": "用户不存在",
                    }
                ),
                404,
            )
        
        # 权限检查
        if not _can_view_user_stats(current_user, user):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        
        # 获取查询参数
        course_id = request.args.get('course_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 获取用户统计数据
        stats = _calculate_user_statistics(user_id, course_id, start_date, end_date)
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        'user_id': user_id,
                        'user_name': user.name,
                        'statistics': stats
                    },
                    "message": "用户练习统计获取成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        current_app.logger.error(f"获取用户练习统计失败: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取用户练习统计失败: {str(e)}",
                }
            ),
            500,
        )

@practice_statistics_bp.route('/practices/<practice_id>/wrong-questions', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_VIEW_STATS)
def get_practice_wrong_questions(practice_id, current_user):
    """
    获取练习错题统计
    
    Args:
        practice_id: 练习ID
        current_user: 当前用户
    
    Returns:
        错题统计数据
    """
    try:
        # 验证练习ID格式
        if not _validate_uuid(practice_id):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_PRACTICE_ID",
                        "message": "无效的练习ID格式",
                    }
                ),
                400,
            )
        
        # 查询练习
        practice = Practice.query.get(practice_id)
        if not practice:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_NOT_FOUND",
                        "message": "练习不存在",
                    }
                ),
                404,
            )
        
        # 权限检查
        if not _can_view_practice_stats(current_user, practice):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        
        # 获取错题统计
        wrong_questions = _get_wrong_questions_statistics(practice_id)
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        'practice_id': practice_id,
                        'practice_title': practice.title,
                        'wrong_questions': wrong_questions
                    },
                    "message": "错题统计获取成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        current_app.logger.error(f"获取错题统计失败: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取错题统计失败: {str(e)}",
                }
            ),
            500,
        )

@practice_statistics_bp.route('/courses/<course_id>/practice-overview', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_VIEW_STATS)
def get_course_practice_overview(course_id, current_user):
    """
    获取课程练习概览统计
    
    Args:
        course_id: 课程ID
        current_user: 当前用户
    
    Returns:
        课程练习概览数据
    """
    try:
        # 验证课程ID格式
        if not _validate_uuid(course_id):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_COURSE_ID",
                        "message": "无效的课程ID格式",
                    }
                ),
                400,
            )
        
        # 查询课程
        course = Course.query.get(course_id)
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
        
        # 权限检查
        if not _can_view_course_stats(current_user, course):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "权限不足",
                    }
                ),
                403,
            )
        
        # 获取课程练习概览
        overview = _get_course_practice_overview(course_id)
        
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        'course_id': course_id,
                        'course_name': course.name,
                        'overview': overview
                    },
                    "message": "课程练习概览获取成功",
                }
            ),
            200,
        )
        
    except Exception as e:
        current_app.logger.error(f"获取课程练习概览失败: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取课程练习概览失败: {str(e)}",
                }
            ),
            500,
        )

# 辅助函数
def _validate_uuid(uuid_string):
    """验证UUID格式"""
    try:
        uuid.UUID(str(uuid_string))
        return True
    except (ValueError, TypeError):
        return False



def _check_practice_access(practice, current_user):
    """检查用户是否有权限访问练习"""
    if current_user.role == "admin":
        return True
    elif current_user.role == "teacher":
        return practice.creator_id == current_user.id
    elif current_user.role == "student":
        return practice.status == "published"
    return False

def _can_view_practice_stats(user, practice):
    """
    检查用户是否可以查看练习统计
    
    Args:
        user: 用户对象
        practice: 练习对象
    
    Returns:
        bool: 是否有权限
    """
    if user.role == 'admin':
        return True
    elif user.role == 'teacher':
        return practice.creator_id == user.id
    elif user.role == 'student':
        # 学生只能查看自己参与的练习统计
        return practice.status == 'published'
    return False

def _can_view_user_stats(current_user, target_user):
    """
    检查用户是否可以查看指定用户的统计
    
    Args:
        current_user: 当前用户
        target_user: 目标用户
    
    Returns:
        bool: 是否有权限
    """
    if current_user.role == 'admin':
        return True
    elif current_user.role == 'teacher':
        # 教师可以查看自己课程中学生的统计
        return True  # 具体权限在查询时进一步过滤
    elif current_user.role == 'student':
        # 学生只能查看自己的统计
        return current_user.id == target_user.id
    return False

def _can_view_course_stats(user, course):
    """
    检查用户是否可以查看课程统计
    
    Args:
        user: 用户对象
        course: 课程对象
    
    Returns:
        bool: 是否有权限
    """
    if user.role == 'admin':
        return True
    elif user.role == 'teacher':
        # 教师可以查看自己创建的课程统计
        return course.creator_id == user.id
    return False

def _calculate_practice_statistics(practice_id):
    """
    计算练习统计数据
    
    Args:
        practice_id: 练习ID
    
    Returns:
        dict: 统计数据
    """
    # 基础统计查询
    total_sessions = PracticeSession.query.filter_by(practice_id=practice_id).count()
    completed_sessions = PracticeSession.query.filter_by(
        practice_id=practice_id, 
        status='completed'
    ).count()
    
    # 参与人数
    participants = db.session.query(PracticeSession.user_id).filter_by(
        practice_id=practice_id
    ).distinct().count()
    
    # 平均完成率
    avg_completion = db.session.query(
        func.avg(PracticeSession.completion_rate)
    ).filter_by(
        practice_id=practice_id,
        status='completed'
    ).scalar() or 0
    
    # 平均正确率
    avg_accuracy = db.session.query(
        func.avg(PracticeSession.correct_answers * 100.0 / PracticeSession.total_questions)
    ).filter(
        and_(
            PracticeSession.practice_id == practice_id,
            PracticeSession.status == 'completed',
            PracticeSession.total_questions > 0
        )
    ).scalar() or 0
    
    # 平均用时
    avg_time = db.session.query(
        func.avg(PracticeSession.total_time_spent)
    ).filter_by(
        practice_id=practice_id,
        status='completed'
    ).scalar() or 0
    
    return {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'participants': participants,
        'completion_rate': round(completed_sessions / total_sessions * 100, 2) if total_sessions > 0 else 0,
        'average_completion': round(avg_completion, 2),
        'average_accuracy': round(avg_accuracy, 2),
        'average_time_spent': int(avg_time)
    }

def _calculate_user_statistics(user_id, course_id=None, start_date=None, end_date=None):
    """
    计算用户统计数据
    
    Args:
        user_id: 用户ID
        course_id: 课程ID（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        dict: 用户统计数据
    """
    # 构建查询条件
    query = PracticeSession.query.filter_by(user_id=user_id)
    
    if course_id:
        query = query.join(Practice).filter(Practice.course_id == course_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(PracticeSession.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(PracticeSession.created_at <= end_dt)
        except ValueError:
            pass
    
    # 基础统计
    total_sessions = query.count()
    completed_sessions = query.filter_by(status='completed').count()
    
    # 总练习时间
    total_time = query.filter_by(status='completed').with_entities(
        func.sum(PracticeSession.total_time_spent)
    ).scalar() or 0
    
    # 平均正确率
    avg_accuracy = query.filter(
        and_(
            PracticeSession.status == 'completed',
            PracticeSession.total_questions > 0
        )
    ).with_entities(
        func.avg(PracticeSession.correct_answers * 100.0 / PracticeSession.total_questions)
    ).scalar() or 0
    
    # 最近7天活动
    week_ago = datetime.now() - timedelta(days=7)
    recent_sessions = query.filter(PracticeSession.created_at >= week_ago).count()
    
    return {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': round(completed_sessions / total_sessions * 100, 2) if total_sessions > 0 else 0,
        'total_time_spent': int(total_time),
        'average_accuracy': round(avg_accuracy, 2),
        'recent_activity': recent_sessions
    }

def _get_wrong_questions_statistics(practice_id):
    """
    获取错题统计
    
    Args:
        practice_id: 练习ID
    
    Returns:
        list: 错题统计列表
    """
    # 查询错题统计
    wrong_stats = db.session.query(
        PracticeQuestion.id,
        PracticeQuestion.order_index,
        Question.title,
        Question.type,
        func.count(PracticeAnswer.id).label('total_attempts'),
        func.sum(func.cast(PracticeAnswer.is_correct == False, db.Integer)).label('wrong_count')
    ).join(
        PracticeAnswer, PracticeAnswer.practice_question_id == PracticeQuestion.id
    ).join(
        Question, Question.id == PracticeQuestion.question_id
    ).filter(
        PracticeQuestion.practice_id == practice_id
    ).group_by(
        PracticeQuestion.id,
        PracticeQuestion.order_index,
        Question.title,
        Question.type
    ).order_by(
        PracticeQuestion.order_index
    ).all()
    
    result = []
    for stat in wrong_stats:
        wrong_rate = (stat.wrong_count / stat.total_attempts * 100) if stat.total_attempts > 0 else 0
        result.append({
            'question_id': stat.id,
            'order_index': stat.order_index,
            'title': stat.title,
            'type': stat.type,
            'total_attempts': stat.total_attempts,
            'wrong_count': stat.wrong_count,
            'wrong_rate': round(wrong_rate, 2)
        })
    
    return result

def _get_course_practice_overview(course_id):
    """
    获取课程练习概览
    
    Args:
        course_id: 课程ID
    
    Returns:
        dict: 课程练习概览数据
    """
    # 课程练习总数
    total_practices = Practice.query.filter_by(course_id=course_id).count()
    published_practices = Practice.query.filter_by(
        course_id=course_id, 
        status='published'
    ).count()
    
    # 学生参与统计
    total_participants = db.session.query(
        PracticeSession.user_id
    ).join(
        Practice, Practice.id == PracticeSession.practice_id
    ).filter(
        Practice.course_id == course_id
    ).distinct().count()
    
    # 完成情况统计
    completion_stats = db.session.query(
        func.count(PracticeSession.id).label('total_sessions'),
        func.sum(func.cast(PracticeSession.status == 'completed', db.Integer)).label('completed_sessions')
    ).join(
        Practice, Practice.id == PracticeSession.practice_id
    ).filter(
        Practice.course_id == course_id
    ).first()
    
    total_sessions = completion_stats.total_sessions or 0
    completed_sessions = completion_stats.completed_sessions or 0
    
    # 平均分数
    avg_score = db.session.query(
        func.avg(PracticeSession.correct_answers * 100.0 / PracticeSession.total_questions)
    ).join(
        Practice, Practice.id == PracticeSession.practice_id
    ).filter(
        and_(
            Practice.course_id == course_id,
            PracticeSession.status == 'completed',
            PracticeSession.total_questions > 0
        )
    ).scalar() or 0
    
    return {
        'total_practices': total_practices,
        'published_practices': published_practices,
        'total_participants': total_participants,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': round(completed_sessions / total_sessions * 100, 2) if total_sessions > 0 else 0,
        'average_score': round(avg_score, 2)
    }

# ==================== T11_009 进度跟踪API ====================

@practice_statistics_bp.route('/learning-history/<user_id>', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def get_learning_history(user_id):
    """
    学习历史查询
    
    Args:
        user_id: 用户ID
    
    Query Parameters:
        course_id: 课程ID（可选）
        start_date: 开始日期（可选，ISO格式）
        end_date: 结束日期（可选，ISO格式）
        limit: 返回记录数限制（可选，默认50）
        offset: 偏移量（可选，默认0）
    
    Returns:
        JSON: 学习历史记录列表
    """
    # 验证用户ID
    if not validate_uuid(user_id):
        return jsonify({'error': '无效的用户ID'}), 400
    
    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 权限检查
    current_user = g.current_user
    if not _can_view_user_stats(current_user, target_user):
        return jsonify({'error': '权限不足'}), 403
    
    # 获取查询参数
    course_id = request.args.get('course_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = min(int(request.args.get('limit', 50)), 100)  # 最大100条
    offset = int(request.args.get('offset', 0))
    
    # 构建查询
    query = PracticeSession.query.filter_by(user_id=user_id)
    
    # 课程过滤
    if course_id:
        if not validate_uuid(course_id):
            return jsonify({'error': '无效的课程ID'}), 400
        query = query.join(Practice).filter(Practice.course_id == course_id)
    
    # 日期过滤
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(PracticeSession.created_at >= start_dt)
        except ValueError:
            return jsonify({'error': '无效的开始日期格式'}), 400
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(PracticeSession.created_at <= end_dt)
        except ValueError:
            return jsonify({'error': '无效的结束日期格式'}), 400
    
    # 执行查询
    sessions = query.join(Practice).join(Course).order_by(
        desc(PracticeSession.created_at)
    ).offset(offset).limit(limit).all()
    
    # 构建响应数据
    history_data = []
    for session in sessions:
        accuracy = 0
        if session.total_questions > 0:
            accuracy = round(session.correct_answers / session.total_questions * 100, 2)
        
        history_data.append({
            'session_id': session.id,
            'practice_id': session.practice_id,
            'practice_title': session.practice.title,
            'course_id': session.practice.course_id,
            'course_name': session.practice.course.name,
            'status': session.status,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': accuracy,
            'completion_rate': session.completion_rate,
            'total_time_spent': session.total_time_spent,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        })
    
    # 获取总数
    total_count = query.count()
    
    return jsonify({
        'learning_history': history_data,
        'pagination': {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }
    }), 200

@practice_statistics_bp.route('/personal-report/<user_id>', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def get_personal_report(user_id):
    """
    获取个人统计报告
    
    Args:
        user_id: 用户ID
    
    Query Parameters:
        course_id: 课程ID（可选）
        period: 统计周期（可选：week/month/quarter/year，默认month）
    
    Returns:
        JSON: 个人统计报告
    """
    # 验证用户ID
    if not validate_uuid(user_id):
        return jsonify({'error': '无效的用户ID'}), 400
    
    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 权限检查
    current_user = g.current_user
    if not _can_view_user_stats(current_user, target_user):
        return jsonify({'error': '权限不足'}), 403
    
    # 获取查询参数
    course_id = request.args.get('course_id')
    period = request.args.get('period', 'month')
    
    # 计算时间范围
    now = datetime.now()
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'quarter':
        start_date = now - timedelta(days=90)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        return jsonify({'error': '无效的统计周期'}), 400
    
    # 获取基础统计
    stats = _calculate_user_statistics(
        user_id=user_id,
        course_id=course_id,
        start_date=start_date.isoformat(),
        end_date=now.isoformat()
    )
    
    # 获取学习趋势数据（按天统计）
    trend_query = PracticeSession.query.filter(
        and_(
            PracticeSession.user_id == user_id,
            PracticeSession.created_at >= start_date
        )
    )
    
    if course_id:
        if not validate_uuid(course_id):
            return jsonify({'error': '无效的课程ID'}), 400
        trend_query = trend_query.join(Practice).filter(Practice.course_id == course_id)
    
    # 按日期分组统计
    daily_stats = db.session.query(
        func.date(PracticeSession.created_at).label('date'),
        func.count(PracticeSession.id).label('sessions'),
        func.sum(PracticeSession.total_time_spent).label('time_spent'),
        func.avg(PracticeSession.correct_answers * 100.0 / PracticeSession.total_questions).label('avg_accuracy')
    ).filter(
        and_(
            PracticeSession.user_id == user_id,
            PracticeSession.created_at >= start_date,
            PracticeSession.status == 'completed',
            PracticeSession.total_questions > 0
        )
    )
    
    if course_id:
        daily_stats = daily_stats.join(Practice).filter(Practice.course_id == course_id)
    
    daily_stats = daily_stats.group_by(
        func.date(PracticeSession.created_at)
    ).order_by(
        func.date(PracticeSession.created_at)
    ).all()
    
    # 构建趋势数据
    trend_data = []
    for stat in daily_stats:
        trend_data.append({
            'date': stat.date.isoformat(),
            'sessions': stat.sessions,
            'time_spent': int(stat.time_spent or 0),
            'average_accuracy': round(stat.avg_accuracy or 0, 2)
        })
    
    # 获取最近错题
    recent_wrong_answers = db.session.query(
        PracticeAnswer,
        PracticeQuestion,
        Question,
        Practice
    ).join(
        PracticeQuestion, PracticeAnswer.practice_question_id == PracticeQuestion.id
    ).join(
        Question, PracticeQuestion.question_id == Question.id
    ).join(
        Practice, PracticeQuestion.practice_id == Practice.id
    ).join(
        PracticeSession, PracticeAnswer.practice_session_id == PracticeSession.id
    ).filter(
        and_(
            PracticeSession.user_id == user_id,
            PracticeAnswer.is_correct == False,
            PracticeSession.created_at >= start_date
        )
    )
    
    if course_id:
        recent_wrong_answers = recent_wrong_answers.filter(Practice.course_id == course_id)
    
    recent_wrong_answers = recent_wrong_answers.order_by(
        desc(PracticeAnswer.created_at)
    ).limit(10).all()
    
    # 构建错题数据
    wrong_questions = []
    for answer, practice_question, question, practice in recent_wrong_answers:
        wrong_questions.append({
            'question_id': question.id,
            'practice_id': practice.id,
            'practice_title': practice.title,
            'question_title': question.title,
            'question_type': question.type,
            'user_answer': answer.user_answer,
            'correct_answer': question.correct_answer,
            'answered_at': answer.created_at.isoformat()
        })
    
    return jsonify({
         'period': period,
         'start_date': start_date.isoformat(),
         'end_date': now.isoformat(),
         'statistics': stats,
         'learning_trend': trend_data,
         'recent_wrong_questions': wrong_questions
     }), 200

@practice_statistics_bp.route('/wrong-questions/<user_id>', methods=['GET'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def get_wrong_questions(user_id):
    """
    获取错题集
    
    Args:
        user_id: 用户ID
    
    Query Parameters:
        course_id: 课程ID（可选）
        practice_id: 练习ID（可选）
        question_type: 题目类型（可选）
        limit: 返回记录数限制（可选，默认20）
        offset: 偏移量（可选，默认0）
    
    Returns:
        JSON: 错题集列表
    """
    # 验证用户ID
    if not validate_uuid(user_id):
        return jsonify({'error': '无效的用户ID'}), 400
    
    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 权限检查
    current_user = g.current_user
    if not _can_view_user_stats(current_user, target_user):
        return jsonify({'error': '权限不足'}), 403
    
    # 获取查询参数
    course_id = request.args.get('course_id')
    practice_id = request.args.get('practice_id')
    question_type = request.args.get('question_type')
    limit = min(int(request.args.get('limit', 20)), 50)  # 最大50条
    offset = int(request.args.get('offset', 0))
    
    # 构建查询
    query = db.session.query(
        PracticeAnswer,
        PracticeQuestion,
        Question,
        Practice,
        Course
    ).join(
        PracticeQuestion, PracticeAnswer.practice_question_id == PracticeQuestion.id
    ).join(
        Question, PracticeQuestion.question_id == Question.id
    ).join(
        Practice, PracticeQuestion.practice_id == Practice.id
    ).join(
        Course, Practice.course_id == Course.id
    ).join(
        PracticeSession, PracticeAnswer.practice_session_id == PracticeSession.id
    ).filter(
        and_(
            PracticeSession.user_id == user_id,
            PracticeAnswer.is_correct == False
        )
    )
    
    # 课程过滤
    if course_id:
        if not validate_uuid(course_id):
            return jsonify({'error': '无效的课程ID'}), 400
        query = query.filter(Practice.course_id == course_id)
    
    # 练习过滤
    if practice_id:
        if not validate_uuid(practice_id):
            return jsonify({'error': '无效的练习ID'}), 400
        query = query.filter(Practice.id == practice_id)
    
    # 题目类型过滤
    if question_type:
        query = query.filter(Question.type == question_type)
    
    # 执行查询
    wrong_answers = query.order_by(
        desc(PracticeAnswer.created_at)
    ).offset(offset).limit(limit).all()
    
    # 构建响应数据
    wrong_questions_data = []
    for answer, practice_question, question, practice, course in wrong_answers:
        wrong_questions_data.append({
            'answer_id': answer.id,
            'question_id': question.id,
            'practice_id': practice.id,
            'course_id': course.id,
            'question_title': question.title,
            'question_type': question.type,
            'question_content': question.content,
            'question_options': question.options,
            'correct_answer': question.correct_answer,
            'user_answer': answer.user_answer,
            'explanation': question.explanation,
            'practice_title': practice.title,
            'course_name': course.name,
            'answered_at': answer.created_at.isoformat(),
            'difficulty': question.difficulty if hasattr(question, 'difficulty') else 'medium'
        })
    
    # 获取总数
    total_count = query.count()
    
    # 获取错题统计
    stats_query = db.session.query(
        func.count(PracticeAnswer.id).label('total_wrong'),
        func.count(func.distinct(Question.id)).label('unique_questions'),
        func.count(func.distinct(Practice.id)).label('practices_with_errors')
    ).join(
        PracticeQuestion, PracticeAnswer.practice_question_id == PracticeQuestion.id
    ).join(
        Question, PracticeQuestion.question_id == Question.id
    ).join(
        Practice, PracticeQuestion.practice_id == Practice.id
    ).join(
        PracticeSession, PracticeAnswer.practice_session_id == PracticeSession.id
    ).filter(
        and_(
            PracticeSession.user_id == user_id,
            PracticeAnswer.is_correct == False
        )
    )
    
    if course_id:
        stats_query = stats_query.filter(Practice.course_id == course_id)
    
    stats = stats_query.first()
    
    return jsonify({
        'wrong_questions': wrong_questions_data,
        'statistics': {
            'total_wrong_answers': stats.total_wrong,
            'unique_wrong_questions': stats.unique_questions,
            'practices_with_errors': stats.practices_with_errors
        },
        'pagination': {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }
    }), 200

@practice_statistics_bp.route('/review-practice/<user_id>', methods=['POST'])
@require_auth
@require_permission(Permission.PRACTICE_PARTICIPATE)
def generate_review_practice(user_id):
    """
    生成复习练习
    
    Args:
        user_id: 用户ID
    
    Request Body:
        course_id: 课程ID（可选）
        question_count: 题目数量（可选，默认10，最大20）
        difficulty_filter: 难度过滤（可选：easy/medium/hard）
        question_types: 题目类型列表（可选）
        include_recent_wrong: 是否包含最近错题（可选，默认true）
    
    Returns:
        JSON: 复习练习题目列表
    """
    # 验证用户ID
    if not validate_uuid(user_id):
        return jsonify({'error': '无效的用户ID'}), 400
    
    # 获取目标用户
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 权限检查
    current_user = g.current_user
    if not _can_view_user_stats(current_user, target_user):
        return jsonify({'error': '权限不足'}), 403
    
    # 获取请求数据
    data = request.get_json() or {}
    course_id = data.get('course_id')
    question_count = min(int(data.get('question_count', 10)), 20)  # 最大20题
    difficulty_filter = data.get('difficulty_filter')
    question_types = data.get('question_types', [])
    include_recent_wrong = data.get('include_recent_wrong', True)
    
    # 验证课程ID
    if course_id and not validate_uuid(course_id):
        return jsonify({'error': '无效的课程ID'}), 400
    
    review_questions = []
    
    # 1. 获取错题（如果启用）
    if include_recent_wrong:
        wrong_query = db.session.query(
            Question
        ).join(
            PracticeQuestion, Question.id == PracticeQuestion.question_id
        ).join(
            Practice, PracticeQuestion.practice_id == Practice.id
        ).join(
            PracticeAnswer, PracticeAnswer.practice_question_id == PracticeQuestion.id
        ).join(
            PracticeSession, PracticeAnswer.practice_session_id == PracticeSession.id
        ).filter(
            and_(
                PracticeSession.user_id == user_id,
                PracticeAnswer.is_correct == False
            )
        )
        
        if course_id:
            wrong_query = wrong_query.filter(Practice.course_id == course_id)
        
        if difficulty_filter:
            wrong_query = wrong_query.filter(Question.difficulty == difficulty_filter)
        
        if question_types:
            wrong_query = wrong_query.filter(Question.type.in_(question_types))
        
        # 获取最近的错题，去重
        wrong_questions = wrong_query.distinct().order_by(
            desc(PracticeAnswer.created_at)
        ).limit(question_count // 2).all()  # 错题占一半
        
        review_questions.extend(wrong_questions)
    
    # 2. 补充随机题目
    remaining_count = question_count - len(review_questions)
    if remaining_count > 0:
        # 获取用户已做过的题目ID，避免重复
        answered_question_ids = db.session.query(
            Question.id
        ).join(
            PracticeQuestion, Question.id == PracticeQuestion.question_id
        ).join(
            Practice, PracticeQuestion.practice_id == Practice.id
        ).join(
            PracticeAnswer, PracticeAnswer.practice_question_id == PracticeQuestion.id
        ).join(
            PracticeSession, PracticeAnswer.practice_session_id == PracticeSession.id
        ).filter(
            PracticeSession.user_id == user_id
        )
        
        if course_id:
            answered_question_ids = answered_question_ids.join(
                Practice, PracticeQuestion.practice_id == Practice.id
            ).filter(Practice.course_id == course_id)
        
        answered_ids = [q.id for q in answered_question_ids.all()]
        
        # 构建随机题目查询
        random_query = Question.query
        
        if course_id:
            random_query = random_query.join(
                PracticeQuestion, Question.id == PracticeQuestion.question_id
            ).join(
                Practice, PracticeQuestion.practice_id == Practice.id
            ).filter(Practice.course_id == course_id)
        
        if difficulty_filter:
            random_query = random_query.filter(Question.difficulty == difficulty_filter)
        
        if question_types:
            random_query = random_query.filter(Question.type.in_(question_types))
        
        # 排除已在复习列表中的题目
        exclude_ids = [q.id for q in review_questions] + answered_ids
        if exclude_ids:
            random_query = random_query.filter(~Question.id.in_(exclude_ids))
        
        # 获取随机题目
        available_questions = random_query.all()
        if available_questions:
            random.shuffle(available_questions)
            review_questions.extend(available_questions[:remaining_count])
    
    # 3. 构建响应数据
    review_data = []
    for i, question in enumerate(review_questions):
        review_data.append({
            'order_index': i + 1,
            'question_id': question.id,
            'title': question.title,
            'content': question.content,
            'type': question.type,
            'options': question.options,
            'difficulty': question.difficulty if hasattr(question, 'difficulty') else 'medium',
            'explanation': question.explanation,
            'is_wrong_question': question in review_questions[:len(review_questions) - remaining_count] if include_recent_wrong else False
        })
    
    return jsonify({
        'review_practice': {
            'user_id': user_id,
            'course_id': course_id,
            'total_questions': len(review_data),
            'wrong_questions_count': len(review_questions) - remaining_count if include_recent_wrong else 0,
            'random_questions_count': remaining_count,
            'generated_at': datetime.now().isoformat()
        },
        'questions': review_data
    }), 200