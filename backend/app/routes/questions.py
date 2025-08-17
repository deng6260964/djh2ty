from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models.question import QuestionBank, Question
from app.models.user import User
from app.utils.permissions import require_permission, require_auth, Permission
from sqlalchemy import or_, and_, func
import json
import random

questions_bp = Blueprint("questions", __name__)

# ==================== 题库管理API ====================


@questions_bp.route("/banks", methods=["GET"], strict_slashes=False)
@require_auth
def get_question_banks(current_user=None):
    """获取题库列表"""
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        category = request.args.get("category")
        difficulty = request.args.get("difficulty")
        search = request.args.get("search", "").strip()
        is_public = request.args.get("is_public", type=bool)

        # 构建查询
        query = QuestionBank.query

        # 权限过滤
        if current_user.role == "student":
            # 学生只能看到公开的题库
            query = query.filter(QuestionBank.is_public == True)
        elif current_user.role == "teacher":
            # 教师可以看到公开的题库和自己创建的题库
            query = query.filter(
                or_(
                    QuestionBank.is_public == True,
                    QuestionBank.created_by == current_user.id,
                )
            )
        # 管理员可以看到所有题库

        # 分类过滤
        if category:
            query = query.filter(QuestionBank.category == category)

        # 难度过滤
        if difficulty:
            query = query.filter(QuestionBank.difficulty_level == difficulty)

        # 公开状态过滤
        if is_public is not None:
            query = query.filter(QuestionBank.is_public == is_public)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    QuestionBank.name.ilike(f"%{search}%"),
                    QuestionBank.description.ilike(f"%{search}%"),
                )
            )

        # 排序
        query = query.order_by(QuestionBank.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        banks = []
        for bank in pagination.items:
            bank_data = bank.to_dict()
            # 添加题目数量
            bank_data["question_count"] = bank.get_question_count()
            banks.append(bank_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "question_banks": banks,
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
                    "message": f"获取题库列表失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route("/banks/<int:bank_id>", methods=["GET"], strict_slashes=False)
@require_auth
def get_question_bank(bank_id, current_user=None):
    """获取题库详情"""
    try:
        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "QUESTION_BANK_NOT_FOUND",
                        "message": "题库不存在",
                    }
                ),
                404,
            )

        # 权限检查
        if current_user.role == "student":
            if not bank.is_public:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not bank.is_public and bank.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )

        bank_data = bank.to_dict()
        bank_data["question_count"] = bank.get_question_count()

        # 获取题目列表（可选）
        include_questions = (
            request.args.get("include_questions", "false").lower() == "true"
        )
        if include_questions:
            questions = Question.query.filter_by(question_bank_id=bank_id).all()
            bank_data["questions"] = [q.to_dict() for q in questions]

        return jsonify({"success": True, "data": {"question_bank": bank_data}}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取题库详情失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route("/banks", methods=["POST"], strict_slashes=False)
@require_permission(Permission.QUESTION_BANK_CREATE)
def create_question_bank(current_user=None):
    """创建题库"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ["name", "category"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_REQUIRED_FIELDS",
                        "message": f'缺少必填字段: {", ".join(missing_fields)}',
                    }
                ),
                400,
            )

        # 验证分类
        valid_categories = [
            "grammar",
            "vocabulary",
            "reading",
            "listening",
            "writing",
            "speaking",
        ]
        if data["category"] not in valid_categories:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_CATEGORY",
                        "message": f'无效的分类，支持的分类: {", ".join(valid_categories)}',
                    }
                ),
                400,
            )

        # 验证难度
        difficulty_level = data.get("difficulty_level", "intermediate")
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if difficulty_level not in valid_difficulties:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DIFFICULTY",
                        "message": f'无效的难度，支持的难度: {", ".join(valid_difficulties)}',
                    }
                ),
                400,
            )

        # 创建题库
        bank = QuestionBank(
            name=data["name"],
            description=data.get("description", ""),
            category=data["category"],
            difficulty_level=difficulty_level,
            created_by=current_user.id,
            is_public=data.get("is_public", False),
        )

        db.session.add(bank)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question_bank": bank.to_dict()},
                    "message": "题库创建成功",
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
                    "message": f"创建题库失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route("/banks/<int:bank_id>", methods=["PUT"], strict_slashes=False)
@require_permission(Permission.QUESTION_BANK_UPDATE)
def update_question_bank(bank_id, current_user=None):
    """更新题库"""
    try:
        data = request.get_json()

        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题库不存在"}),
                404,
            )

        # 权限检查：只有创建者或管理员可以修改
        if current_user.role != "admin" and bank.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "无权限修改此题库",
                    }
                ),
                403,
            )

        # 更新字段
        if "name" in data:
            bank.name = data["name"]

        if "description" in data:
            bank.description = data["description"]

        if "category" in data:
            valid_categories = [
                "grammar",
                "vocabulary",
                "reading",
                "listening",
                "writing",
                "speaking",
            ]
            if data["category"] not in valid_categories:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_CATEGORY",
                            "message": f'无效的分类，支持的分类: {", ".join(valid_categories)}',
                        }
                    ),
                    400,
                )
            bank.category = data["category"]

        if "difficulty_level" in data:
            valid_difficulties = ["beginner", "intermediate", "advanced"]
            if data["difficulty_level"] not in valid_difficulties:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_DIFFICULTY",
                            "message": f'无效的难度，支持的难度: {", ".join(valid_difficulties)}',
                        }
                    ),
                    400,
                )
            bank.difficulty_level = data["difficulty_level"]

        if "is_public" in data:
            bank.is_public = data["is_public"]

        bank.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question_bank": bank.to_dict()},
                    "message": "题库更新成功",
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
                    "message": f"更新题库失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route("/banks/<int:bank_id>", methods=["DELETE"], strict_slashes=False)
@require_permission(Permission.QUESTION_BANK_DELETE)
def delete_question_bank(bank_id, current_user=None):
    """删除题库"""
    try:
        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题库不存在"}),
                404,
            )

        # 权限检查：只有创建者或管理员可以删除
        if current_user.role != "admin" and bank.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "无权限删除此题库",
                    }
                ),
                403,
            )

        # 检查是否有题目
        question_count = Question.query.filter_by(question_bank_id=bank_id).count()
        if question_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "BANK_NOT_EMPTY",
                        "message": f"题库中还有{question_count}道题目，无法删除",
                    }
                ),
                400,
            )

        db.session.delete(bank)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {},
                    "message": "Question bank deleted successfully",
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
                    "message": f"删除题库失败: {str(e)}",
                }
            ),
            500,
        )


# ==================== 题目管理API ====================


@questions_bp.route(
    "/banks/<int:bank_id>/questions", methods=["GET"], strict_slashes=False
)
@require_auth
def get_questions(bank_id, current_user=None):
    """获取题目列表"""
    try:
        # 检查题库权限
        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题库不存在"}),
                404,
            )

        # 权限检查
        if current_user.role == "student":
            if not bank.is_public:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not bank.is_public and bank.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        question_type = request.args.get("type")
        difficulty = request.args.get("difficulty")
        search = request.args.get("search", "").strip()

        # 构建查询
        query = Question.query.filter_by(question_bank_id=bank_id)

        # 题目类型过滤
        if question_type:
            query = query.filter(Question.question_type == question_type)

        # 难度过滤
        if difficulty:
            query = query.filter(Question.difficulty_level == difficulty)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Question.title.ilike(f"%{search}%"),
                    Question.content.ilike(f"%{search}%"),
                )
            )

        # 排序
        query = query.order_by(Question.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        questions = [q.to_dict() for q in pagination.items]

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "questions": questions,
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
                    "message": f"获取题目列表失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route(
    "/questions/<int:question_id>", methods=["GET"], strict_slashes=False
)
@require_auth
def get_question(question_id, current_user=None):
    """获取题目详情"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题目不存在"}),
                404,
            )

        # 检查题库权限
        bank = question.question_bank
        if current_user.role == "student":
            if not bank.is_public:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题目",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not bank.is_public and bank.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题目",
                        }
                    ),
                    403,
                )

        return jsonify({"success": True, "data": {"question": question.to_dict()}}), 200

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": f"获取题目详情失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route(
    "/banks/<int:bank_id>/questions", methods=["POST"], strict_slashes=False
)
@require_permission(Permission.QUESTION_CREATE)
def create_question(bank_id, current_user=None):
    """创建题目"""
    try:
        # 检查题库权限
        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题库不存在"}),
                404,
            )

        # 权限检查：只有题库创建者或管理员可以添加题目
        if current_user.role != "admin" and bank.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "无权限向此题库添加题目",
                    }
                ),
                403,
            )

        data = request.get_json()

        # 验证必填字段
        required_fields = ["question_type", "title", "content"]
        for field in required_fields:
            if not data.get(field):
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

        # 验证题目类型
        valid_types = [
            "multiple_choice",
            "true_false",
            "fill_blank",
            "essay",
            "listening",
            "speaking",
        ]
        if data["question_type"] not in valid_types:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_QUESTION_TYPE",
                        "message": f'无效的题目类型，支持的类型: {", ".join(valid_types)}',
                    }
                ),
                400,
            )

        # 验证难度
        difficulty_level = data.get("difficulty_level", "intermediate")
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if difficulty_level not in valid_difficulties:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_DIFFICULTY",
                        "message": f'无效的难度，支持的难度: {", ".join(valid_difficulties)}',
                    }
                ),
                400,
            )

        # 验证分值
        points = data.get("points", 1)
        if not isinstance(points, int) or points <= 0:
            return (
                jsonify(
                    {"success": False, "error": "INVALID_POINTS", "message": "分值必须是正整数"}
                ),
                400,
            )

        # 处理选项（选择题需要）
        options = data.get("options")
        if data["question_type"] in ["multiple_choice"] and not options:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_OPTIONS",
                        "message": "选择题必须提供选项",
                    }
                ),
                400,
            )

        if options and isinstance(options, (list, dict)):
            options = json.dumps(options)

        # 处理正确答案
        correct_answer = data.get("correct_answer")
        if correct_answer and isinstance(correct_answer, (list, dict)):
            correct_answer = json.dumps(correct_answer)

        # 处理标签
        tags = data.get("tags", [])
        if isinstance(tags, list):
            tags = ",".join(tags)

        # 创建题目
        question = Question(
            question_bank_id=bank_id,
            question_type=data["question_type"],
            title=data["title"],
            content=data["content"],
            options=options,
            correct_answer=correct_answer,
            explanation=data.get("explanation", ""),
            points=points,
            difficulty_level=difficulty_level,
            tags=tags,
            audio_file=data.get("audio_file"),
            image_file=data.get("image_file"),
            created_by=current_user.id,
        )

        db.session.add(question)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question": question.to_dict()},
                    "message": "题目创建成功",
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
                    "message": f"创建题目失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route(
    "/questions/<int:question_id>", methods=["PUT"], strict_slashes=False
)
@require_permission(Permission.QUESTION_UPDATE)
def update_question(question_id, current_user=None):
    """更新题目"""
    try:
        data = request.get_json()

        question = Question.query.get(question_id)
        if not question:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题目不存在"}),
                404,
            )

        # 权限检查：只有题库创建者或管理员可以修改
        bank = question.question_bank
        if current_user.role != "admin" and bank.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "无权限修改此题目",
                    }
                ),
                403,
            )

        # 更新字段
        if "question_type" in data:
            valid_types = [
                "multiple_choice",
                "true_false",
                "fill_blank",
                "essay",
                "listening",
                "speaking",
            ]
            if data["question_type"] not in valid_types:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_QUESTION_TYPE",
                            "message": f'无效的题目类型，支持的类型: {", ".join(valid_types)}',
                        }
                    ),
                    400,
                )
            question.question_type = data["question_type"]

        if "title" in data:
            question.title = data["title"]

        if "content" in data:
            question.content = data["content"]

        if "options" in data:
            options = data["options"]
            if isinstance(options, (list, dict)):
                options = json.dumps(options)
            question.options = options

        if "correct_answer" in data:
            correct_answer = data["correct_answer"]
            if isinstance(correct_answer, (list, dict)):
                correct_answer = json.dumps(correct_answer)
            question.correct_answer = correct_answer

        if "explanation" in data:
            question.explanation = data["explanation"]

        if "points" in data:
            if not isinstance(data["points"], int) or data["points"] <= 0:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_POINTS",
                            "message": "分值必须是正整数",
                        }
                    ),
                    400,
                )
            question.points = data["points"]

        if "difficulty_level" in data:
            valid_difficulties = ["beginner", "intermediate", "advanced"]
            if data["difficulty_level"] not in valid_difficulties:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_DIFFICULTY",
                            "message": f'无效的难度，支持的难度: {", ".join(valid_difficulties)}',
                        }
                    ),
                    400,
                )
            question.difficulty_level = data["difficulty_level"]

        if "tags" in data:
            tags = data["tags"]
            if isinstance(tags, list):
                tags = ",".join(tags)
            question.tags = tags

        if "audio_file" in data:
            question.audio_file = data["audio_file"]

        if "image_file" in data:
            question.image_file = data["image_file"]

        question.updated_at = datetime.utcnow()
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"question": question.to_dict()},
                    "message": "题目更新成功",
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
                    "message": f"更新题目失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route(
    "/questions/<int:question_id>", methods=["DELETE"], strict_slashes=False
)
@require_permission(Permission.QUESTION_DELETE)
def delete_question(question_id, current_user=None):
    """删除题目"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题目不存在"}),
                404,
            )

        # 权限检查：只有题库创建者或管理员可以删除
        bank = question.question_bank
        if current_user.role != "admin" and bank.created_by != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "PERMISSION_DENIED",
                        "message": "无权限删除此题目",
                    }
                ),
                403,
            )

        db.session.delete(question)
        db.session.commit()

        return (
            jsonify(
                {"success": True, "data": {"message": "题目删除成功"}, "message": "题目删除成功"}
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


# ==================== 随机抽题和试卷生成API ====================


@questions_bp.route(
    "/banks/<int:bank_id>/random", methods=["POST"], strict_slashes=False
)
@require_permission(Permission.QUESTION_RANDOM_DRAW)
def random_draw_questions(bank_id, current_user=None):
    """随机抽题"""
    try:
        # 检查题库权限
        bank = QuestionBank.query.get(bank_id)
        if not bank:
            return (
                jsonify({"success": False, "error": "NOT_FOUND", "message": "题库不存在"}),
                404,
            )

        # 权限检查
        if current_user.role == "student":
            if not bank.is_public:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )
        elif current_user.role == "teacher":
            if not bank.is_public and bank.created_by != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "PERMISSION_DENIED",
                            "message": "无权限访问此题库",
                        }
                    ),
                    403,
                )

        data = request.get_json()
        count = data.get("count", 10)
        question_type = data.get("question_type")
        difficulty = data.get("difficulty")

        # 验证抽题数量
        if not isinstance(count, int) or count <= 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_COUNT",
                        "message": "抽题数量必须是正整数",
                    }
                ),
                400,
            )

        # 构建查询
        query = Question.query.filter_by(question_bank_id=bank_id)

        if question_type:
            query = query.filter(Question.question_type == question_type)

        if difficulty:
            query = query.filter(Question.difficulty_level == difficulty)

        # 获取所有符合条件的题目
        all_questions = query.all()

        if len(all_questions) < count:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INSUFFICIENT_QUESTIONS",
                        "message": f"题库中符合条件的题目不足，只有{len(all_questions)}道题目",
                    }
                ),
                400,
            )

        # 随机抽取
        selected_questions = random.sample(all_questions, count)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "questions": [q.to_dict() for q in selected_questions],
                        "total_selected": len(selected_questions),
                    },
                    "message": "随机抽题成功",
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
                    "message": f"随机抽题失败: {str(e)}",
                }
            ),
            500,
        )


@questions_bp.route("/papers/generate", methods=["POST"], strict_slashes=False)
@require_permission(Permission.QUESTION_PAPER_GENERATE)
def generate_paper(current_user=None):
    """生成试卷"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ["title", "question_configs"]
        for field in required_fields:
            if not data.get(field):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "MISSING_REQUIRED_FIELD",
                            "message": f"缺少必填字段: {field}",
                        }
                    ),
                    400,
                )

        question_configs = data["question_configs"]
        if not isinstance(question_configs, list) or not question_configs:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_QUESTION_CONFIGS",
                        "message": "题目配置必须是非空数组",
                    }
                ),
                400,
            )

        paper_questions = []
        total_points = 0

        for config in question_configs:
            bank_id = config.get("bank_id")
            count = config.get("count", 1)
            question_type = config.get("question_type")
            difficulty = config.get("difficulty")

            if not bank_id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "MISSING_BANK_ID",
                            "message": "每个配置必须指定题库ID",
                        }
                    ),
                    400,
                )

            # 检查题库权限
            bank = QuestionBank.query.get(bank_id)
            if not bank:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "BANK_NOT_FOUND",
                            "message": f"题库{bank_id}不存在",
                        }
                    ),
                    404,
                )

            if current_user.role == "teacher":
                if not bank.is_public and bank.created_by != current_user.id:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "PERMISSION_DENIED",
                                "message": f"无权限访问题库{bank_id}",
                            }
                        ),
                        403,
                    )

            # 构建查询
            query = Question.query.filter_by(question_bank_id=bank_id)

            if question_type:
                query = query.filter(Question.question_type == question_type)

            if difficulty:
                query = query.filter(Question.difficulty_level == difficulty)

            # 获取题目
            available_questions = query.all()

            if len(available_questions) < count:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INSUFFICIENT_QUESTIONS",
                            "message": f"题库{bank_id}中符合条件的题目不足，需要{count}道，只有{len(available_questions)}道",
                        }
                    ),
                    400,
                )

            # 随机选择题目
            selected = random.sample(available_questions, count)
            paper_questions.extend(selected)
            total_points += sum(q.points for q in selected)

        # 打乱题目顺序
        random.shuffle(paper_questions)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "paper": {
                            "title": data["title"],
                            "description": data.get("description", ""),
                            "total_questions": len(paper_questions),
                            "total_points": total_points,
                            "questions": [q.to_dict() for q in paper_questions],
                        }
                    },
                    "message": "试卷生成成功",
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
                    "message": f"生成试卷失败: {str(e)}",
                }
            ),
            500,
        )
