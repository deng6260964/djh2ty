# -*- coding: utf-8 -*-
"""
文件上传路由模块
提供文件上传、下载和管理功能
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from app.database import db
from app.models.file import File
from app.models.user import User
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission

# 创建蓝图
files_bp = Blueprint("files", __name__, url_prefix="/api/files")


@files_bp.route("/upload", methods=["POST"], strict_slashes=False)
@jwt_required()
def upload_file():
    """上传文件

    支持的文件类型:
    - homework_attachment: 作业附件
    - submission_file: 作业提交文件
    - question_audio: 题目音频
    - question_image: 题目图片
    - course_material: 课程资料
    - avatar: 头像
    - other: 其他文件
    """
    try:
        current_user_id = get_jwt_identity()

        # 检查是否有文件
        if "file" not in request.files:
            return jsonify({"error": "没有选择文件"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "没有选择文件"}), 400

        # 获取文件类别
        category = request.form.get("category", "other")

        # 验证文件类型
        if not File.is_allowed_file(file.filename, category):
            allowed_extensions = File.get_allowed_extensions().get(category, [])
            return (
                jsonify({"error": f'不支持的文件类型，允许的类型: {", ".join(allowed_extensions)}'}),
                400,
            )

        # 检查文件大小
        max_size = File.get_max_file_size(category)
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头

        if file_size > max_size:
            return jsonify({"error": f"文件大小超过限制，最大允许 {max_size // (1024*1024)}MB"}), 400

        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}{file_extension}"

        # 创建上传目录
        upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], category)
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, stored_filename)
        file.save(file_path)

        # 保存文件信息到数据库
        file_record = File(
            filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            file_extension=file_extension,
            file_category=category,
            uploaded_by=current_user_id,
        )

        db.session.add(file_record)
        db.session.commit()

        return jsonify({"message": "文件上传成功", "file": file_record.to_dict()}), 201

    except RequestEntityTooLarge:
        return jsonify({"error": "文件大小超过服务器限制"}), 413
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"文件上传失败: {str(e)}")
        return jsonify({"error": "文件上传失败"}), 500


@files_bp.route("/<int:file_id>/download", methods=["GET"])
@jwt_required()
def download_file(file_id):
    """下载文件"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        # 获取文件记录
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({"error": "文件不存在"}), 404

        # 权限检查
        can_access = False

        # 文件上传者可以访问
        if file_record.uploaded_by == current_user_id:
            can_access = True

        # 教师可以访问自己课程相关的文件
        elif current_user.role == "teacher":
            # 检查是否是作业附件或提交文件
            if file_record.file_category in ["homework_attachment", "submission_file"]:
                # 通过作业或提交记录检查权限
                # 这里需要根据具体的关联关系来实现
                can_access = True  # 简化处理，实际应该检查具体权限

        # 学生可以访问自己提交的文件和已发布作业的附件
        elif current_user.role == "student":
            if (
                file_record.file_category == "submission_file"
                and file_record.uploaded_by == current_user_id
            ):
                can_access = True
            elif file_record.file_category == "homework_attachment":
                # 检查学生是否选修了相关课程
                can_access = True  # 简化处理

        if not can_access:
            return jsonify({"error": "没有权限访问此文件"}), 403

        # 检查文件是否存在
        if not os.path.exists(file_record.file_path):
            return jsonify({"error": "文件不存在"}), 404

        # 增加下载次数
        file_record.increment_download_count()

        # 返回文件
        return send_file(
            file_record.file_path,
            as_attachment=True,
            download_name=file_record.filename,
        )

    except Exception as e:
        current_app.logger.error(f"文件下载失败: {str(e)}")
        return jsonify({"error": "文件下载失败"}), 500


@files_bp.route("/<int:file_id>", methods=["GET"])
@jwt_required()
def get_file_info(file_id):
    """获取文件信息"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({"error": "文件不存在"}), 404

        # 基本权限检查（简化版本）
        if file_record.uploaded_by != current_user_id and current_user.role not in [
            "teacher",
            "admin",
        ]:
            return jsonify({"error": "没有权限访问此文件"}), 403

        return jsonify({"file": file_record.to_dict()}), 200

    except Exception as e:
        current_app.logger.error(f"获取文件信息失败: {str(e)}")
        return jsonify({"error": "获取文件信息失败"}), 500


@files_bp.route("/<int:file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    """删除文件"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user:
            return jsonify({"error": "用户不存在"}), 404

        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({"error": "文件不存在"}), 404

        # 权限检查：只有文件上传者或管理员可以删除
        if file_record.uploaded_by != current_user_id and current_user.role != "admin":
            return jsonify({"error": "没有权限删除此文件"}), 403

        # 检查文件是否被引用
        # 这里应该检查文件是否被作业或提交记录引用
        # 简化处理，实际应该检查具体的引用关系

        # 删除物理文件
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)

        # 删除数据库记录
        db.session.delete(file_record)
        db.session.commit()

        return jsonify({"message": "文件删除成功"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"文件删除失败: {str(e)}")
        return jsonify({"error": "文件删除失败"}), 500


@files_bp.route("/my-files", methods=["GET"])
@jwt_required()
def get_my_files():
    """获取当前用户上传的文件列表"""
    try:
        current_user_id = get_jwt_identity()

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        category = request.args.get("category")

        # 构建查询
        query = File.query.filter_by(uploaded_by=current_user_id)

        if category:
            query = query.filter_by(file_category=category)

        # 排序和分页
        query = query.order_by(File.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        files = [file.to_dict() for file in pagination.items]

        return (
            jsonify(
                {
                    "files": files,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages,
                        "has_next": pagination.has_next,
                        "has_prev": pagination.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({"error": "获取文件列表失败"}), 500
