from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import random

from models.question import Question
from models.user import User
from models.database import db

questions_bp = Blueprint('questions', __name__, url_prefix='/api/questions')

def validate_question_type(question_type):
    """验证题目类型"""
    valid_types = ['single_choice', 'multiple_choice', 'fill_blank', 'essay', 'true_false']
    return question_type in valid_types

def validate_difficulty(difficulty):
    """验证难度等级"""
    return difficulty in ['easy', 'medium', 'hard']

def validate_points(points):
    """验证分值"""
    try:
        points = int(points)
        return 1 <= points <= 100
    except (ValueError, TypeError):
        return False

@questions_bp.route('', methods=['GET'])
@jwt_required()
def get_questions():
    """获取题目列表"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以管理题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以访问题目管理',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 获取查询参数
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        question_type = request.args.get('type')
        keyword = request.args.get('keyword')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # 验证参数
        if difficulty and not validate_difficulty(difficulty):
            return jsonify({
                'success': False,
                'message': '难度等级不正确',
                'code': 'INVALID_DIFFICULTY'
            }), 400
        
        if question_type and not validate_question_type(question_type):
            return jsonify({
                'success': False,
                'message': '题目类型不正确',
                'code': 'INVALID_QUESTION_TYPE'
            }), 400
        
        # 搜索题目
        if keyword:
            questions = Question.search_questions(user_id, keyword, category, difficulty, question_type)
        else:
            questions = Question.get_by_teacher(user_id, category, difficulty, question_type)
        
        # 分页处理
        total = len(questions)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_questions = questions[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': {
                'questions': [q.to_dict() for q in paginated_questions],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取题目列表失败: {str(e)}',
            'code': 'GET_QUESTIONS_ERROR'
        }), 500

@questions_bp.route('/<int:question_id>', methods=['GET'])
@jwt_required()
def get_question(question_id):
    """获取题目详情"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看题目详情
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看题目详情',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        question = Question.find_by_id(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': '题目不存在',
                'code': 'QUESTION_NOT_FOUND'
            }), 404
        
        # 检查权限
        if question.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权访问此题目',
                'code': 'ACCESS_DENIED'
            }), 403
        
        return jsonify({
            'success': True,
            'data': {
                'question': question.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取题目详情失败: {str(e)}',
            'code': 'GET_QUESTION_ERROR'
        }), 500

@questions_bp.route('', methods=['POST'])
@jwt_required()
def create_question():
    """创建题目"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以创建题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以创建题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'type', 'difficulty', 'points', 'correct_answer']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        # 验证题目类型
        if not validate_question_type(data['type']):
            return jsonify({
                'success': False,
                'message': '题目类型不正确',
                'code': 'INVALID_QUESTION_TYPE'
            }), 400
        
        # 验证难度等级
        if not validate_difficulty(data['difficulty']):
            return jsonify({
                'success': False,
                'message': '难度等级不正确',
                'code': 'INVALID_DIFFICULTY'
            }), 400
        
        # 验证分值
        if not validate_points(data['points']):
            return jsonify({
                'success': False,
                'message': '分值必须是1-100之间的整数',
                'code': 'INVALID_POINTS'
            }), 400
        
        # 验证选择题选项
        if data['type'] in ['single_choice', 'multiple_choice']:
            if not data.get('options') or len(data['options']) < 2:
                return jsonify({
                    'success': False,
                    'message': '选择题至少需要2个选项',
                    'code': 'INSUFFICIENT_OPTIONS'
                }), 400
        
        # 创建题目
        question = Question(
            teacher_id=user_id,
            title=data['title'],
            content=data.get('content', ''),
            type=data['type'],
            options=json.dumps(data.get('options', [])) if data.get('options') else None,
            correct_answer=data['correct_answer'],
            explanation=data.get('explanation', ''),
            difficulty=data['difficulty'],
            category=data.get('category', ''),
            tags=data.get('tags', ''),
            points=int(data['points']),
            time_limit=data.get('time_limit'),
            status='active'
        )
        question.save()
        
        return jsonify({
            'success': True,
            'message': '题目创建成功',
            'data': {
                'question': question.to_dict()
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建题目失败: {str(e)}',
            'code': 'CREATE_QUESTION_ERROR'
        }), 500

@questions_bp.route('/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    """更新题目"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以更新题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以更新题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        question = Question.find_by_id(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': '题目不存在',
                'code': 'QUESTION_NOT_FOUND'
            }), 404
        
        # 检查权限
        if question.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权修改此题目',
                'code': 'ACCESS_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data and data['title']:
            question.title = data['title']
        
        if 'content' in data:
            question.content = data['content']
        
        if 'type' in data:
            if not validate_question_type(data['type']):
                return jsonify({
                    'success': False,
                    'message': '题目类型不正确',
                    'code': 'INVALID_QUESTION_TYPE'
                }), 400
            question.type = data['type']
        
        if 'options' in data:
            question.options = json.dumps(data['options']) if data['options'] else None
        
        if 'correct_answer' in data and data['correct_answer']:
            question.correct_answer = data['correct_answer']
        
        if 'explanation' in data:
            question.explanation = data['explanation']
        
        if 'difficulty' in data:
            if not validate_difficulty(data['difficulty']):
                return jsonify({
                    'success': False,
                    'message': '难度等级不正确',
                    'code': 'INVALID_DIFFICULTY'
                }), 400
            question.difficulty = data['difficulty']
        
        if 'category' in data:
            question.category = data['category']
        
        if 'tags' in data:
            question.tags = data['tags']
        
        if 'points' in data:
            if not validate_points(data['points']):
                return jsonify({
                    'success': False,
                    'message': '分值必须是1-100之间的整数',
                    'code': 'INVALID_POINTS'
                }), 400
            question.points = int(data['points'])
        
        if 'time_limit' in data:
            question.time_limit = data['time_limit']
        
        # 保存更新
        question.save()
        
        return jsonify({
            'success': True,
            'message': '题目更新成功',
            'data': {
                'question': question.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新题目失败: {str(e)}',
            'code': 'UPDATE_QUESTION_ERROR'
        }), 500

@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    """删除题目（软删除）"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以删除题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以删除题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        question = Question.find_by_id(question_id)
        if not question:
            return jsonify({
                'success': False,
                'message': '题目不存在',
                'code': 'QUESTION_NOT_FOUND'
            }), 404
        
        # 检查权限
        if question.teacher_id != user_id:
            return jsonify({
                'success': False,
                'message': '无权删除此题目',
                'code': 'ACCESS_DENIED'
            }), 403
        
        # 软删除题目
        question.delete()
        
        return jsonify({
            'success': True,
            'message': '题目删除成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除题目失败: {str(e)}',
            'code': 'DELETE_QUESTION_ERROR'
        }), 500

@questions_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """获取题目分类"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看分类
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看题目分类',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        categories = Question.get_categories_by_teacher(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'categories': categories
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取题目分类失败: {str(e)}',
            'code': 'GET_CATEGORIES_ERROR'
        }), 500

@questions_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """获取题目统计信息"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以查看统计
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以查看题目统计',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        statistics = Question.get_statistics(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': statistics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取题目统计失败: {str(e)}',
            'code': 'GET_STATISTICS_ERROR'
        }), 500

@questions_bp.route('/random', methods=['POST'])
@jwt_required()
def get_random_questions():
    """随机获取题目（用于自动组卷）"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以随机获取题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以随机获取题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('difficulty_distribution'):
            return jsonify({
                'success': False,
                'message': '难度分布不能为空',
                'code': 'MISSING_DIFFICULTY_DISTRIBUTION'
            }), 400
        
        difficulty_distribution = data['difficulty_distribution']
        category = data.get('category')
        question_type = data.get('type')
        exclude_ids = data.get('exclude_ids', [])
        
        # 验证难度分布
        for difficulty, count in difficulty_distribution.items():
            if not validate_difficulty(difficulty):
                return jsonify({
                    'success': False,
                    'message': f'难度等级 {difficulty} 不正确',
                    'code': 'INVALID_DIFFICULTY'
                }), 400
            
            if not isinstance(count, int) or count < 0:
                return jsonify({
                    'success': False,
                    'message': f'难度 {difficulty} 的题目数量必须是非负整数',
                    'code': 'INVALID_COUNT'
                }), 400
        
        # 验证题目类型
        if question_type and not validate_question_type(question_type):
            return jsonify({
                'success': False,
                'message': '题目类型不正确',
                'code': 'INVALID_QUESTION_TYPE'
            }), 400
        
        # 随机获取题目
        questions = Question.get_random_questions(
            user_id, difficulty_distribution, category, question_type, exclude_ids
        )
        
        # 计算总分
        total_points = sum(q.points for q in questions)
        
        return jsonify({
            'success': True,
            'data': {
                'questions': [q.to_dict() for q in questions],
                'total_points': total_points,
                'count': len(questions)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'随机获取题目失败: {str(e)}',
            'code': 'GET_RANDOM_QUESTIONS_ERROR'
        }), 500

@questions_bp.route('/batch', methods=['POST'])
@jwt_required()
def create_questions_batch():
    """批量创建题目"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以批量创建题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以批量创建题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        if not data.get('questions') or not isinstance(data['questions'], list):
            return jsonify({
                'success': False,
                'message': '题目列表不能为空',
                'code': 'MISSING_QUESTIONS'
            }), 400
        
        questions_data = data['questions']
        created_questions = []
        errors = []
        
        for i, question_data in enumerate(questions_data):
            try:
                # 验证必填字段
                required_fields = ['title', 'type', 'difficulty', 'points', 'correct_answer']
                for field in required_fields:
                    if not question_data.get(field):
                        errors.append(f'第{i+1}题: {field}不能为空')
                        continue
                
                # 验证题目类型
                if not validate_question_type(question_data['type']):
                    errors.append(f'第{i+1}题: 题目类型不正确')
                    continue
                
                # 验证难度等级
                if not validate_difficulty(question_data['difficulty']):
                    errors.append(f'第{i+1}题: 难度等级不正确')
                    continue
                
                # 验证分值
                if not validate_points(question_data['points']):
                    errors.append(f'第{i+1}题: 分值必须是1-100之间的整数')
                    continue
                
                # 创建题目
                question = Question(
                    teacher_id=user_id,
                    title=question_data['title'],
                    content=question_data.get('content', ''),
                    type=question_data['type'],
                    options=json.dumps(question_data.get('options', [])) if question_data.get('options') else None,
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data.get('explanation', ''),
                    difficulty=question_data['difficulty'],
                    category=question_data.get('category', ''),
                    tags=question_data.get('tags', ''),
                    points=int(question_data['points']),
                    time_limit=question_data.get('time_limit'),
                    status='active'
                )
                question.save()
                created_questions.append(question.to_dict())
                
            except Exception as e:
                errors.append(f'第{i+1}题: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': f'批量创建完成，成功{len(created_questions)}题，失败{len(errors)}题',
            'data': {
                'created_questions': created_questions,
                'errors': errors,
                'success_count': len(created_questions),
                'error_count': len(errors)
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量创建题目失败: {str(e)}',
            'code': 'BATCH_CREATE_QUESTIONS_ERROR'
        }), 500

@questions_bp.route('/auto-generate', methods=['POST'])
@jwt_required()
def auto_generate_questions():
    """自动生成题目"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # 只有教师可以自动生成题目
        if user.role != 'teacher':
            return jsonify({
                'success': False,
                'message': '只有教师可以自动生成题目',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['topic', 'difficulty', 'count']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}不能为空',
                    'code': 'MISSING_FIELD'
                }), 400
        
        topic = data['topic']
        difficulty = data['difficulty']
        count = int(data['count'])
        
        # 验证难度等级
        if not validate_difficulty(difficulty):
            return jsonify({
                'success': False,
                'message': '难度等级不正确',
                'code': 'INVALID_DIFFICULTY'
            }), 400
        
        # 验证生成数量
        if count <= 0 or count > 50:
            return jsonify({
                'success': False,
                'message': '生成数量必须在1-50之间',
                'code': 'INVALID_COUNT'
            }), 400
        
        # 模拟自动生成题目（实际项目中可以接入AI生成服务）
        generated_questions = []
        question_types = ['single_choice', 'multiple_choice', 'fill_blank', 'essay']
        
        for i in range(count):
            question_type = random.choice(question_types)
            
            # 生成基础题目数据
            question_data = {
                'title': f'{topic}相关题目{i+1}',
                'content': f'这是一道关于{topic}的{difficulty}难度题目。',
                'type': question_type,
                'difficulty': difficulty,
                'category': topic,
                'points': random.randint(5, 20),
                'explanation': f'这道题考查的是{topic}的相关知识点。'
            }
            
            # 根据题目类型生成选项和答案
            if question_type in ['single_choice', 'multiple_choice']:
                options = [f'选项A: {topic}相关内容A', f'选项B: {topic}相关内容B', 
                          f'选项C: {topic}相关内容C', f'选项D: {topic}相关内容D']
                question_data['options'] = options
                question_data['correct_answer'] = 'A'
            else:
                question_data['correct_answer'] = f'{topic}的标准答案'
            
            # 创建题目
            question = Question(
                teacher_id=user_id,
                title=question_data['title'],
                content=question_data['content'],
                type=question_data['type'],
                options=json.dumps(question_data.get('options', [])) if question_data.get('options') else None,
                correct_answer=question_data['correct_answer'],
                explanation=question_data['explanation'],
                difficulty=question_data['difficulty'],
                category=question_data['category'],
                tags=topic,
                points=question_data['points'],
                status='active'
            )
            question.save()
            generated_questions.append(question.to_dict())
        
        return jsonify({
            'success': True,
            'message': f'成功生成{len(generated_questions)}道题目',
            'data': {
                'questions': generated_questions,
                'count': len(generated_questions)
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'自动生成题目失败: {str(e)}',
            'code': 'AUTO_GENERATE_ERROR'
        }), 500