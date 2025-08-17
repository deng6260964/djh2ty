from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import json
from sqlalchemy import or_, and_, func
from app.database import db
from app.models.practice import Practice
from app.models.practice_question import PracticeQuestion
from app.models.practice_session import PracticeSession
from app.models.practice_answer import PracticeAnswer
from app.models.question import Question
from app.models.user import User
from app.models.course import Course
from app.utils.permissions import (
    require_permission,
    require_auth,
    Permission,
)
from app.utils.validation import validate_uuid

practices_bp = Blueprint("practices", __name__)

# ==================== 练习管理API ====================


@practices_bp.route("/", methods=["GET"], strict_slashes=False)
@require_auth
def get_practices(current_user=None):
    """获取练习列表"""
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        course_id = request.args.get("course_id", type=int)
        status = request.args.get("status")
        search = request.args.get("search", "").strip()
        is_public = request.args.get("is_public", type=bool)

        # 构建查询
        query = Practice.query

        # 权限过滤
        if current_user.role == "student":
            # 学生只能看到已发布的练习
            query = query.filter(Practice.status == "published")
        elif current_user.role == "teacher":
            # 教师可以看到自己创建的练习
            query = query.filter(Practice.creator_id == current_user.id)
        # 管理员可以看到所有练习

        # 课程过滤
        if course_id:
            query = query.filter(Practice.course_id == course_id)

        # 状态过滤
        if status:
            valid_statuses = ["draft", "published", "archived"]
            if status in valid_statuses:
                query = query.filter(Practice.status == status)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Practice.title.ilike(f"%{search}%"),
                    Practice.description.ilike(f"%{search}%"),
                )
            )

        # 排序
        query = query.order_by(Practice.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        practices = [practice.to_dict() for practice in pagination.items]

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "practices": practices,
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
                    "message": f"获取练习列表失败: {str(e)}",
                }
            ),
            500,
         )


@practices_bp.route("/<practice_id>/questions/reorder", methods=["PUT"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def reorder_practice_questions(practice_id, current_user=None):
    """调整练习题目顺序"""
    try:
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

        # 权限检查：只有创建者可以调整题目顺序
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能修改自己创建的练习",
                    }
                ),
                403,
            )

        data = request.get_json()
        if not data or "question_orders" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空或缺少题目顺序列表",
                    }
                ),
                400,
            )

        question_orders = data["question_orders"]
        if not isinstance(question_orders, list) or len(question_orders) == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "题目顺序列表不能为空",
                    }
                ),
                400,
            )

        # 验证数据格式
        for item in question_orders:
            if not isinstance(item, dict) or "practice_question_id" not in item or "order_index" not in item:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_DATA",
                            "message": "每个题目顺序项必须包含practice_question_id和order_index",
                        }
                    ),
                    400,
                )

        # 获取所有相关的练习题目
        practice_question_ids = [item["practice_question_id"] for item in question_orders]
        practice_questions = PracticeQuestion.query.filter(
            PracticeQuestion.id.in_(practice_question_ids),
            PracticeQuestion.practice_id == practice_id
        ).all()

        if len(practice_questions) != len(practice_question_ids):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_QUESTION_NOT_FOUND",
                        "message": "部分练习题目不存在",
                    }
                ),
                404,
            )

        # 验证顺序索引的唯一性和连续性
        order_indices = [item["order_index"] for item in question_orders]
        if len(set(order_indices)) != len(order_indices):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_ORDER",
                        "message": "题目顺序索引不能重复",
                    }
                ),
                400,
            )

        # 更新题目顺序
        for item in question_orders:
            practice_question = next(
                pq for pq in practice_questions 
                if pq.id == item["practice_question_id"]
            )
            practice_question.order_index = item["order_index"]

        db.session.commit()

        # 返回更新后的题目列表
        updated_questions = []
        for pq in sorted(practice_questions, key=lambda x: x.order_index):
            question = Question.query.get(pq.question_id)
            question_data = question.to_dict()
            question_data.update(
                {
                    "practice_question_id": pq.id,
                    "order_index": pq.order_index,
                    "points": pq.points,
                    "is_required": pq.is_required,
                }
            )
            updated_questions.append(question_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"questions": updated_questions},
                    "message": "题目顺序调整成功",
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
                    "message": f"调整题目顺序失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>/questions/<practice_question_id>/config", methods=["PUT"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def update_practice_question_config(practice_id, practice_question_id, current_user=None):
    """更新练习题目配置"""
    try:
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

        # 权限检查：只有创建者可以更新题目配置
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能修改自己创建的练习",
                    }
                ),
                403,
            )

        practice_question = PracticeQuestion.query.filter_by(
            id=practice_question_id, practice_id=practice_id
        ).first()
        if not practice_question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_QUESTION_NOT_FOUND",
                        "message": "练习题目不存在",
                    }
                ),
                404,
            )

        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空",
                    }
                ),
                400,
            )

        # 更新配置字段
        if "points" in data:
            points = data["points"]
            if not isinstance(points, (int, float)) or points <= 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_POINTS",
                            "message": "分值必须是大于0的数字",
                        }
                    ),
                    400,
                )
            practice_question.points = points

        if "is_required" in data:
            is_required = data["is_required"]
            if not isinstance(is_required, bool):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_REQUIRED",
                            "message": "is_required必须是布尔值",
                        }
                    ),
                    400,
                )
            practice_question.is_required = is_required

        if "order_index" in data:
            order_index = data["order_index"]
            if not isinstance(order_index, int) or order_index <= 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_ORDER",
                            "message": "排序索引必须是大于0的整数",
                        }
                    ),
                    400,
                )
            
            # 检查排序索引是否与其他题目冲突
            existing_question = PracticeQuestion.query.filter(
                PracticeQuestion.practice_id == practice_id,
                PracticeQuestion.order_index == order_index,
                PracticeQuestion.id != practice_question_id
            ).first()
            if existing_question:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ORDER_CONFLICT",
                            "message": f"排序索引 {order_index} 已被其他题目使用",
                        }
                    ),
                    400,
                )
            practice_question.order_index = order_index

        db.session.commit()

        # 返回更新后的题目信息
        question = Question.query.get(practice_question.question_id)
        question_data = question.to_dict()
        question_data.update(
            {
                "practice_question_id": practice_question.id,
                "order_index": practice_question.order_index,
                "points": practice_question.points,
                "is_required": practice_question.is_required,
            }
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question": question_data},
                    "message": "题目配置更新成功",
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
                    "message": f"更新题目配置失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/", methods=["POST"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_CREATE)  # 复用考试创建权限
def create_practice(current_user=None):
    """创建练习"""
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空",
                    }
                ),
                400,
            )

        # 验证必填字段
        required_fields = ["title", "course_id"]
        for field in required_fields:
            if field not in data or not data[field]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "MISSING_FIELD",
                            "message": f"缺少必填字段: {field}",
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
                        "message": "课程不存在",
                    }
                ),
                404,
            )

        # 权限检查：教师只能在自己的课程中创建练习
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能在自己的课程中创建练习",
                    }
                ),
                403,
            )

        # 创建练习
        practice = Practice(
            title=data["title"],
            description=data.get("description", ""),
            course_id=data["course_id"],
            creator_id=current_user.id,
            status="draft",
            settings=json.dumps(data.get("settings", {})),
        )

        db.session.add(practice)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"practice": practice.to_dict()},
                    "message": "练习创建成功",
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
                    "message": f"创建练习失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>", methods=["GET"], strict_slashes=False)
@require_auth
def get_practice(practice_id, current_user=None):
    """获取练习详情"""
    try:
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
        if current_user.role == "student":
            # 学生只能查看已发布的练习
            if practice.status != "published":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "练习尚未发布",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            # 教师只能查看自己创建的练习
            if practice.creator_id != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "您只能查看自己创建的练习",
                        }
                    ),
                    403,
                )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"practice": practice.to_dict()},
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
                    "message": f"获取练习详情失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>", methods=["PUT"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def update_practice(practice_id, current_user=None):
    """更新练习"""
    try:
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

        # 权限检查：只有创建者可以更新
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能更新自己创建的练习",
                    }
                ),
                403,
            )

        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空",
                    }
                ),
                400,
            )

        # 更新字段
        if "title" in data:
            practice.title = data["title"]
        if "description" in data:
            practice.description = data["description"]
        if "status" in data:
            valid_statuses = ["draft", "published", "archived"]
            if data["status"] in valid_statuses:
                practice.status = data["status"]
        if "settings" in data:
            practice.settings = json.dumps(data["settings"])

        practice.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"practice": practice.to_dict()},
                    "message": "练习更新成功",
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
                    "message": f"更新练习失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>", methods=["DELETE"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_DELETE)  # 复用考试删除权限
def delete_practice(practice_id, current_user=None):
    """删除练习"""
    try:
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

        # 权限检查：只有创建者可以删除
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能删除自己创建的练习",
                    }
                ),
                403,
            )

        # 检查是否有进行中的会话
        active_sessions = PracticeSession.query.filter_by(
            practice_id=practice_id, status="in_progress"
        ).count()
        if active_sessions > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_IN_USE",
                        "message": "练习正在使用中，无法删除",
                    }
                ),
                400,
            )

        db.session.delete(practice)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "练习删除成功",
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
                    "message": f"删除练习失败: {str(e)}",
                }
            ),
            500,
        )


# ==================== 练习题目管理API ====================


@practices_bp.route("/<practice_id>/questions", methods=["GET"], strict_slashes=False)
@require_auth
def get_practice_questions(practice_id, current_user=None):
    """获取练习题目列表"""
    try:
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
        if current_user.role == "student":
            if practice.status != "published":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "练习尚未发布",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if practice.creator_id != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "您只能查看自己创建的练习",
                        }
                    ),
                    403,
                )

        # 获取练习题目
        practice_questions = (
            PracticeQuestion.query.filter_by(practice_id=practice_id)
            .order_by(PracticeQuestion.order_index)
            .all()
        )

        questions_data = []
        for pq in practice_questions:
            question_data = pq.question.to_dict()
            question_data.update(
                {
                    "practice_question_id": pq.id,
                    "order_index": pq.order_index,
                    "points": pq.points,
                    "is_required": pq.is_required,
                }
            )
            questions_data.append(question_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "practice_id": practice_id,
                        "questions": questions_data,
                        "total_count": len(questions_data),
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
                    "message": f"获取练习题目失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>/questions", methods=["POST"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def add_practice_question(practice_id, current_user=None):
    """添加练习题目"""
    try:
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

        # 权限检查：只有创建者可以添加题目
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能修改自己创建的练习",
                    }
                ),
                403,
            )

        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空",
                    }
                ),
                400,
            )

        # 验证必填字段
        if "question_id" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_FIELD",
                        "message": "缺少题目ID",
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
                        "message": "题目不存在",
                    }
                ),
                404,
            )

        # 检查题目是否已经添加到练习中
        existing = PracticeQuestion.query.filter_by(
            practice_id=practice_id, question_id=data["question_id"]
        ).first()
        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_ALREADY_EXISTS",
                        "message": "题目已存在于练习中",
                    }
                ),
                400,
            )

        # 获取下一个排序索引
        max_order = (
            db.session.query(func.max(PracticeQuestion.order_index))
            .filter_by(practice_id=practice_id)
            .scalar()
            or 0
        )

        # 创建练习题目关联
        practice_question = PracticeQuestion(
            practice_id=practice_id,
            question_id=data["question_id"],
            order_index=max_order + 1,
            points=data.get("points", 1),
            is_required=data.get("is_required", True),
        )

        db.session.add(practice_question)
        db.session.commit()

        # 返回添加的题目信息
        question_data = question.to_dict()
        question_data.update(
            {
                "practice_question_id": practice_question.id,
                "order_index": practice_question.order_index,
                "points": practice_question.points,
                "is_required": practice_question.is_required,
            }
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question": question_data},
                    "message": "题目添加成功",
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
                    "message": f"添加题目失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>/questions/batch", methods=["POST"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def batch_add_practice_questions(practice_id, current_user=None):
    """批量添加练习题目"""
    try:
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

        # 权限检查：只有创建者可以添加题目
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能修改自己创建的练习",
                    }
                ),
                403,
            )

        data = request.get_json()
        if not data or "questions" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "请求数据不能为空或缺少题目列表",
                    }
                ),
                400,
            )

        questions_data = data["questions"]
        if not isinstance(questions_data, list) or len(questions_data) == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DATA",
                        "message": "题目列表不能为空",
                    }
                ),
                400,
            )

        # 验证所有题目ID
        question_ids = [q.get("question_id") for q in questions_data]
        if not all(question_ids):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_FIELD",
                        "message": "所有题目都必须包含question_id",
                    }
                ),
                400,
            )

        # 检查题目是否存在
        questions = Question.query.filter(Question.id.in_(question_ids)).all()
        if len(questions) != len(question_ids):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_NOT_FOUND",
                        "message": "部分题目不存在",
                    }
                ),
                404,
            )

        # 检查是否有重复题目
        existing_questions = PracticeQuestion.query.filter(
            PracticeQuestion.practice_id == practice_id,
            PracticeQuestion.question_id.in_(question_ids)
        ).all()
        if existing_questions:
            existing_ids = [eq.question_id for eq in existing_questions]
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_ALREADY_EXISTS",
                        "message": f"题目ID {existing_ids} 已存在于练习中",
                    }
                ),
                400,
            )

        # 获取当前最大排序索引
        max_order = (
            db.session.query(func.max(PracticeQuestion.order_index))
            .filter_by(practice_id=practice_id)
            .scalar()
            or 0
        )

        # 批量创建练习题目关联
        added_questions = []
        for i, question_data in enumerate(questions_data):
            practice_question = PracticeQuestion(
                practice_id=practice_id,
                question_id=question_data["question_id"],
                order_index=max_order + i + 1,
                points=question_data.get("points", 1),
                is_required=question_data.get("is_required", True),
            )
            db.session.add(practice_question)
            added_questions.append(practice_question)

        db.session.commit()

        # 返回添加的题目信息
        result_questions = []
        for pq in added_questions:
            question = next(q for q in questions if q.id == pq.question_id)
            question_data = question.to_dict()
            question_data.update(
                {
                    "practice_question_id": pq.id,
                    "order_index": pq.order_index,
                    "points": pq.points,
                    "is_required": pq.is_required,
                }
            )
            result_questions.append(question_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "questions": result_questions,
                        "added_count": len(result_questions),
                    },
                    "message": f"成功添加 {len(result_questions)} 道题目",
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
                    "message": f"批量添加题目失败: {str(e)}",
                }
            ),
            500,
        )


@practices_bp.route("/<practice_id>/questions/<practice_question_id>", methods=["DELETE"], strict_slashes=False)
@require_auth
@require_permission(Permission.EXAM_UPDATE)  # 复用考试更新权限
def remove_practice_question(practice_id, practice_question_id, current_user=None):
    """删除练习题目"""
    try:
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

        # 权限检查：只有创建者可以删除题目
        if current_user.role == "teacher" and practice.creator_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "您只能修改自己创建的练习",
                    }
                ),
                403,
            )

        practice_question = PracticeQuestion.query.filter_by(
            id=practice_question_id, practice_id=practice_id
        ).first()
        if not practice_question:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PRACTICE_QUESTION_NOT_FOUND",
                        "message": "练习题目不存在",
                    }
                ),
                404,
            )

        # 检查是否有学生已经答题
        answered_count = PracticeAnswer.query.filter_by(
            practice_question_id=practice_question_id
        ).count()
        if answered_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_ANSWERED",
                        "message": "该题目已有学生答题，无法删除",
                    }
                ),
                400,
            )

        # 删除题目并重新排序
        deleted_order = practice_question.order_index
        db.session.delete(practice_question)

        # 更新后续题目的排序
        PracticeQuestion.query.filter(
            PracticeQuestion.practice_id == practice_id,
            PracticeQuestion.order_index > deleted_order
        ).update(
            {PracticeQuestion.order_index: PracticeQuestion.order_index - 1}
        )

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "题目删除成功",
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
                    "message": f"删除题目失败: {str(e)}",
                }
            ),
            500,
        )