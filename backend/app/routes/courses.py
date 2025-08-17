from flask import Blueprint, jsonify, request
from app.utils.permissions import (
    require_auth,
    admin_required,
    teacher_required,
    require_permission,
    Permission,
    PermissionManager,
)
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.database import db
from sqlalchemy import or_, and_, func
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
courses_bp = Blueprint("courses", __name__)


@courses_bp.route("", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_courses(current_user):
    """获取课程列表"""
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        course_type = request.args.get("course_type")
        teacher_id = request.args.get("teacher_id", type=int)
        search = request.args.get("search")
        is_active = request.args.get("is_active")

        # 构建查询
        query = Course.query

        # 课程类型过滤
        if course_type:
            query = query.filter(Course.course_type == course_type)

        # 教师过滤
        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)

        # 状态过滤
        if is_active is not None:
            is_active_bool = is_active.lower() in ["true", "1", "yes"]
            query = query.filter(Course.is_active == is_active_bool)

        # 搜索过滤（课程名称或描述）
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Course.name.ilike(search_pattern),
                    Course.description.ilike(search_pattern),
                )
            )

        # 权限控制：教师只能查看自己的课程和激活的课程
        if current_user.role == "teacher":
            query = query.filter(
                or_(Course.teacher_id == current_user.id, Course.is_active == True)
            )
        elif current_user.role == "student":
            # 学生只能查看激活的课程
            query = query.filter(Course.is_active == True)

        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        courses = pagination.items

        # 为每个课程添加选课人数信息
        courses_data = []
        for course in courses:
            course_dict = course.to_dict()
            # 获取当前选课人数
            enrolled_count = CourseEnrollment.query.filter_by(
                course_id=course.id, is_active=True
            ).count()
            course_dict["enrolled_count"] = enrolled_count
            course_dict["available_slots"] = course.max_students - enrolled_count
            courses_data.append(course_dict)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "courses": courses_data,
                        "pagination": {
                            "page": page,
                            "per_page": per_page,
                            "total": pagination.total,
                            "pages": pagination.pages,
                            "has_next": pagination.has_next,
                            "has_prev": pagination.has_prev,
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to retrieve courses",
                }
            ),
            500,
        )


@courses_bp.route("/<int:course_id>", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_course(course_id, current_user):
    """获取课程详情"""
    try:
        # 查找课程
        course = Course.query.get(course_id)
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

        # 权限检查：学生只能查看激活的课程
        if current_user.role == "student" and not course.is_active:
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

        # 教师只能查看自己的课程或激活的课程
        if current_user.role == "teacher":
            if course.teacher_id != current_user.id and not course.is_active:
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

        course_dict = course.to_dict()

        # 获取选课学生信息
        enrollments = CourseEnrollment.query.filter_by(
            course_id=course.id, is_active=True
        ).all()

        students = []
        for enrollment in enrollments:
            if enrollment.student:
                students.append(
                    {
                        "id": enrollment.student.id,
                        "name": enrollment.student.name,
                        "email": enrollment.student.email,
                        "enrolled_at": enrollment.enrolled_at.isoformat(),
                    }
                )

        course_dict["students"] = students
        course_dict["enrolled_count"] = len(students)
        course_dict["available_slots"] = course.max_students - len(students)

        return jsonify({"success": True, "data": {"course": course_dict}}), 200

    except Exception as e:
        logger.error(f"Error getting course {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to retrieve course",
                }
            ),
            500,
        )


@courses_bp.route("", methods=["POST"])
@require_auth
@require_permission(Permission.COURSE_CREATE)
def create_course(current_user):
    """创建新课程"""
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_INPUT",
                        "message": "No data provided",
                    }
                ),
                400,
            )

        # 验证必填字段
        required_fields = ["name", "course_type"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MISSING_FIELDS",
                        "message": f'Missing required fields: {", ".join(missing_fields)}',
                    }
                ),
                400,
            )

        # 验证课程类型
        valid_types = ["one_to_one", "one_to_many"]
        if data["course_type"] not in valid_types:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_COURSE_TYPE",
                        "message": f'Invalid course type. Must be one of: {", ".join(valid_types)}',
                    }
                ),
                400,
            )

        # 设置最大学生数
        max_students = data.get("max_students", 1)
        if data["course_type"] == "one_to_one":
            max_students = 1
        elif data["course_type"] == "one_to_many":
            if max_students > 3:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_MAX_STUDENTS",
                            "message": "One-to-many courses can have at most 3 students",
                        }
                    ),
                    400,
                )
            max_students = min(max_students, 3)

        # 设置教师ID
        teacher_id = current_user.id
        if current_user.role == "admin" and data.get("teacher_id"):
            # 管理员可以指定教师
            teacher_id = data["teacher_id"]
            teacher = User.query.filter_by(
                id=teacher_id, role="teacher", is_active=True
            ).first()
            if not teacher:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_TEACHER",
                            "message": "Invalid teacher ID",
                        }
                    ),
                    400,
                )
        elif current_user.role != "teacher" and current_user.role != "admin":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "Only teachers and admins can create courses",
                    }
                ),
                403,
            )

        # 验证时间安排格式
        schedule = data.get("schedule")
        if schedule:
            try:
                # 验证JSON格式
                if isinstance(schedule, str):
                    json.loads(schedule)
                elif isinstance(schedule, dict):
                    schedule = json.dumps(schedule)
            except json.JSONDecodeError:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_SCHEDULE",
                            "message": "Invalid schedule format",
                        }
                    ),
                    400,
                )

        # 创建新课程
        new_course = Course(
            name=data["name"].strip(),
            description=data.get("description", "").strip(),
            course_type=data["course_type"],
            max_students=max_students,
            schedule=schedule,
            teacher_id=teacher_id,
            is_active=data.get("is_active", True),
        )

        db.session.add(new_course)
        db.session.commit()

        logger.info(f"Course created: {new_course.name} by {current_user.email}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"course": new_course.to_dict()},
                    "message": "Course created successfully",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating course: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to create course",
                }
            ),
            500,
        )


@courses_bp.route("/<int:course_id>", methods=["PUT"])
@require_auth
@require_permission(Permission.COURSE_UPDATE)
def update_course(course_id, current_user):
    """更新课程信息"""
    try:
        # 查找课程
        course = Course.query.get(course_id)
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

        # 权限检查：教师只能更新自己的课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only update your own courses",
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
                        "error": "INVALID_INPUT",
                        "message": "No data provided",
                    }
                ),
                400,
            )

        # 更新课程名称
        if "name" in data:
            course.name = data["name"].strip()

        # 更新课程描述
        if "description" in data:
            course.description = data["description"].strip()

        # 更新课程类型和最大学生数
        if "course_type" in data:
            valid_types = ["one_to_one", "one_to_many"]
            if data["course_type"] not in valid_types:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_COURSE_TYPE",
                            "message": f'Invalid course type. Must be one of: {", ".join(valid_types)}',
                        }
                    ),
                    400,
                )

            # 检查是否有学生已选课，如果有则不能修改课程类型
            enrolled_count = CourseEnrollment.query.filter_by(
                course_id=course.id, is_active=True
            ).count()

            if enrolled_count > 0 and data["course_type"] != course.course_type:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "CANNOT_CHANGE_TYPE",
                            "message": "Cannot change course type when students are enrolled",
                        }
                    ),
                    400,
                )

            course.course_type = data["course_type"]

            # 根据课程类型设置最大学生数
            if data["course_type"] == "one_to_one":
                course.max_students = 1
            elif data["course_type"] == "one_to_many":
                max_students = data.get("max_students", course.max_students)
                if max_students > 3:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "INVALID_MAX_STUDENTS",
                                "message": "One-to-many courses can have at most 3 students",
                            }
                        ),
                        400,
                    )
                course.max_students = min(max_students, 3)

        # 更新最大学生数（独立于课程类型）
        elif "max_students" in data:
            max_students = data["max_students"]
            if course.course_type == "one_to_one":
                max_students = 1
            elif course.course_type == "one_to_many":
                if max_students > 3:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "INVALID_MAX_STUDENTS",
                                "message": "One-to-many courses can have at most 3 students",
                            }
                        ),
                        400,
                    )
                max_students = min(max_students, 3)

            # 检查当前选课人数是否超过新的最大值
            enrolled_count = CourseEnrollment.query.filter_by(
                course_id=course.id, is_active=True
            ).count()

            if enrolled_count > max_students:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ENROLLED_EXCEEDS_LIMIT",
                            "message": f"Cannot reduce max students below current enrollment ({enrolled_count})",
                        }
                    ),
                    400,
                )

            course.max_students = max_students

        # 更新时间安排
        if "schedule" in data:
            schedule = data["schedule"]
            if schedule:
                try:
                    # 验证JSON格式
                    if isinstance(schedule, str):
                        json.loads(schedule)
                    elif isinstance(schedule, dict):
                        schedule = json.dumps(schedule)
                except json.JSONDecodeError:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "INVALID_SCHEDULE",
                                "message": "Invalid schedule format",
                            }
                        ),
                        400,
                    )
            course.schedule = schedule

        # 更新教师（仅管理员可以修改）
        if "teacher_id" in data:
            if current_user.role != "admin":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "Only administrators can change course teacher",
                        }
                    ),
                    403,
                )

            teacher = User.query.filter_by(
                id=data["teacher_id"], role="teacher", is_active=True
            ).first()
            if not teacher:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "INVALID_TEACHER",
                            "message": "Invalid teacher ID",
                        }
                    ),
                    400,
                )

            course.teacher_id = data["teacher_id"]

        # 更新激活状态（仅管理员可以修改）
        if "is_active" in data:
            if current_user.role != "admin":
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "ACCESS_DENIED",
                            "message": "Only administrators can change course status",
                        }
                    ),
                    403,
                )

            course.is_active = bool(data["is_active"])

        db.session.commit()

        logger.info(f"Course updated: {course.name} by {current_user.email}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"course": course.to_dict()},
                    "message": "Course updated successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating course {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to update course",
                }
            ),
            500,
        )


@courses_bp.route("/<int:course_id>", methods=["DELETE"])
@require_auth
@require_permission(Permission.COURSE_DELETE)
def delete_course(course_id, current_user):
    """删除课程（软删除）"""
    try:
        # 查找课程
        course = Course.query.get(course_id)
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

        # 权限检查：教师只能删除自己的课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only delete your own courses",
                    }
                ),
                403,
            )

        # 检查是否有学生选课
        enrolled_count = CourseEnrollment.query.filter_by(
            course_id=course.id, is_active=True
        ).count()

        if enrolled_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "COURSE_HAS_STUDENTS",
                        "message": "Cannot delete course with enrolled students",
                    }
                ),
                400,
            )

        # 软删除：设置为非激活状态
        course.is_active = False
        db.session.commit()

        logger.info(f"Course deactivated: {course.name} by {current_user.email}")

        return (
            jsonify({"success": True, "message": "Course deactivated successfully"}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to delete course",
                }
            ),
            500,
        )


# 选课/退课相关API
@courses_bp.route("/<int:course_id>/enroll", methods=["POST"])
@require_auth
def enroll_course(course_id, current_user):
    """学生选课"""
    try:
        # 只有学生可以选课
        if current_user.role != "student":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "Only students can enroll in courses",
                    }
                ),
                403,
            )

        # 查找课程
        course = Course.query.filter_by(id=course_id, is_active=True).first()
        if not course:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "COURSE_NOT_FOUND",
                        "message": "Course not found or inactive",
                    }
                ),
                404,
            )

        # 检查是否已经选过该课程
        existing_enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id, is_active=True
        ).first()

        if existing_enrollment:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ALREADY_ENROLLED",
                        "message": "You are already enrolled in this course",
                    }
                ),
                400,
            )

        # 检查课程是否已满
        current_enrollment_count = CourseEnrollment.query.filter_by(
            course_id=course_id, is_active=True
        ).count()

        if current_enrollment_count >= course.max_students:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "COURSE_FULL",
                        "message": "Course is full",
                    }
                ),
                400,
            )

        # 创建选课记录
        enrollment = CourseEnrollment(course_id=course_id, student_id=current_user.id)

        db.session.add(enrollment)
        db.session.commit()

        logger.info(f"Student {current_user.email} enrolled in course {course.name}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "enrollment": enrollment.to_dict(),
                        "course": course.to_dict(),
                    },
                    "message": "Successfully enrolled in course",
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error enrolling in course {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to enroll in course",
                }
            ),
            500,
        )


@courses_bp.route("/<int:course_id>/unenroll", methods=["DELETE"])
@require_auth
def unenroll_course(course_id, current_user):
    """学生退课"""
    try:
        # 只有学生可以退课
        if current_user.role != "student":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "Only students can unenroll from courses",
                    }
                ),
                403,
            )

        # 查找选课记录
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id, student_id=current_user.id, is_active=True
        ).first()

        if not enrollment:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "NOT_ENROLLED",
                        "message": "You are not enrolled in this course",
                    }
                ),
                404,
            )

        # 软删除选课记录
        enrollment.is_active = False
        db.session.commit()

        course = Course.query.get(course_id)
        logger.info(
            f"Student {current_user.email} unenrolled from course {course.name if course else course_id}"
        )

        return (
            jsonify(
                {"success": True, "message": "Successfully unenrolled from course"}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unenrolling from course {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to unenroll from course",
                }
            ),
            500,
        )


@courses_bp.route("/<int:course_id>/students", methods=["GET"])
@require_auth
def get_course_students(course_id, current_user):
    """获取课程学生列表"""
    try:
        # 查找课程
        course = Course.query.get(course_id)
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

        # 权限检查：教师只能查看自己的课程，管理员可以查看所有课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only view students of your own courses",
                    }
                ),
                403,
            )
        elif current_user.role == "student":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "Students cannot view course student lists",
                    }
                ),
                403,
            )

        # 获取选课学生列表
        enrollments = (
            db.session.query(CourseEnrollment, User)
            .join(User, CourseEnrollment.student_id == User.id)
            .filter(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.is_active == True,
                User.is_active == True,
            )
            .all()
        )

        students = []
        for enrollment, user in enrollments:
            student_data = user.to_dict()
            student_data["enrollment_date"] = enrollment.enrolled_at.isoformat()
            students.append(student_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "course": course.to_dict(),
                        "students": students,
                        "total_students": len(students),
                        "available_spots": course.max_students - len(students),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting course students {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get course students",
                }
            ),
            500,
        )


@courses_bp.route("/my-courses", methods=["GET"])
@require_auth
def get_my_courses(current_user):
    """获取我的课程（学生：已选课程，教师：教授课程）"""
    try:
        if current_user.role == "student":
            # 学生获取已选课程
            enrollments = (
                db.session.query(CourseEnrollment, Course, User)
                .join(Course, CourseEnrollment.course_id == Course.id)
                .join(User, Course.teacher_id == User.id)
                .filter(
                    CourseEnrollment.student_id == current_user.id,
                    CourseEnrollment.is_active == True,
                    Course.is_active == True,
                )
                .all()
            )

            courses = []
            for enrollment, course, teacher in enrollments:
                course_data = course.to_dict()
                course_data["teacher"] = {
                    "id": teacher.id,
                    "name": teacher.name,
                    "email": teacher.email,
                }
                course_data["enrollment_date"] = enrollment.enrolled_at.isoformat()
                courses.append(course_data)

        elif current_user.role == "teacher":
            # 教师获取教授课程
            courses_query = Course.query.filter_by(
                teacher_id=current_user.id, is_active=True
            ).all()

            courses = []
            for course in courses_query:
                course_data = course.to_dict()
                # 添加学生数量信息
                student_count = CourseEnrollment.query.filter_by(
                    course_id=course.id, is_active=True
                ).count()
                course_data["student_count"] = student_count
                course_data["available_spots"] = course.max_students - student_count
                courses.append(course_data)

        else:
            # 管理员获取所有课程
            courses_query = Course.query.filter_by(is_active=True).all()
            courses = []
            for course in courses_query:
                course_data = course.to_dict()
                # 添加教师和学生信息
                teacher = User.query.get(course.teacher_id)
                if teacher:
                    course_data["teacher"] = {
                        "id": teacher.id,
                        "name": teacher.name,
                        "email": teacher.email,
                    }
                student_count = CourseEnrollment.query.filter_by(
                    course_id=course.id, is_active=True
                ).count()
                course_data["student_count"] = student_count
                course_data["available_spots"] = course.max_students - student_count
                courses.append(course_data)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"courses": courses, "total_courses": len(courses)},
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting my courses for user {current_user.id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get courses",
                }
            ),
            500,
        )


# 课程时间安排相关API
@courses_bp.route("/<int:course_id>/schedule", methods=["PUT"])
@require_auth
@require_permission(Permission.COURSE_UPDATE)
def update_course_schedule(course_id, current_user):
    """更新课程时间安排"""
    try:
        # 查找课程
        course = Course.query.get(course_id)
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

        # 权限检查：教师只能更新自己的课程
        if current_user.role == "teacher" and course.teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only update your own course schedule",
                    }
                ),
                403,
            )

        data = request.get_json()
        if not data or "schedule" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_INPUT",
                        "message": "Schedule data is required",
                    }
                ),
                400,
            )

        schedule = data["schedule"]

        # 验证时间安排格式
        if not _validate_schedule_format(schedule):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_SCHEDULE_FORMAT",
                        "message": 'Invalid schedule format. Expected format: [{"day": "monday", "start_time": "09:00", "end_time": "10:00"}]',
                    }
                ),
                400,
            )

        # 检查教师时间冲突
        conflicts = _check_teacher_schedule_conflicts(
            current_user.id, schedule, course_id
        )
        if conflicts:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "SCHEDULE_CONFLICT",
                        "message": "Schedule conflicts with existing courses",
                        "conflicts": conflicts,
                    }
                ),
                400,
            )

        # 更新课程时间安排
        course.schedule = (
            json.dumps(schedule) if isinstance(schedule, list) else schedule
        )
        db.session.commit()

        logger.info(f"Course schedule updated: {course.name} by {current_user.email}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": {"course": course.to_dict()},
                    "message": "Course schedule updated successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating course schedule {course_id}: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to update course schedule",
                }
            ),
            500,
        )


@courses_bp.route("/schedule/conflicts", methods=["POST"])
@require_auth
def check_schedule_conflicts(current_user):
    """检查时间安排冲突"""
    try:
        data = request.get_json()
        if not data or "schedule" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_INPUT",
                        "message": "Schedule data is required",
                    }
                ),
                400,
            )

        schedule = data["schedule"]
        course_id = data.get("course_id")  # 可选，用于排除当前课程

        # 验证时间安排格式
        if not _validate_schedule_format(schedule):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "INVALID_SCHEDULE_FORMAT",
                        "message": "Invalid schedule format",
                    }
                ),
                400,
            )

        # 检查教师时间冲突
        teacher_conflicts = _check_teacher_schedule_conflicts(
            current_user.id, schedule, course_id
        )

        # 如果是学生，检查学生时间冲突
        student_conflicts = []
        if current_user.role == "student":
            student_conflicts = _check_student_schedule_conflicts(
                current_user.id, schedule, course_id
            )

        has_conflicts = bool(teacher_conflicts or student_conflicts)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "has_conflicts": has_conflicts,
                        "teacher_conflicts": teacher_conflicts,
                        "student_conflicts": student_conflicts,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error checking schedule conflicts: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to check schedule conflicts",
                }
            ),
            500,
        )


@courses_bp.route("/schedule/available-times", methods=["GET"])
@require_auth
def get_available_times(current_user):
    """获取可用时间段"""
    try:
        # 获取查询参数
        teacher_id = request.args.get("teacher_id", type=int)
        student_id = request.args.get("student_id", type=int)

        # 如果没有指定用户ID，使用当前用户
        if not teacher_id and not student_id:
            if current_user.role == "teacher":
                teacher_id = current_user.id
            elif current_user.role == "student":
                student_id = current_user.id

        # 权限检查
        if (
            teacher_id
            and current_user.role == "teacher"
            and teacher_id != current_user.id
        ):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only view your own available times",
                    }
                ),
                403,
            )

        if (
            student_id
            and current_user.role == "student"
            and student_id != current_user.id
        ):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only view your own available times",
                    }
                ),
                403,
            )

        # 获取已占用的时间段
        occupied_times = []

        if teacher_id:
            # 获取教师的课程时间
            teacher_courses = Course.query.filter_by(
                teacher_id=teacher_id, is_active=True
            ).all()

            for course in teacher_courses:
                if course.schedule:
                    try:
                        schedule = (
                            json.loads(course.schedule)
                            if isinstance(course.schedule, str)
                            else course.schedule
                        )
                        if isinstance(schedule, list):
                            occupied_times.extend(schedule)
                    except json.JSONDecodeError:
                        continue

        if student_id:
            # 获取学生的选课时间
            enrollments = (
                db.session.query(CourseEnrollment, Course)
                .join(Course, CourseEnrollment.course_id == Course.id)
                .filter(
                    CourseEnrollment.student_id == student_id,
                    CourseEnrollment.is_active == True,
                    Course.is_active == True,
                )
                .all()
            )

            for enrollment, course in enrollments:
                if course.schedule:
                    try:
                        schedule = (
                            json.loads(course.schedule)
                            if isinstance(course.schedule, str)
                            else course.schedule
                        )
                        if isinstance(schedule, list):
                            occupied_times.extend(schedule)
                    except json.JSONDecodeError:
                        continue

        # 生成可用时间段（这里简化处理，实际可以更复杂）
        all_time_slots = _generate_all_time_slots()
        available_times = _filter_available_times(all_time_slots, occupied_times)

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "available_times": available_times,
                        "occupied_times": occupied_times,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting available times: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get available times",
                }
            ),
            500,
        )


# 辅助函数
def _validate_schedule_format(schedule):
    """验证时间安排格式"""
    if not isinstance(schedule, list):
        return False

    valid_days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    for slot in schedule:
        if not isinstance(slot, dict):
            return False

        required_fields = ["day", "start_time", "end_time"]
        if not all(field in slot for field in required_fields):
            return False

        if slot["day"].lower() not in valid_days:
            return False

        # 验证时间格式 (HH:MM)
        try:
            start_time = datetime.strptime(slot["start_time"], "%H:%M").time()
            end_time = datetime.strptime(slot["end_time"], "%H:%M").time()

            if start_time >= end_time:
                return False
        except ValueError:
            return False

    return True


def _check_teacher_schedule_conflicts(teacher_id, new_schedule, exclude_course_id=None):
    """检查教师时间冲突"""
    conflicts = []

    # 获取教师的所有课程
    query = Course.query.filter_by(teacher_id=teacher_id, is_active=True)
    if exclude_course_id:
        query = query.filter(Course.id != exclude_course_id)

    existing_courses = query.all()

    for course in existing_courses:
        if not course.schedule:
            continue

        try:
            existing_schedule = (
                json.loads(course.schedule)
                if isinstance(course.schedule, str)
                else course.schedule
            )
            if not isinstance(existing_schedule, list):
                continue

            for new_slot in new_schedule:
                for existing_slot in existing_schedule:
                    if _time_slots_overlap(new_slot, existing_slot):
                        conflicts.append(
                            {
                                "course_id": course.id,
                                "course_name": course.name,
                                "conflicting_time": existing_slot,
                                "new_time": new_slot,
                            }
                        )
        except (json.JSONDecodeError, KeyError):
            continue

    return conflicts


def _check_student_schedule_conflicts(student_id, new_schedule, exclude_course_id=None):
    """检查学生时间冲突"""
    conflicts = []

    # 获取学生的所有选课
    query = (
        db.session.query(CourseEnrollment, Course)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .filter(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.is_active == True,
            Course.is_active == True,
        )
    )

    if exclude_course_id:
        query = query.filter(Course.id != exclude_course_id)

    enrollments = query.all()

    for enrollment, course in enrollments:
        if not course.schedule:
            continue

        try:
            existing_schedule = (
                json.loads(course.schedule)
                if isinstance(course.schedule, str)
                else course.schedule
            )
            if not isinstance(existing_schedule, list):
                continue

            for new_slot in new_schedule:
                for existing_slot in existing_schedule:
                    if _time_slots_overlap(new_slot, existing_slot):
                        conflicts.append(
                            {
                                "course_id": course.id,
                                "course_name": course.name,
                                "conflicting_time": existing_slot,
                                "new_time": new_slot,
                            }
                        )
        except (json.JSONDecodeError, KeyError):
            continue

    return conflicts


def _time_slots_overlap(slot1, slot2):
    """检查两个时间段是否重叠"""
    if slot1["day"].lower() != slot2["day"].lower():
        return False

    try:
        start1 = datetime.strptime(slot1["start_time"], "%H:%M").time()
        end1 = datetime.strptime(slot1["end_time"], "%H:%M").time()
        start2 = datetime.strptime(slot2["start_time"], "%H:%M").time()
        end2 = datetime.strptime(slot2["end_time"], "%H:%M").time()

        # 检查时间重叠
        return not (end1 <= start2 or end2 <= start1)
    except ValueError:
        return False


def _generate_all_time_slots():
    """生成所有可能的时间段"""
    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    time_slots = []

    # 生成从8:00到22:00的时间段，每小时一个
    for day in days:
        for hour in range(8, 22):
            time_slots.append(
                {
                    "day": day,
                    "start_time": f"{hour:02d}:00",
                    "end_time": f"{hour+1:02d}:00",
                }
            )

    return time_slots


def _filter_available_times(all_slots, occupied_slots):
    """过滤出可用时间段"""
    available = []

    for slot in all_slots:
        is_available = True
        for occupied in occupied_slots:
            if _time_slots_overlap(slot, occupied):
                is_available = False
                break

        if is_available:
            available.append(slot)

    return available


# 课程统计相关API
@courses_bp.route("/statistics/overview", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_course_statistics_overview(current_user):
    """获取课程统计概览"""
    try:
        # 基础统计
        total_courses = Course.query.filter_by(is_active=True).count()
        total_enrollments = CourseEnrollment.query.filter_by(is_active=True).count()

        # 按课程类型统计
        one_on_one_courses = Course.query.filter_by(
            course_type="one_on_one", is_active=True
        ).count()

        one_to_many_courses = Course.query.filter_by(
            course_type="one_to_many", is_active=True
        ).count()

        # 按教师统计（如果是管理员）
        teacher_stats = []
        if current_user.role == "admin":
            teachers = (
                db.session.query(
                    User.id,
                    User.name,
                    User.email,
                    db.func.count(Course.id).label("course_count"),
                )
                .outerjoin(
                    Course,
                    db.and_(Course.teacher_id == User.id, Course.is_active == True),
                )
                .filter(User.role == "teacher", User.is_active == True)
                .group_by(User.id, User.name, User.email)
                .all()
            )

            for teacher in teachers:
                teacher_stats.append(
                    {
                        "teacher_id": teacher.id,
                        "teacher_name": teacher.name,
                        "teacher_email": teacher.email,
                        "course_count": teacher.course_count,
                    }
                )

        # 如果是教师，只返回自己的统计
        elif current_user.role == "teacher":
            my_courses = Course.query.filter_by(
                teacher_id=current_user.id, is_active=True
            ).count()

            my_enrollments = (
                db.session.query(CourseEnrollment)
                .join(Course, CourseEnrollment.course_id == Course.id)
                .filter(
                    Course.teacher_id == current_user.id,
                    CourseEnrollment.is_active == True,
                    Course.is_active == True,
                )
                .count()
            )

            teacher_stats = [
                {
                    "teacher_id": current_user.id,
                    "teacher_name": current_user.name,
                    "teacher_email": current_user.email,
                    "course_count": my_courses,
                    "enrollment_count": my_enrollments,
                }
            ]

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "total_courses": total_courses,
                        "total_enrollments": total_enrollments,
                        "course_types": {
                            "one_on_one": one_on_one_courses,
                            "one_to_many": one_to_many_courses,
                        },
                        "teacher_statistics": teacher_stats,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting course statistics overview: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get course statistics",
                }
            ),
            500,
        )


@courses_bp.route("/statistics/enrollments", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_enrollment_statistics(current_user):
    """获取选课统计"""
    try:
        # 获取查询参数
        course_id = request.args.get("course_id", type=int)
        teacher_id = request.args.get("teacher_id", type=int)

        # 权限检查
        if current_user.role == "teacher":
            teacher_id = current_user.id  # 教师只能查看自己的统计

        # 构建查询
        query = (
            db.session.query(
                Course.id,
                Course.name,
                Course.course_type,
                Course.max_students,
                db.func.count(CourseEnrollment.id).label("enrolled_count"),
            )
            .outerjoin(
                CourseEnrollment,
                db.and_(
                    CourseEnrollment.course_id == Course.id,
                    CourseEnrollment.is_active == True,
                ),
            )
            .filter(Course.is_active == True)
        )

        if course_id:
            query = query.filter(Course.id == course_id)

        if teacher_id:
            query = query.filter(Course.teacher_id == teacher_id)

        query = query.group_by(
            Course.id, Course.name, Course.course_type, Course.max_students
        )

        results = query.all()

        enrollment_stats = []
        for result in results:
            enrollment_rate = (
                (result.enrolled_count / result.max_students * 100)
                if result.max_students > 0
                else 0
            )

            enrollment_stats.append(
                {
                    "course_id": result.id,
                    "course_name": result.name,
                    "course_type": result.course_type,
                    "max_students": result.max_students,
                    "enrolled_count": result.enrolled_count,
                    "available_spots": result.max_students - result.enrolled_count,
                    "enrollment_rate": round(enrollment_rate, 2),
                }
            )

        return (
            jsonify(
                {"success": True, "data": {"enrollment_statistics": enrollment_stats}}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting enrollment statistics: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get enrollment statistics",
                }
            ),
            500,
        )


@courses_bp.route("/statistics/popular-courses", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_popular_courses(current_user):
    """获取热门课程统计"""
    try:
        # 获取查询参数
        limit = request.args.get("limit", default=10, type=int)

        # 权限检查
        query = (
            db.session.query(
                Course.id,
                Course.name,
                Course.course_type,
                User.name.label("teacher_name"),
                db.func.count(CourseEnrollment.id).label("enrollment_count"),
            )
            .join(User, Course.teacher_id == User.id)
            .outerjoin(
                CourseEnrollment,
                db.and_(
                    CourseEnrollment.course_id == Course.id,
                    CourseEnrollment.is_active == True,
                ),
            )
            .filter(Course.is_active == True)
        )

        # 如果是教师，只查看自己的课程
        if current_user.role == "teacher":
            query = query.filter(Course.teacher_id == current_user.id)

        query = (
            query.group_by(Course.id, Course.name, Course.course_type, User.name)
            .order_by(db.func.count(CourseEnrollment.id).desc())
            .limit(limit)
        )

        results = query.all()

        popular_courses = []
        for result in results:
            popular_courses.append(
                {
                    "course_id": result.id,
                    "course_name": result.name,
                    "course_type": result.course_type,
                    "teacher_name": result.teacher_name,
                    "enrollment_count": result.enrollment_count,
                }
            )

        return (
            jsonify({"success": True, "data": {"popular_courses": popular_courses}}),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting popular courses: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get popular courses",
                }
            ),
            500,
        )


@courses_bp.route("/statistics/teacher-performance", methods=["GET"])
@require_auth
@require_permission(Permission.COURSE_READ)
def get_teacher_performance(current_user):
    """获取教师表现统计"""
    try:
        # 权限检查：只有管理员或教师本人可以查看
        teacher_id = request.args.get("teacher_id", type=int)

        if current_user.role == "teacher":
            teacher_id = current_user.id
        elif current_user.role != "admin" and teacher_id != current_user.id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "ACCESS_DENIED",
                        "message": "You can only view your own performance statistics",
                    }
                ),
                403,
            )

        # 如果没有指定教师ID且是管理员，返回所有教师统计
        if not teacher_id and current_user.role == "admin":
            teachers = (
                db.session.query(
                    User.id,
                    User.name,
                    User.email,
                    db.func.count(Course.id).label("total_courses"),
                    db.func.count(CourseEnrollment.id).label("total_enrollments"),
                )
                .outerjoin(
                    Course,
                    db.and_(Course.teacher_id == User.id, Course.is_active == True),
                )
                .outerjoin(
                    CourseEnrollment,
                    db.and_(
                        CourseEnrollment.course_id == Course.id,
                        CourseEnrollment.is_active == True,
                    ),
                )
                .filter(User.role == "teacher", User.is_active == True)
                .group_by(User.id, User.name, User.email)
                .all()
            )

            teacher_performance = []
            for teacher in teachers:
                avg_enrollment = (
                    (teacher.total_enrollments / teacher.total_courses)
                    if teacher.total_courses > 0
                    else 0
                )

                teacher_performance.append(
                    {
                        "teacher_id": teacher.id,
                        "teacher_name": teacher.name,
                        "teacher_email": teacher.email,
                        "total_courses": teacher.total_courses,
                        "total_enrollments": teacher.total_enrollments,
                        "average_enrollment_per_course": round(avg_enrollment, 2),
                    }
                )

            return (
                jsonify(
                    {
                        "success": True,
                        "data": {"teacher_performance": teacher_performance},
                    }
                ),
                200,
            )

        # 单个教师的详细统计
        teacher = User.query.filter_by(
            id=teacher_id, role="teacher", is_active=True
        ).first()
        if not teacher:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "TEACHER_NOT_FOUND",
                        "message": "Teacher not found",
                    }
                ),
                404,
            )

        # 获取教师的课程统计
        courses = Course.query.filter_by(teacher_id=teacher_id, is_active=True).all()

        course_details = []
        total_enrollments = 0

        for course in courses:
            enrollment_count = CourseEnrollment.query.filter_by(
                course_id=course.id, is_active=True
            ).count()

            total_enrollments += enrollment_count

            course_details.append(
                {
                    "course_id": course.id,
                    "course_name": course.name,
                    "course_type": course.course_type,
                    "max_students": course.max_students,
                    "enrolled_count": enrollment_count,
                    "enrollment_rate": round(
                        (enrollment_count / course.max_students * 100), 2
                    )
                    if course.max_students > 0
                    else 0,
                }
            )

        avg_enrollment = (total_enrollments / len(courses)) if courses else 0

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "teacher_info": {
                            "teacher_id": teacher.id,
                            "teacher_name": teacher.name,
                            "teacher_email": teacher.email,
                        },
                        "performance_summary": {
                            "total_courses": len(courses),
                            "total_enrollments": total_enrollments,
                            "average_enrollment_per_course": round(avg_enrollment, 2),
                        },
                        "course_details": course_details,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting teacher performance: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "INTERNAL_ERROR",
                    "message": "Failed to get teacher performance statistics",
                }
            ),
            500,
        )
