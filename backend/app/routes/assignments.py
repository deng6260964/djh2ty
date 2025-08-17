from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.utils.permissions import require_role
from sqlalchemy import or_, and_

assignments_bp = Blueprint("assignments", __name__)


@assignments_bp.route("/", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_assignments():
    """获取作业列表"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        course_id = request.args.get("course_id", type=int)
        homework_type = request.args.get("type")
        status = request.args.get("status")  # published, draft
        search = request.args.get("search", "").strip()

        # 构建查询
        query = Homework.query

        # 权限过滤
        if current_user.role == "teacher":
            # 教师只能看到自己创建的作业
            query = query.filter(Homework.teacher_id == current_user_id)
        elif current_user.role == "student":
            # 学生只能看到已发布的作业，且是自己选课的课程
            from app.models.course import CourseEnrollment

            enrolled_courses = (
                db.session.query(CourseEnrollment.course_id)
                .filter(CourseEnrollment.student_id == current_user_id)
                .subquery()
            )
            query = query.filter(
                and_(
                    Homework.is_published == True,
                    Homework.course_id.in_(enrolled_courses),
                )
            )

        # 课程过滤
        if course_id:
            query = query.filter(Homework.course_id == course_id)

        # 类型过滤
        if homework_type:
            query = query.filter(Homework.homework_type == homework_type)

        # 状态过滤
        if status == "published":
            query = query.filter(Homework.is_published == True)
        elif status == "draft":
            query = query.filter(Homework.is_published == False)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    Homework.title.ilike(f"%{search}%"),
                    Homework.description.ilike(f"%{search}%"),
                )
            )

        # 排序
        query = query.order_by(Homework.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        assignments = []
        for homework in pagination.items:
            assignment_data = homework.to_dict()

            # 添加作业状态
            assignment_data["status"] = homework.status

            # 为学生添加提交状态
            if current_user.role == "student":
                assignment_data["student_status"] = homework.get_status_for_student(
                    current_user_id
                )

                submission = HomeworkSubmission.query.filter_by(
                    homework_id=homework.id, student_id=current_user_id
                ).first()
                assignment_data["submission_status"] = (
                    submission.status if submission else "not_started"
                )
                assignment_data["submission_id"] = submission.id if submission else None

            # 为教师添加统计信息
            elif current_user.role == "teacher":
                assignment_data["submission_count"] = homework.get_submission_count()
                assignment_data["graded_count"] = homework.get_graded_count()

            assignments.append(assignment_data)

        return (
            jsonify(
                {
                    "assignments": assignments,
                    "pagination": {
                        "page": pagination.page,
                        "pages": pagination.pages,
                        "per_page": pagination.per_page,
                        "total": pagination.total,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"获取作业列表失败: {str(e)}"}), 500


@assignments_bp.route("/<int:assignment_id>", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_assignment(assignment_id):
    """获取作业详情"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if current_user.role == "teacher":
            # 教师只能查看自己创建的作业
            if homework.teacher_id != current_user_id:
                return jsonify({"error": "无权限访问此作业"}), 403
        elif current_user.role == "student":
            # 学生只能查看已发布的作业，且是自己选课的课程
            if not homework.is_published:
                return jsonify({"error": "作业未发布"}), 403

            from app.models.course import CourseEnrollment

            enrollment = CourseEnrollment.query.filter_by(
                student_id=current_user_id, course_id=homework.course_id, is_active=True
            ).first()
            if not enrollment:
                return jsonify({"error": "未选修此课程"}), 403

        assignment_data = homework.to_dict()

        # 添加作业状态
        assignment_data["status"] = homework.status

        # 为学生添加提交信息
        if current_user.role == "student":
            assignment_data["student_status"] = homework.get_status_for_student(
                current_user_id
            )

            submission = HomeworkSubmission.query.filter_by(
                homework_id=homework.id, student_id=current_user_id
            ).first()
            if submission:
                assignment_data["submission"] = submission.to_dict()
            else:
                assignment_data["submission"] = None

        # 为教师添加提交列表
        elif current_user.role == "teacher":
            submissions = HomeworkSubmission.query.filter_by(
                homework_id=homework.id
            ).all()
            assignment_data["submissions"] = [sub.to_dict() for sub in submissions]
            assignment_data["submission_count"] = len(submissions)
            assignment_data["graded_count"] = sum(
                1 for sub in submissions if sub.score is not None
            )

        return jsonify(assignment_data), 200

    except Exception as e:
        return jsonify({"error": f"获取作业详情失败: {str(e)}"}), 500


@assignments_bp.route("/", methods=["POST"], strict_slashes=False)
@require_role("teacher")
def create_assignment(current_user=None):
    print(f"DEBUG: create_assignment called with current_user: {current_user}")
    """创建新作业"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        # 验证必填字段
        required_fields = ["title", "course_id", "homework_type", "due_date"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"缺少必填字段: {field}"}), 400

        # 验证课程存在且教师有权限
        course = Course.query.get(data["course_id"])
        if not course:
            return jsonify({"error": "课程不存在"}), 404

        print(
            f"DEBUG: course.teacher_id = {course.teacher_id} (type: {type(course.teacher_id)})"
        )
        print(
            f"DEBUG: current_user_id = {current_user_id} (type: {type(current_user_id)})"
        )
        print(f"DEBUG: comparison result = {course.teacher_id != current_user_id}")

        if course.teacher_id != current_user_id:
            return jsonify({"error": "无权限为此课程创建作业"}), 403

        # 验证作业类型
        valid_types = ["writing", "reading", "listening", "speaking", "mixed"]
        if data["homework_type"] not in valid_types:
            return jsonify({"error": f'无效的作业类型，支持的类型: {", ".join(valid_types)}'}), 400

        # 验证截止时间格式
        try:
            due_date = datetime.fromisoformat(data["due_date"].replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"error": "截止时间格式错误，请使用ISO格式"}), 400

        # 验证最大分数
        max_score = data.get("max_score", 100)
        if not isinstance(max_score, int) or max_score <= 0:
            return jsonify({"error": "最大分数必须是正整数"}), 400

        # 处理附件文件
        attachment_files = data.get("attachment_files")
        if attachment_files and isinstance(attachment_files, (list, dict)):
            import json

            attachment_files = json.dumps(attachment_files)

        # 创建作业
        homework = Homework(
            title=data["title"],
            description=data.get("description", ""),
            course_id=data["course_id"],
            teacher_id=current_user_id,
            homework_type=data["homework_type"],
            max_score=max_score,
            due_date=due_date,
            instructions=data.get("instructions", ""),
            attachment_files=attachment_files,
            is_published=data.get("is_published", False),
        )

        db.session.add(homework)
        db.session.commit()

        return jsonify({"message": "作业创建成功", "assignment": homework.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"创建作业失败: {str(e)}"}), 500


@assignments_bp.route("/<int:assignment_id>", methods=["PUT"])
@require_role("teacher")
def update_assignment(assignment_id, current_user=None):
    """更新作业"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if homework.teacher_id != current_user_id:
            return jsonify({"error": "无权限修改此作业"}), 403

        # 检查是否有学生已提交，如果有则限制某些字段的修改
        has_submissions = (
            HomeworkSubmission.query.filter_by(homework_id=assignment_id)
            .filter(HomeworkSubmission.status != "draft")
            .first()
            is not None
        )

        # 更新字段
        if "title" in data:
            homework.title = data["title"]

        if "description" in data:
            homework.description = data["description"]

        if "instructions" in data:
            homework.instructions = data["instructions"]

        if "is_published" in data:
            homework.is_published = data["is_published"]

        # 如果有提交，限制关键字段修改
        if has_submissions:
            restricted_fields = ["homework_type", "max_score", "due_date"]
            for field in restricted_fields:
                if field in data:
                    return jsonify({"error": f"作业已有提交，无法修改{field}字段"}), 400
        else:
            # 没有提交时可以修改所有字段
            if "homework_type" in data:
                valid_types = ["writing", "reading", "listening", "speaking", "mixed"]
                if data["homework_type"] not in valid_types:
                    return (
                        jsonify({"error": f'无效的作业类型，支持的类型: {", ".join(valid_types)}'}),
                        400,
                    )
                homework.homework_type = data["homework_type"]

            if "max_score" in data:
                if not isinstance(data["max_score"], int) or data["max_score"] <= 0:
                    return jsonify({"error": "最大分数必须是正整数"}), 400
                homework.max_score = data["max_score"]

            if "due_date" in data:
                try:
                    homework.due_date = datetime.fromisoformat(
                        data["due_date"].replace("Z", "+00:00")
                    )
                except ValueError:
                    return jsonify({"error": "截止时间格式错误，请使用ISO格式"}), 400

        homework.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "作业更新成功", "assignment": homework.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"更新作业失败: {str(e)}"}), 500


@assignments_bp.route("/<int:assignment_id>", methods=["DELETE"])
@require_role("teacher")
def delete_assignment(assignment_id, current_user=None):
    """删除作业"""
    try:
        current_user_id = int(get_jwt_identity())

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if homework.teacher_id != current_user_id:
            return jsonify({"error": "无权限删除此作业"}), 403

        # 检查是否有学生提交
        submissions_count = HomeworkSubmission.query.filter_by(
            homework_id=assignment_id
        ).count()

        if submissions_count > 0:
            return jsonify({"error": "作业已有学生提交，无法删除"}), 400

        db.session.delete(homework)
        db.session.commit()

        return jsonify({"message": "作业删除成功"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"删除作业失败: {str(e)}"}), 500


# 作业提交相关API
@assignments_bp.route("/<int:assignment_id>/submissions", methods=["GET"])
@jwt_required()
def get_submissions(assignment_id):
    """获取作业提交列表"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if current_user.role == "teacher":
            # 教师只能查看自己创建的作业的提交
            if homework.teacher_id != current_user_id:
                return jsonify({"error": "无权限查看此作业的提交"}), 403

            # 获取所有提交
            submissions = HomeworkSubmission.query.filter_by(
                homework_id=assignment_id
            ).all()

        elif current_user.role == "student":
            # 学生只能查看自己的提交
            submissions = HomeworkSubmission.query.filter_by(
                homework_id=assignment_id, student_id=current_user_id
            ).all()
        else:
            return jsonify({"error": "无权限访问"}), 403

        return jsonify({"submissions": [sub.to_dict() for sub in submissions]}), 200

    except Exception as e:
        return jsonify({"error": f"获取提交列表失败: {str(e)}"}), 500


@assignments_bp.route("/<int:assignment_id>/submissions", methods=["POST"])
@jwt_required()
@require_role("student")
def submit_assignment(assignment_id, current_user=None):
    """提交作业"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 检查作业是否已发布
        if not homework.is_published:
            return jsonify({"error": "作业未发布"}), 403

        # 检查学生是否选修了该课程
        from app.models.course import CourseEnrollment

        enrollment = CourseEnrollment.query.filter_by(
            student_id=current_user_id, course_id=homework.course_id, is_active=True
        ).first()
        if not enrollment:
            return jsonify({"error": "未选修此课程"}), 403

        # 检查是否已有提交
        existing_submission = HomeworkSubmission.query.filter_by(
            homework_id=assignment_id, student_id=current_user_id
        ).first()

        if existing_submission:
            # 更新现有提交
            submission = existing_submission
            if submission.status == "submitted":
                return jsonify({"error": "作业已提交，无法重复提交"}), 400
        else:
            # 创建新提交
            submission = HomeworkSubmission(
                homework_id=assignment_id,
                student_id=current_user_id,
                status="draft",  # 显式设置默认状态
            )
            db.session.add(submission)

        # 更新提交内容
        if "content" in data:
            submission.content = data["content"]

        if "submission_files" in data:
            submission.submission_files = data["submission_files"]

        if "file_ids" in data:
            file_ids = data["file_ids"]
            # 验证文件ID
            if file_ids:
                from app.models.file import File

                valid_files = File.query.filter(
                    File.id.in_(file_ids),
                    File.uploaded_by == current_user_id,
                    File.file_category == "submission_file",
                ).all()
                if len(valid_files) != len(file_ids):
                    return jsonify({"error": "部分文件不存在或无权限访问"}), 400

                import json

                submission.file_ids = json.dumps(file_ids)

        # 确定提交状态
        submit_action = data.get("action", "draft")  # draft 或 submit

        if submit_action == "submit":
            # 正式提交
            print(
                f"[DEBUG] 检查提交内容: content={submission.content}, submission_files={submission.submission_files}, file_ids={submission.file_ids}"
            )
            if (
                not submission.content
                and not submission.submission_files
                and not submission.file_ids
            ):
                return jsonify({"error": "提交内容不能为空"}), 400

            print(f"[DEBUG] 调用submission.submit()方法前状态: {submission.status}")
            result = submission.submit()
            print(f"[DEBUG] submission.submit()返回结果: {result}")
            print(f"[DEBUG] 提交后状态: {submission.status}")
        else:
            # 保存草稿
            print(f"[DEBUG] 设置为草稿状态")
            submission.status = "draft"

        submission.updated_at = datetime.utcnow()
        print(f"[DEBUG] 准备提交到数据库")
        db.session.commit()
        print(f"[DEBUG] 数据库提交成功")

        # 在提交到数据库后更新文件关联信息
        if "file_ids" in data and data["file_ids"]:
            from app.models.file import File

            File.query.filter(File.id.in_(data["file_ids"])).update(
                {"related_id": submission.id, "related_type": "homework_submission"},
                synchronize_session=False,
            )
            db.session.commit()

        return (
            jsonify(
                {
                    "message": "提交成功" if submit_action == "submit" else "草稿保存成功",
                    "submission": submission.to_dict(),
                }
            ),
            201 if not existing_submission else 200,
        )

    except Exception as e:
        db.session.rollback()
        import traceback

        error_msg = f"提交作业失败: {str(e)}"
        error_trace = traceback.format_exc()
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] 详细错误信息: {error_trace}")

        # 记录到应用日志
        from flask import current_app

        current_app.logger.error(f"{error_msg}\n{error_trace}")

        return jsonify({"error": f"提交失败: {str(e)}"}), 500


@assignments_bp.route(
    "/<int:assignment_id>/submissions/<int:submission_id>", methods=["GET"]
)
@jwt_required()
def get_submission(assignment_id, submission_id):
    """获取单个提交详情"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        submission = HomeworkSubmission.query.get(submission_id)
        if not submission or submission.homework_id != assignment_id:
            return jsonify({"error": "提交不存在"}), 404

        # 权限检查
        if current_user.role == "student":
            # 学生只能查看自己的提交
            if submission.student_id != current_user_id:
                return jsonify({"error": "无权限查看此提交"}), 403
        elif current_user.role == "teacher":
            # 教师只能查看自己课程的提交
            if submission.homework.teacher_id != current_user_id:
                return jsonify({"error": "无权限查看此提交"}), 403
        else:
            return jsonify({"error": "无权限访问"}), 403

        return jsonify(submission.to_dict()), 200

    except Exception as e:
        return jsonify({"error": f"获取提交详情失败: {str(e)}"}), 500


@assignments_bp.route(
    "/<int:assignment_id>/submissions/<int:submission_id>", methods=["PUT"]
)
@jwt_required()
@require_role("student")
def update_submission(assignment_id, submission_id, current_user=None):
    """更新提交内容"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        submission = HomeworkSubmission.query.get(submission_id)
        if not submission or submission.homework_id != assignment_id:
            return jsonify({"error": "提交不存在"}), 404

        # 权限检查
        if submission.student_id != current_user_id:
            return jsonify({"error": "无权限修改此提交"}), 403

        # 检查提交状态
        if submission.status == "submitted":
            return jsonify({"error": "已提交的作业无法修改"}), 400

        # 检查作业截止时间
        if submission.homework.is_overdue:
            return jsonify({"error": "作业已截止，无法修改"}), 400

        # 更新内容
        if "content" in data:
            submission.content = data["content"]

        if "submission_files" in data:
            submission.submission_files = data["submission_files"]

        # 处理提交动作
        submit_action = data.get("action", "draft")

        if submit_action == "submit":
            if not submission.content and not submission.submission_files:
                return jsonify({"error": "提交内容不能为空"}), 400
            submission.submit()

        submission.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "更新成功", "submission": submission.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"更新提交失败: {str(e)}"}), 500


# 作业批改相关API
@assignments_bp.route(
    "/<int:assignment_id>/submissions/<int:submission_id>/grade", methods=["POST"]
)
@jwt_required()
@require_role("teacher")
def grade_submission(assignment_id, submission_id, current_user=None):
    """批改作业"""
    try:
        print(
            f"DEBUG: grade_submission called with assignment_id={assignment_id}, submission_id={submission_id}"
        )
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        print(f"DEBUG: current_user_id={current_user_id}, data={data}")

        submission = HomeworkSubmission.query.get(submission_id)
        print(f"DEBUG: submission found: {submission}")
        if not submission or submission.homework_id != assignment_id:
            return jsonify({"error": "提交不存在"}), 404

        print(f"DEBUG: submission.homework: {submission.homework}")
        # 权限检查 - 只有作业创建者可以批改
        if submission.homework.teacher_id != current_user_id:
            return jsonify({"error": "无权限批改此作业"}), 403

        # 检查提交状态
        print(f"DEBUG: submission.status: {submission.status}")
        if submission.status != "submitted":
            return jsonify({"error": "只能批改已提交的作业"}), 400

        # 验证分数
        score = data.get("score")
        if score is None:
            return jsonify({"error": "分数不能为空"}), 400

        try:
            score = float(score)
        except (ValueError, TypeError):
            return jsonify({"error": "分数必须是数字"}), 400

        if score < 0 or score > submission.homework.max_score:
            return jsonify({"error": f"分数必须在0到{submission.homework.max_score}之间"}), 400

        # 获取反馈
        feedback = data.get("feedback", "")

        # 批改作业
        print(
            f"DEBUG: calling submission.grade with score={score}, feedback={feedback}, grader_id={current_user_id}"
        )
        result = submission.grade(score, feedback, current_user_id)
        print(f"DEBUG: grade result: {result}")

        print(f"DEBUG: before commit, submission status: {submission.status}")
        db.session.commit()
        print(f"DEBUG: after commit")

        submission_dict = submission.to_dict()
        print(f"DEBUG: submission.to_dict() result: {submission_dict}")

        return jsonify({"message": "批改成功", "submission": submission_dict}), 200

    except Exception as e:
        print(f"DEBUG: Exception in grade_submission: {str(e)}")
        import traceback

        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": f"批改作业失败: {str(e)}"}), 500


@assignments_bp.route(
    "/<int:assignment_id>/submissions/<int:submission_id>/grade", methods=["PUT"]
)
@jwt_required()
@require_role("teacher")
def update_grade(assignment_id, submission_id, current_user=None):
    """更新批改结果"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        submission = HomeworkSubmission.query.get(submission_id)
        if not submission or submission.homework_id != assignment_id:
            return jsonify({"error": "提交不存在"}), 404

        # 权限检查
        if submission.homework.teacher_id != current_user_id:
            return jsonify({"error": "无权限修改此批改"}), 403

        # 检查是否已批改
        if submission.status != "graded":
            return jsonify({"error": "作业尚未批改"}), 400

        # 验证分数
        if "score" in data:
            score = data["score"]
            try:
                score = float(score)
            except (ValueError, TypeError):
                return jsonify({"error": "分数必须是数字"}), 400

            if score < 0 or score > submission.homework.max_score:
                return (
                    jsonify({"error": f"分数必须在0到{submission.homework.max_score}之间"}),
                    400,
                )

            submission.score = score

        # 更新反馈
        if "feedback" in data:
            submission.feedback = data["feedback"]

        submission.graded_at = datetime.utcnow()
        submission.graded_by = current_user_id
        db.session.commit()

        return jsonify({"message": "批改更新成功", "submission": submission.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"更新批改失败: {str(e)}"}), 500


@assignments_bp.route("/<int:assignment_id>/batch-grade", methods=["POST"])
@jwt_required()
@require_role("teacher")
def batch_grade_submissions(assignment_id, current_user=None):
    """批量批改作业"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if homework.teacher_id != current_user_id:
            return jsonify({"error": "无权限批改此作业"}), 403

        grades = data.get("grades", [])
        if not grades:
            return jsonify({"error": "批改数据不能为空"}), 400

        results = []
        errors = []

        for grade_data in grades:
            try:
                submission_id = grade_data.get("submission_id")
                score = grade_data.get("score")
                feedback = grade_data.get("feedback", "")

                if not submission_id:
                    errors.append({"error": "提交ID不能为空"})
                    continue

                submission = HomeworkSubmission.query.get(submission_id)
                if not submission or submission.homework_id != assignment_id:
                    errors.append({"submission_id": submission_id, "error": "提交不存在"})
                    continue

                if submission.status != "submitted":
                    errors.append(
                        {"submission_id": submission_id, "error": "只能批改已提交的作业"}
                    )
                    continue

                # 验证分数
                if score is None:
                    errors.append({"submission_id": submission_id, "error": "分数不能为空"})
                    continue

                try:
                    score = float(score)
                except (ValueError, TypeError):
                    errors.append({"submission_id": submission_id, "error": "分数必须是数字"})
                    continue

                if score < 0 or score > homework.max_score:
                    errors.append(
                        {
                            "submission_id": submission_id,
                            "error": f"分数必须在0到{homework.max_score}之间",
                        }
                    )
                    continue

                # 批改作业
                submission.grade(score, feedback, current_user_id)
                results.append(
                    {
                        "submission_id": submission_id,
                        "status": "success",
                        "submission": submission.to_dict(),
                    }
                )

            except Exception as e:
                errors.append(
                    {"submission_id": grade_data.get("submission_id"), "error": str(e)}
                )

        db.session.commit()

        return (
            jsonify(
                {
                    "message": f"批量批改完成，成功{len(results)}个，失败{len(errors)}个",
                    "results": results,
                    "errors": errors,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"批量批改失败: {str(e)}"}), 500


# 作业统计相关API
@assignments_bp.route("/<int:assignment_id>/statistics", methods=["GET"])
@jwt_required()
def get_assignment_statistics(assignment_id):
    """获取作业统计信息"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        homework = Homework.query.get(assignment_id)
        if not homework:
            return jsonify({"error": "作业不存在"}), 404

        # 权限检查
        if current_user.role == "teacher":
            # 教师只能查看自己创建的作业统计
            if homework.teacher_id != current_user_id:
                return jsonify({"error": "无权限查看此作业统计"}), 403
        elif current_user.role == "student":
            # 学生只能查看已发布作业的基本统计
            if not homework.is_published:
                return jsonify({"error": "作业未发布"}), 403

            # 检查是否选修了该课程
            enrollment = CourseEnrollment.query.filter_by(
                student_id=current_user_id, course_id=homework.course_id, is_active=True
            ).first()
            if not enrollment:
                return jsonify({"error": "未选修此课程"}), 403
        else:
            return jsonify({"error": "无权限访问"}), 403

        # 获取统计数据
        total_students = (
            db.session.query(CourseEnrollment)
            .filter_by(course_id=homework.course_id, is_active=True)
            .count()
        )

        total_submissions = homework.get_submission_count()
        graded_submissions = homework.get_graded_count()

        # 获取提交状态统计
        submission_stats = (
            db.session.query(
                HomeworkSubmission.status, db.func.count(HomeworkSubmission.id)
            )
            .filter_by(homework_id=assignment_id)
            .group_by(HomeworkSubmission.status)
            .all()
        )

        status_counts = {status: count for status, count in submission_stats}

        # 基本统计信息
        statistics = {
            "assignment_info": {
                "id": homework.id,
                "title": homework.title,
                "max_score": homework.max_score,
                "due_date": homework.due_date.isoformat()
                if homework.due_date
                else None,
                "is_published": homework.is_published,
                "is_overdue": homework.is_overdue,
            },
            "total_students": total_students,
            "total_submissions": total_submissions,
            "submission_rate": round((total_submissions / total_students * 100), 2)
            if total_students > 0
            else 0,
            "graded_submissions": graded_submissions,
            "grading_progress": round((graded_submissions / total_submissions * 100), 2)
            if total_submissions > 0
            else 0,
            "submission_overview": {
                "total_students": total_students,
                "total_submissions": total_submissions,
                "submission_rate": round((total_submissions / total_students * 100), 2)
                if total_students > 0
                else 0,
                "graded_submissions": graded_submissions,
                "grading_progress": round(
                    (graded_submissions / total_submissions * 100), 2
                )
                if total_submissions > 0
                else 0,
            },
            "status_distribution": {
                "draft": status_counts.get("draft", 0),
                "submitted": status_counts.get("submitted", 0),
                "graded": status_counts.get("graded", 0),
                "not_submitted": total_students - total_submissions,
            },
        }

        # 教师可以看到更详细的统计
        if current_user.role == "teacher":
            # 成绩统计
            graded_scores = (
                db.session.query(HomeworkSubmission.score)
                .filter_by(homework_id=assignment_id, status="graded")
                .filter(HomeworkSubmission.score.isnot(None))
                .all()
            )

            if graded_scores:
                scores = [score[0] for score in graded_scores]
                average_score = round(sum(scores) / len(scores), 2)
                statistics["average_score"] = average_score
                statistics["grade_statistics"] = {
                    "average_score": average_score,
                    "highest_score": max(scores),
                    "lowest_score": min(scores),
                    "pass_rate": round(
                        len([s for s in scores if s >= homework.max_score * 0.6])
                        / len(scores)
                        * 100,
                        2,
                    ),
                }

                # 分数分布
                score_ranges = {
                    "excellent": len(
                        [s for s in scores if s >= homework.max_score * 0.9]
                    ),
                    "good": len(
                        [
                            s
                            for s in scores
                            if homework.max_score * 0.8 <= s < homework.max_score * 0.9
                        ]
                    ),
                    "fair": len(
                        [
                            s
                            for s in scores
                            if homework.max_score * 0.6 <= s < homework.max_score * 0.8
                        ]
                    ),
                    "poor": len([s for s in scores if s < homework.max_score * 0.6]),
                }
                statistics["score_distribution"] = score_ranges
            else:
                statistics["average_score"] = None
                statistics["grade_statistics"] = None
                statistics["score_distribution"] = None

            # 提交时间统计
            if homework.due_date:
                late_submissions = (
                    db.session.query(HomeworkSubmission)
                    .filter(
                        HomeworkSubmission.homework_id == assignment_id,
                        HomeworkSubmission.submitted_at > homework.due_date,
                    )
                    .count()
                )

                statistics["timing_statistics"] = {
                    "on_time_submissions": total_submissions - late_submissions,
                    "late_submissions": late_submissions,
                    "late_rate": round((late_submissions / total_submissions * 100), 2)
                    if total_submissions > 0
                    else 0,
                }

        return jsonify({"message": "获取统计信息成功", "statistics": statistics}), 200

    except Exception as e:
        return jsonify({"error": f"获取统计信息失败: {str(e)}"}), 500


@assignments_bp.route("/statistics/overview", methods=["GET"])
@jwt_required()
def get_assignments_overview():
    """获取作业总览统计"""
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        if current_user.role == "teacher":
            # 教师查看自己创建的所有作业统计
            homeworks = Homework.query.filter_by(teacher_id=current_user_id).all()

            total_assignments = len(homeworks)
            published_assignments = len([hw for hw in homeworks if hw.is_published])
            overdue_assignments = len([hw for hw in homeworks if hw.is_overdue])

            # 计算总提交数和总批改数
            total_submissions = sum(hw.get_submission_count() for hw in homeworks)
            total_graded = sum(hw.get_graded_count() for hw in homeworks)

            overview = {
                "role": "teacher",
                "assignments_overview": {
                    "total_assignments": total_assignments,
                    "published_assignments": published_assignments,
                    "draft_assignments": total_assignments - published_assignments,
                    "overdue_assignments": overdue_assignments,
                },
                "grading_overview": {
                    "total_submissions": total_submissions,
                    "graded_submissions": total_graded,
                    "pending_grading": total_submissions - total_graded,
                    "grading_progress": round(
                        (total_graded / total_submissions * 100), 2
                    )
                    if total_submissions > 0
                    else 0,
                },
            }

        elif current_user.role == "student":
            # 学生查看自己的作业完成情况
            from app.models.course import CourseEnrollment

            # 获取学生选修的所有课程
            enrollments = CourseEnrollment.query.filter_by(
                student_id=current_user_id, is_active=True
            ).all()
            course_ids = [e.course_id for e in enrollments]

            # 获取这些课程的所有已发布作业
            homeworks = Homework.query.filter(
                Homework.course_id.in_(course_ids), Homework.is_published == True
            ).all()

            total_assignments = len(homeworks)

            # 获取学生的提交情况
            submissions = HomeworkSubmission.query.filter(
                HomeworkSubmission.student_id == current_user_id,
                HomeworkSubmission.homework_id.in_([hw.id for hw in homeworks]),
            ).all()

            submitted_count = len(
                [s for s in submissions if s.status in ["submitted", "graded"]]
            )
            graded_count = len([s for s in submissions if s.status == "graded"])
            draft_count = len([s for s in submissions if s.status == "draft"])
            overdue_count = len(
                [
                    hw
                    for hw in homeworks
                    if hw.is_overdue
                    and not any(
                        s.homework_id == hw.id and s.status in ["submitted", "graded"]
                        for s in submissions
                    )
                ]
            )

            overview = {
                "role": "student",
                "assignments_overview": {
                    "total_assignments": total_assignments,
                    "submitted_assignments": submitted_count,
                    "draft_assignments": draft_count,
                    "not_started": total_assignments - submitted_count - draft_count,
                    "overdue_assignments": overdue_count,
                },
                "completion_overview": {
                    "completion_rate": round(
                        (submitted_count / total_assignments * 100), 2
                    )
                    if total_assignments > 0
                    else 0,
                    "graded_assignments": graded_count,
                    "pending_grading": submitted_count - graded_count,
                },
            }

            # 计算平均分（如果有已批改的作业）
            graded_submissions = [
                s for s in submissions if s.status == "graded" and s.score is not None
            ]
            if graded_submissions:
                avg_score = sum(s.score for s in graded_submissions) / len(
                    graded_submissions
                )
                overview["grade_overview"] = {
                    "average_score": round(avg_score, 2),
                    "graded_count": len(graded_submissions),
                }

        else:
            return jsonify({"error": "无权限访问"}), 403

        return jsonify({"message": "获取总览统计成功", "statistics": overview}), 200

    except Exception as e:
        return jsonify({"error": f"获取总览统计失败: {str(e)}"}), 500
