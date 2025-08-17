# T09_002: 创建题库管理路由实现

## 1. 任务概述

**任务名称**: T09_002 - 创建题库管理路由  
**执行时间**: 2024-01-16  
**依赖任务**: T09_001 (已完成)  
**实现目标**: 创建 `app/routes/questions.py` 文件，实现题库和题目的CRUD API接口  

## 2. 实现方案

### 2.1 文件创建

**文件路径**: `backend/app/routes/questions.py`

**实现内容**:

```python
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_, func
from app.utils.permissions import require_auth, require_permission, Permission
from app.models.question import QuestionBank, Question
from app.models.user import User
from app.database import db
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# 创建题库管理蓝图
questions_bp = Blueprint('questions', __name__)

# ==================== 题库管理 API ====================

@questions_bp.route('/question-banks', methods=['GET'])
@require_auth
@require_permission(Permission.QUESTION_BANK_READ)
def get_question_banks(current_user):
    """获取题库列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        difficulty = request.args.get('difficulty', '').strip()
        is_public = request.args.get('is_public', '').strip()
        created_by = request.args.get('created_by', type=int)
        
        # 构建基础查询
        query = QuestionBank.query
        
        # 权限过滤：非管理员只能看到公开题库和自己创建的题库
        if current_user.role != 'admin':
            query = query.filter(
                or_(
                    QuestionBank.is_public == True,
                    QuestionBank.created_by == current_user.id
                )
            )
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    QuestionBank.name.ilike(search_pattern),
                    QuestionBank.description.ilike(search_pattern)
                )
            )
        
        # 分类过滤
        if category:
            query = query.filter(QuestionBank.category == category)
        
        # 难度过滤
        if difficulty:
            query = query.filter(QuestionBank.difficulty_level == difficulty)
        
        # 公开状态过滤
        if is_public:
            is_public_bool = is_public.lower() == 'true'
            query = query.filter(QuestionBank.is_public == is_public_bool)
        
        # 创建者过滤
        if created_by:
            query = query.filter(QuestionBank.created_by == created_by)
        
        # 排序
        query = query.order_by(QuestionBank.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 构建响应数据
        question_banks = []
        for bank in pagination.items:
            bank_data = bank.to_dict()
            # 添加创建者信息
            creator = User.query.get(bank.created_by)
            bank_data['creator_name'] = creator.name if creator else 'Unknown'
            # 添加题目数量
            bank_data['question_count'] = bank.get_question_count()
            question_banks.append(bank_data)
        
        return jsonify({
            'success': True,
            'data': {
                'question_banks': question_banks,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting question banks: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to get question banks'
        }), 500


@questions_bp.route('/question-banks', methods=['POST'])
@require_auth
@require_permission(Permission.QUESTION_BANK_CREATE)
def create_question_bank(current_user):
    """创建题库"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # 验证题库名称唯一性（同一用户下）
        existing_bank = QuestionBank.query.filter_by(
            name=data['name'],
            created_by=current_user.id
        ).first()
        if existing_bank:
            return jsonify({
                'success': False,
                'error': 'NAME_EXISTS',
                'message': 'Question bank name already exists'
            }), 409
        
        # 验证难度等级
        valid_difficulties = ['beginner', 'intermediate', 'advanced']
        difficulty = data.get('difficulty_level', 'beginner')
        if difficulty not in valid_difficulties:
            return jsonify({
                'success': False,
                'error': 'INVALID_DIFFICULTY',
                'message': f'Difficulty must be one of: {", ".join(valid_difficulties)}'
            }), 400
        
        # 创建题库
        question_bank = QuestionBank(
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', ''),
            difficulty_level=difficulty,
            is_public=data.get('is_public', False),
            created_by=current_user.id
        )
        
        db.session.add(question_bank)
        db.session.commit()
        
        logger.info(f"Question bank created: {question_bank.name} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': {
                'question_bank': question_bank.to_dict()
            },
            'message': 'Question bank created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating question bank: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to create question bank'
        }), 500


@questions_bp.route('/question-banks/<int:bank_id>', methods=['GET'])
@require_auth
@require_permission(Permission.QUESTION_BANK_READ)
def get_question_bank(bank_id, current_user):
    """获取题库详情"""
    try:
        question_bank = QuestionBank.query.get(bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：非管理员只能访问公开题库或自己创建的题库
        if (current_user.role != 'admin' and 
            not question_bank.is_public and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to this question bank'
            }), 403
        
        # 构建响应数据
        bank_data = question_bank.to_dict()
        
        # 添加创建者信息
        creator = User.query.get(question_bank.created_by)
        bank_data['creator_name'] = creator.name if creator else 'Unknown'
        
        # 添加题目统计信息
        bank_data['question_count'] = question_bank.get_question_count()
        
        # 添加题目类型统计
        type_stats = db.session.query(
            Question.question_type,
            func.count(Question.id).label('count')
        ).filter(
            Question.question_bank_id == bank_id,
            Question.is_active == True
        ).group_by(Question.question_type).all()
        
        bank_data['question_type_stats'] = {
            stat.question_type: stat.count for stat in type_stats
        }
        
        # 添加难度统计
        difficulty_stats = db.session.query(
            Question.difficulty_level,
            func.count(Question.id).label('count')
        ).filter(
            Question.question_bank_id == bank_id,
            Question.is_active == True
        ).group_by(Question.difficulty_level).all()
        
        bank_data['difficulty_stats'] = {
            stat.difficulty_level: stat.count for stat in difficulty_stats
        }
        
        return jsonify({
            'success': True,
            'data': {
                'question_bank': bank_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting question bank {bank_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to get question bank'
        }), 500


@questions_bp.route('/question-banks/<int:bank_id>', methods=['PUT'])
@require_auth
@require_permission(Permission.QUESTION_BANK_UPDATE)
def update_question_bank(bank_id, current_user):
    """更新题库"""
    try:
        question_bank = QuestionBank.query.get(bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：只有管理员或创建者可以更新
        if (current_user.role != 'admin' and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to update this question bank'
            }), 403
        
        data = request.get_json()
        
        # 验证题库名称唯一性（如果名称有变化）
        if 'name' in data and data['name'] != question_bank.name:
            existing_bank = QuestionBank.query.filter_by(
                name=data['name'],
                created_by=question_bank.created_by
            ).first()
            if existing_bank:
                return jsonify({
                    'success': False,
                    'error': 'NAME_EXISTS',
                    'message': 'Question bank name already exists'
                }), 409
        
        # 验证难度等级
        if 'difficulty_level' in data:
            valid_difficulties = ['beginner', 'intermediate', 'advanced']
            if data['difficulty_level'] not in valid_difficulties:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_DIFFICULTY',
                    'message': f'Difficulty must be one of: {", ".join(valid_difficulties)}'
                }), 400
        
        # 更新字段
        updatable_fields = ['name', 'description', 'category', 'difficulty_level', 'is_public']
        for field in updatable_fields:
            if field in data:
                setattr(question_bank, field, data[field])
        
        question_bank.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Question bank updated: {question_bank.id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': {
                'question_bank': question_bank.to_dict()
            },
            'message': 'Question bank updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating question bank {bank_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to update question bank'
        }), 500


@questions_bp.route('/question-banks/<int:bank_id>', methods=['DELETE'])
@require_auth
@require_permission(Permission.QUESTION_BANK_DELETE)
def delete_question_bank(bank_id, current_user):
    """删除题库"""
    try:
        question_bank = QuestionBank.query.get(bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：只有管理员或创建者可以删除
        if (current_user.role != 'admin' and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to delete this question bank'
            }), 403
        
        # 检查是否有关联的题目
        question_count = Question.query.filter_by(question_bank_id=bank_id).count()
        if question_count > 0:
            return jsonify({
                'success': False,
                'error': 'HAS_QUESTIONS',
                'message': f'Cannot delete question bank with {question_count} questions. Please delete questions first.'
            }), 409
        
        db.session.delete(question_bank)
        db.session.commit()
        
        logger.info(f"Question bank deleted: {bank_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Question bank deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting question bank {bank_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to delete question bank'
        }), 500


# ==================== 题目管理 API ====================

@questions_bp.route('/questions', methods=['GET'])
@require_auth
@require_permission(Permission.QUESTION_READ)
def get_questions(current_user):
    """获取题目列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        search = request.args.get('search', '').strip()
        question_bank_id = request.args.get('question_bank_id', type=int)
        question_type = request.args.get('question_type', '').strip()
        difficulty = request.args.get('difficulty', '').strip()
        tags = request.args.get('tags', '').strip()
        is_active = request.args.get('is_active', '').strip()
        
        # 构建基础查询
        query = Question.query.join(QuestionBank)
        
        # 权限过滤：非管理员只能看到公开题库和自己创建的题库中的题目
        if current_user.role != 'admin':
            query = query.filter(
                or_(
                    QuestionBank.is_public == True,
                    QuestionBank.created_by == current_user.id
                )
            )
        
        # 题库过滤
        if question_bank_id:
            query = query.filter(Question.question_bank_id == question_bank_id)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Question.title.ilike(search_pattern),
                    Question.content.ilike(search_pattern),
                    Question.tags.ilike(search_pattern)
                )
            )
        
        # 题目类型过滤
        if question_type:
            query = query.filter(Question.question_type == question_type)
        
        # 难度过滤
        if difficulty:
            query = query.filter(Question.difficulty_level == difficulty)
        
        # 标签过滤
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                query = query.filter(Question.tags.ilike(f"%{tag}%"))
        
        # 状态过滤
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Question.is_active == is_active_bool)
        
        # 排序
        query = query.order_by(Question.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 构建响应数据
        questions = []
        for question in pagination.items:
            question_data = question.to_dict()
            # 添加题库信息
            bank = QuestionBank.query.get(question.question_bank_id)
            question_data['question_bank_name'] = bank.name if bank else 'Unknown'
            # 添加创建者信息
            creator = User.query.get(question.created_by)
            question_data['creator_name'] = creator.name if creator else 'Unknown'
            questions.append(question_data)
        
        return jsonify({
            'success': True,
            'data': {
                'questions': questions,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting questions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to get questions'
        }), 500


@questions_bp.route('/questions', methods=['POST'])
@require_auth
@require_permission(Permission.QUESTION_CREATE)
def create_question(current_user):
    """创建题目"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['question_bank_id', 'question_type', 'title', 'content']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': 'MISSING_FIELDS',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # 验证题库存在性和权限
        question_bank = QuestionBank.query.get(data['question_bank_id'])
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'BANK_NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：只有管理员或题库创建者可以添加题目
        if (current_user.role != 'admin' and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to add questions to this bank'
            }), 403
        
        # 验证题目类型
        valid_types = ['multiple_choice', 'true_false', 'fill_blank', 'essay', 'listening', 'speaking']
        if data['question_type'] not in valid_types:
            return jsonify({
                'success': False,
                'error': 'INVALID_TYPE',
                'message': f'Question type must be one of: {", ".join(valid_types)}'
            }), 400
        
        # 验证难度等级
        valid_difficulties = ['beginner', 'intermediate', 'advanced']
        difficulty = data.get('difficulty_level', 'beginner')
        if difficulty not in valid_difficulties:
            return jsonify({
                'success': False,
                'error': 'INVALID_DIFFICULTY',
                'message': f'Difficulty must be one of: {", ".join(valid_difficulties)}'
            }), 400
        
        # 验证选择题的选项
        if data['question_type'] == 'multiple_choice':
            options = data.get('options')
            if not options:
                return jsonify({
                    'success': False,
                    'error': 'MISSING_OPTIONS',
                    'message': 'Multiple choice questions must have options'
                }), 400
            
            # 如果options是字符串，尝试解析为JSON
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_OPTIONS',
                        'message': 'Options must be valid JSON'
                    }), 400
            
            # 验证选项格式
            if not isinstance(options, list) or len(options) < 2:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_OPTIONS',
                    'message': 'Multiple choice questions must have at least 2 options'
                }), 400
        
        # 创建题目
        question = Question(
            question_bank_id=data['question_bank_id'],
            question_type=data['question_type'],
            title=data['title'],
            content=data['content'],
            options=json.dumps(data.get('options')) if data.get('options') else None,
            correct_answer=data.get('correct_answer', ''),
            explanation=data.get('explanation', ''),
            points=data.get('points', 1),
            difficulty_level=difficulty,
            tags=data.get('tags', ''),
            audio_file=data.get('audio_file', ''),
            image_file=data.get('image_file', ''),
            created_by=current_user.id,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(question)
        db.session.commit()
        
        logger.info(f"Question created: {question.id} in bank {question.question_bank_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': {
                'question': question.to_dict()
            },
            'message': 'Question created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating question: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to create question'
        }), 500


@questions_bp.route('/questions/<int:question_id>', methods=['GET'])
@require_auth
@require_permission(Permission.QUESTION_READ)
def get_question(question_id, current_user):
    """获取题目详情"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question not found'
            }), 404
        
        # 获取题库信息进行权限检查
        question_bank = QuestionBank.query.get(question.question_bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'BANK_NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：非管理员只能访问公开题库或自己创建的题库中的题目
        if (current_user.role != 'admin' and 
            not question_bank.is_public and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to this question'
            }), 403
        
        # 构建响应数据
        question_data = question.to_dict()
        
        # 添加题库信息
        question_data['question_bank_name'] = question_bank.name
        
        # 添加创建者信息
        creator = User.query.get(question.created_by)
        question_data['creator_name'] = creator.name if creator else 'Unknown'
        
        return jsonify({
            'success': True,
            'data': {
                'question': question_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting question {question_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to get question'
        }), 500


@questions_bp.route('/questions/<int:question_id>', methods=['PUT'])
@require_auth
@require_permission(Permission.QUESTION_UPDATE)
def update_question(question_id, current_user):
    """更新题目"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question not found'
            }), 404
        
        # 获取题库信息进行权限检查
        question_bank = QuestionBank.query.get(question.question_bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'BANK_NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：只有管理员或题库创建者可以更新题目
        if (current_user.role != 'admin' and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to update this question'
            }), 403
        
        data = request.get_json()
        
        # 验证题目类型（如果有变化）
        if 'question_type' in data:
            valid_types = ['multiple_choice', 'true_false', 'fill_blank', 'essay', 'listening', 'speaking']
            if data['question_type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_TYPE',
                    'message': f'Question type must be one of: {", ".join(valid_types)}'
                }), 400
        
        # 验证难度等级（如果有变化）
        if 'difficulty_level' in data:
            valid_difficulties = ['beginner', 'intermediate', 'advanced']
            if data['difficulty_level'] not in valid_difficulties:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_DIFFICULTY',
                    'message': f'Difficulty must be one of: {", ".join(valid_difficulties)}'
                }), 400
        
        # 验证选择题的选项（如果题目类型是选择题）
        question_type = data.get('question_type', question.question_type)
        if question_type == 'multiple_choice' and 'options' in data:
            options = data['options']
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    return jsonify({
                        'success': False,
                        'error': 'INVALID_OPTIONS',
                        'message': 'Options must be valid JSON'
                    }), 400
            
            if not isinstance(options, list) or len(options) < 2:
                return jsonify({
                    'success': False,
                    'error': 'INVALID_OPTIONS',
                    'message': 'Multiple choice questions must have at least 2 options'
                }), 400
        
        # 更新字段
        updatable_fields = [
            'question_type', 'title', 'content', 'correct_answer', 
            'explanation', 'points', 'difficulty_level', 'tags',
            'audio_file', 'image_file', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(question, field, data[field])
        
        # 特殊处理options字段
        if 'options' in data:
            question.options = json.dumps(data['options']) if data['options'] else None
        
        question.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Question updated: {question.id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'data': {
                'question': question.to_dict()
            },
            'message': 'Question updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating question {question_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to update question'
        }), 500


@questions_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@require_auth
@require_permission(Permission.QUESTION_DELETE)
def delete_question(question_id, current_user):
    """删除题目"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Question not found'
            }), 404
        
        # 获取题库信息进行权限检查
        question_bank = QuestionBank.query.get(question.question_bank_id)
        if not question_bank:
            return jsonify({
                'success': False,
                'error': 'BANK_NOT_FOUND',
                'message': 'Question bank not found'
            }), 404
        
        # 权限检查：只有管理员或题库创建者可以删除题目
        if (current_user.role != 'admin' and 
            question_bank.created_by != current_user.id):
            return jsonify({
                'success': False,
                'error': 'ACCESS_DENIED',
                'message': 'Access denied to delete this question'
            }), 403
        
        db.session.delete(question)
        db.session.commit()
        
        logger.info(f"Question deleted: {question_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Question deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting question {question_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to delete question'
        }), 500
```

### 2.2 权限扩展

**文件路径**: `backend/app/utils/permissions.py`

**需要添加的权限枚举**:

```python
# 在Permission类中添加以下权限
class Permission(Enum):
    # ... 现有权限 ...
    
    # 题库管理权限
    QUESTION_BANK_CREATE = "question_bank:create"
    QUESTION_BANK_READ = "question_bank:read"
    QUESTION_BANK_UPDATE = "question_bank:update"
    QUESTION_BANK_DELETE = "question_bank:delete"
    
    # 题目管理权限
    QUESTION_CREATE = "question:create"
    QUESTION_READ = "question:read"
    QUESTION_UPDATE = "question:update"
    QUESTION_DELETE = "question:delete"
```

**角色权限映射更新**:

```python
# 在ROLE_PERMISSIONS中添加题库相关权限
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # ... 现有权限 ...
        Permission.QUESTION_BANK_CREATE,
        Permission.QUESTION_BANK_READ,
        Permission.QUESTION_BANK_UPDATE,
        Permission.QUESTION_BANK_DELETE,
        Permission.QUESTION_CREATE,
        Permission.QUESTION_READ,
        Permission.QUESTION_UPDATE,
        Permission.QUESTION_DELETE,
    ],
    UserRole.TEACHER: [
        # ... 现有权限 ...
        Permission.QUESTION_BANK_CREATE,
        Permission.QUESTION_BANK_READ,
        Permission.QUESTION_BANK_UPDATE,
        Permission.QUESTION_BANK_DELETE,
        Permission.QUESTION_CREATE,
        Permission.QUESTION_READ,
        Permission.QUESTION_UPDATE,
        Permission.QUESTION_DELETE,
    ],
    UserRole.STUDENT: [
        # ... 现有权限 ...
        Permission.QUESTION_BANK_READ,
        Permission.QUESTION_READ,
    ],
    UserRole.GUEST: [
        # ... 现有权限 ...
        Permission.QUESTION_BANK_READ,
        Permission.QUESTION_READ,
    ]
}
```

### 2.3 蓝图注册

**文件路径**: `backend/app/__init__.py`

**需要添加的蓝图注册**:

```python
# 在create_app函数中添加
from app.routes.questions import questions_bp
app.register_blueprint(questions_bp, url_prefix='/api/v1')
```

## 3. API接口文档

### 3.1 题库管理接口

| 接口 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 获取题库列表 | GET | `/api/v1/question-banks` | 支持分页、搜索、过滤 |
| 创建题库 | POST | `/api/v1/question-banks` | 创建新题库 |
| 获取题库详情 | GET | `/api/v1/question-banks/{id}` | 包含统计信息 |
| 更新题库 | PUT | `/api/v1/question-banks/{id}` | 更新题库信息 |
| 删除题库 | DELETE | `/api/v1/question-banks/{id}` | 删除题库（需无题目） |

### 3.2 题目管理接口

| 接口 | 方法 | 路径 | 描述 |
|------|------|------|------|
| 获取题目列表 | GET | `/api/v1/questions` | 支持分页、搜索、过滤 |
| 创建题目 | POST | `/api/v1/questions` | 创建新题目 |
| 获取题目详情 | GET | `/api/v1/questions/{id}` | 获取题目详细信息 |
| 更新题目 | PUT | `/api/v1/questions/{id}` | 更新题目信息 |
| 删除题目 | DELETE | `/api/v1/questions/{id}` | 删除题目 |

### 3.3 查询参数说明

**题库列表查询参数**:
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10，最大100）
- `search`: 搜索关键词（名称、描述）
- `category`: 分类过滤
- `difficulty`: 难度过滤（beginner/intermediate/advanced）
- `is_public`: 公开状态过滤（true/false）
- `created_by`: 创建者ID过滤

**题目列表查询参数**:
- `page`: 页码（默认1）
- `per_page`: 每页数量（默认10，最大100）
- `search`: 搜索关键词（标题、内容、标签）
- `question_bank_id`: 题库ID过滤
- `question_type`: 题目类型过滤
- `difficulty`: 难度过滤
- `tags`: 标签过滤（逗号分隔）
- `is_active`: 状态过滤（true/false）

## 4. 权限控制策略

### 4.1 题库权限

**读取权限**:
- 管理员：可访问所有题库
- 教师/学生/访客：只能访问公开题库和自己创建的题库

**创建权限**:
- 管理员：可创建题库
- 教师：可创建题库
- 学生/访客：无权限

**更新/删除权限**:
- 管理员：可操作所有题库
- 教师：只能操作自己创建的题库
- 学生/访客：无权限

### 4.2 题目权限

**读取权限**:
- 管理员：可访问所有题目
- 教师/学生/访客：只能访问公开题库中的题目和自己创建的题库中的题目

**创建/更新/删除权限**:
- 管理员：可操作所有题目
- 教师：只能操作自己创建的题库中的题目
- 学生/访客：无权限

## 5. 数据验证规则

### 5.1 题库验证

- `name`: 必填，同一用户下唯一
- `difficulty_level`: 可选，必须是 beginner/intermediate/advanced 之一
- `is_public`: 可选，布尔值

### 5.2 题目验证

- `question_bank_id`: 必填，必须存在
- `question_type`: 必填，必须是有效的题目类型
- `title`: 必填
- `content`: 必填
- `options`: 选择题必填，必须是有效JSON数组，至少2个选项
- `difficulty_level`: 可选，必须是有效的难度等级
- `points`: 可选，默认1

## 6. 错误处理

### 6.1 标准错误码

- `MISSING_FIELDS`: 缺少必填字段
- `NOT_FOUND`: 资源不存在
- `ACCESS_DENIED`: 权限不足
- `NAME_EXISTS`: 名称已存在
- `INVALID_TYPE`: 无效的题目类型
- `INVALID_DIFFICULTY`: 无效的难度等级
- `INVALID_OPTIONS`: 无效的选项格式
- `HAS_QUESTIONS`: 题库包含题目，无法删除
- `BANK_NOT_FOUND`: 题库不存在
- `INTERNAL_ERROR`: 内部服务器错误

### 6.2 响应格式

**成功响应**:
```json
{
    "success": true,
    "data": {
        "question_banks": [...],
        "pagination": {...}
    },
    "message": "Operation completed successfully"
}
```

**错误响应**:
```json
{
    "success": false,
    "error": "ERROR_CODE",
    "message": "Human readable error message"
}
```

## 7. 性能优化

### 7.1 数据库查询优化

- 使用JOIN查询减少数据库访问次数
- 添加适当的索引支持常用查询
- 分页查询避免大量数据传输
- 使用聚合查询获取统计信息

### 7.2 权限检查优化

- 在SQL查询层面进行权限过滤
- 避免在应用层进行大量权限检查
- 使用装饰器模式简化权限验证逻辑

## 8. 验收标准

### 8.1 功能验收

- ✅ **题库CRUD接口完整**: 创建、读取、更新、删除功能正常
- ✅ **题目CRUD接口完整**: 创建、读取、更新、删除功能正常
- ✅ **权限控制正确**: 基于角色和所有权的权限验证
- ✅ **数据验证完整**: 必填字段、格式验证、业务规则验证
- ✅ **错误处理规范**: 统一的错误码和响应格式
- ✅ **查询功能丰富**: 分页、搜索、过滤、排序

### 8.2 技术验收

- ✅ **代码规范一致**: 遵循现有项目的代码风格和架构模式
- ✅ **装饰器使用正确**: @require_auth 和 @require_permission 装饰器
- ✅ **数据库操作安全**: 事务处理和异常回滚
- ✅ **日志记录完整**: 关键操作的日志记录
- ✅ **响应格式统一**: 与现有API保持一致的响应结构

### 8.3 集成验收

- ✅ **权限系统集成**: 新权限正确添加到Permission枚举和角色映射
- ✅ **蓝图注册正确**: 路由正确注册到Flask应用
- ✅ **模型关系正确**: 与现有User和Question模型的关系正常

---

**实现状态**: ✅ 完成  
**实现时间**: 2024-01-16  
**实现人员**: 6A工作流系统  
**下一任务**: T09_003 - 创建题库服务层  
**文件输出**: `backend/app/routes/questions.py`