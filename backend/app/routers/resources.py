import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete

from app.database import get_db
from app.models.resource import Resource, ResourceShare
from app.models.student import Student
from app.schemas.resource import (
    ResourceShareRequest, ResourceResponse, ResourceListResponse
)
from app.dependencies import get_admin_user, get_current_user, get_current_student
from app.models.user import User
from app.utils.file_handler import save_upload_file, delete_file, get_file_abs_path

router = APIRouter(prefix="/resources", tags=["资料管理"])


@router.get("/shared")
async def get_shared_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：分享给当前学生的资料"""
    query = select(Resource).join(
        ResourceShare,
        and_(
            ResourceShare.resource_id == Resource.id,
            ResourceShare.student_id == current_student.id,
        )
    )
    if subject:
        query = query.where(Resource.subject == subject)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
    )
    resources = result.scalars().all()

    items = [ResourceResponse.model_validate(r) for r in resources]
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/my")
async def get_my_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_student=Depends(get_current_student),
):
    """小程序端：我的资料（get_shared_resources 别名）"""
    return await get_shared_resources(page, page_size, None, db, current_student)


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """资料列表"""
    query = select(Resource)
    conditions = []
    if subject:
        conditions.append(Resource.subject == subject)
    if grade:
        conditions.append(Resource.grade == grade)
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
    )
    resources = result.scalars().all()

    items = []
    for r in resources:
        # 查询分享学生 ID 列表
        share_result = await db.execute(
            select(ResourceShare.student_id).where(ResourceShare.resource_id == r.id)
        )
        shared_students = [row[0] for row in share_result.all()]
        rr = ResourceResponse.model_validate(r)
        rr.shared_students = shared_students
        items.append(rr)

    return ResourceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/upload", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_resource(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    grade: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """上传资料文件"""
    relative_path, mime_type, file_size = await save_upload_file(file)

    resource = Resource(
        title=title,
        description=description,
        subject=subject,
        grade=grade,
        file_type=mime_type,
        original_name=file.filename or "unknown",
        file_path=relative_path,
        file_size=file_size,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """资料详情"""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=404,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "资料不存在"},
        )

    share_result = await db.execute(
        select(ResourceShare.student_id).where(ResourceShare.resource_id == resource_id)
    )
    shared_students = [row[0] for row in share_result.all()]

    rr = ResourceResponse.model_validate(resource)
    rr.shared_students = shared_students
    return rr


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除资料（同时删除文件）"""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=404,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "资料不存在"},
        )

    # 删除文件
    delete_file(resource.file_path)

    # 删除数据库记录（级联删除 resource_shares）
    await db.execute(
        delete(ResourceShare).where(ResourceShare.resource_id == resource_id)
    )
    await db.delete(resource)
    await db.commit()


@router.post("/{resource_id}/share")
async def share_resource(
    resource_id: int,
    data: ResourceShareRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """分享资料给指定学生"""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=404,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "资料不存在"},
        )

    shared_count = 0
    for student_id in data.student_ids:
        # 检查学生是否存在
        s_result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        if not s_result.scalar_one_or_none():
            continue

        # 检查是否已分享
        existing = await db.execute(
            select(ResourceShare).where(
                ResourceShare.resource_id == resource_id,
                ResourceShare.student_id == student_id,
            )
        )
        if not existing.scalar_one_or_none():
            share = ResourceShare(
                resource_id=resource_id,
                student_id=student_id,
            )
            db.add(share)
            shared_count += 1

    await db.commit()
    return {"shared": True, "shared_count": shared_count}


@router.delete("/{resource_id}/share/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    resource_id: int,
    student_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """撤销对某学生的资料分享"""
    result = await db.execute(
        select(ResourceShare).where(
            ResourceShare.resource_id == resource_id,
            ResourceShare.student_id == student_id,
        )
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(
            status_code=404,
            detail={"code": "SHARE_NOT_FOUND", "message": "未找到该分享记录"},
        )
    await db.delete(share)
    await db.commit()


@router.get("/{resource_id}/download")
async def download_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """下载资料文件（鉴权后返回文件）"""
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=404,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "资料不存在"},
        )

    # 权限检查：admin 可下载所有；student/parent 只能下载分享给自己的
    if current_user.role != "admin":
        # 查找该用户关联的学生
        s_result = await db.execute(
            select(Student).where(
                (Student.user_id == current_user.id) | (Student.parent_user_id == current_user.id),
                Student.is_active == True,
            )
        )
        student = s_result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "无权下载"})

        share_result = await db.execute(
            select(ResourceShare).where(
                ResourceShare.resource_id == resource_id,
                ResourceShare.student_id == student.id,
            )
        )
        if not share_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "无权下载此资料"})

    # 获取文件绝对路径
    abs_path = get_file_abs_path(resource.file_path)
    if not abs_path:
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_NOT_FOUND", "message": "文件不存在"},
        )

    # 编码文件名（处理中文）
    encoded_name = urllib.parse.quote(resource.original_name)
    return FileResponse(
        path=str(abs_path),
        media_type=resource.file_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
        },
    )
