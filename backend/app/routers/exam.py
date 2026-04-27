import random
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.exam import ExamQuestion, Vocabulary, MockExam
from app.models.student import Student
from app.schemas.exam import (
    ExamQuestionCreate, ExamQuestionUpdate, ExamQuestionResponse, ExamQuestionListResponse,
    VocabularyCreate, VocabularyResponse, VocabularyListResponse,
    MockExamCreate, MockExamResponse,
)
from app.dependencies import get_admin_user
from app.models.user import User

router = APIRouter(prefix="/exam", tags=["考试辅导"])


@router.get("/questions", response_model=ExamQuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    question_type: Optional[str] = Query(None),
    difficulty: Optional[int] = Query(None),
    tags: Optional[str] = Query(None, description="逗号分隔的标签"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """真题列表"""
    query = select(ExamQuestion)
    conditions = []
    if subject:
        conditions.append(ExamQuestion.subject == subject)
    if year:
        conditions.append(ExamQuestion.year == year)
    if question_type:
        conditions.append(ExamQuestion.question_type == question_type)
    if difficulty:
        conditions.append(ExamQuestion.difficulty == difficulty)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        conditions.append(ExamQuestion.tags.contains(tag_list))
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(ExamQuestion.created_at.desc()).offset(offset).limit(page_size)
    )
    questions = result.scalars().all()

    items = [ExamQuestionResponse.model_validate(q) for q in questions]
    return ExamQuestionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/questions", response_model=ExamQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: ExamQuestionCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """添加真题"""
    question = ExamQuestion(
        subject=data.subject,
        year=data.year,
        question_type=data.question_type,
        content=data.content,
        options=data.options,
        answer=data.answer,
        explanation=data.explanation,
        difficulty=data.difficulty,
        tags=data.tags,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return ExamQuestionResponse.model_validate(question)


@router.put("/questions/{question_id}", response_model=ExamQuestionResponse)
async def update_question(
    question_id: int,
    data: ExamQuestionUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新真题"""
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=404,
            detail={"code": "QUESTION_NOT_FOUND", "message": "题目不存在"},
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)

    await db.commit()
    await db.refresh(question)
    return ExamQuestionResponse.model_validate(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除真题"""
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(
            status_code=404,
            detail={"code": "QUESTION_NOT_FOUND", "message": "题目不存在"},
        )
    await db.delete(question)
    await db.commit()


@router.get("/vocabulary", response_model=VocabularyListResponse)
async def list_vocabulary(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    subject: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """词汇列表"""
    query = select(Vocabulary)
    conditions = []
    if subject:
        conditions.append(Vocabulary.subject == subject)
    if level:
        conditions.append(Vocabulary.level == level)
    if search:
        conditions.append(Vocabulary.word.ilike(f"%{search}%"))
    if conditions:
        query = query.where(and_(*conditions))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Vocabulary.word).offset(offset).limit(page_size)
    )
    vocab_list = result.scalars().all()

    items = [VocabularyResponse.model_validate(v) for v in vocab_list]
    return VocabularyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/vocabulary", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary(
    data: VocabularyCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """添加词汇"""
    # 检查是否已存在
    existing = await db.execute(
        select(Vocabulary).where(
            Vocabulary.subject == data.subject,
            Vocabulary.word == data.word,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={"code": "DUPLICATE_WORD", "message": "该词汇已存在"},
        )

    vocab = Vocabulary(
        subject=data.subject,
        word=data.word,
        phonetic=data.phonetic,
        meaning=data.meaning,
        example=data.example,
        level=data.level,
    )
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return VocabularyResponse.model_validate(vocab)


@router.post("/mock-exams", response_model=MockExamResponse, status_code=status.HTTP_201_CREATED)
async def create_mock_exam(
    data: MockExamCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建模拟考试（从题库随机抽题）"""
    # 验证学生
    student_result = await db.execute(
        select(Student).where(Student.id == data.student_id)
    )
    if not student_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404,
            detail={"code": "STUDENT_NOT_FOUND", "message": "学生不存在"},
        )

    # 构建题目查询条件
    query = select(ExamQuestion).where(ExamQuestion.subject == data.subject)
    conditions = []
    if data.question_types:
        conditions.append(ExamQuestion.question_type.in_(data.question_types))
    if data.difficulty_range and len(data.difficulty_range) == 2:
        conditions.append(ExamQuestion.difficulty >= data.difficulty_range[0])
        conditions.append(ExamQuestion.difficulty <= data.difficulty_range[1])
    if data.tags:
        conditions.append(ExamQuestion.tags.overlap(data.tags))
    if conditions:
        query = query.where(and_(*conditions))

    result = await db.execute(query)
    all_questions = result.scalars().all()

    if not all_questions:
        raise HTTPException(
            status_code=400,
            detail={"code": "NO_QUESTIONS", "message": "没有符合条件的题目"},
        )

    # 随机抽取
    count = min(data.question_count, len(all_questions))
    selected = random.sample(all_questions, count)
    question_ids = [q.id for q in selected]

    mock_exam = MockExam(
        student_id=data.student_id,
        title=data.title,
        subject=data.subject,
        question_ids=question_ids,
        status="active",
    )
    db.add(mock_exam)
    await db.commit()
    await db.refresh(mock_exam)

    response = MockExamResponse.model_validate(mock_exam)
    response.questions = [ExamQuestionResponse.model_validate(q) for q in selected]
    return response


@router.get("/mock-exams/{exam_id}", response_model=MockExamResponse)
async def get_mock_exam(
    exam_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """模拟考试详情（含题目）"""
    result = await db.execute(
        select(MockExam).where(MockExam.id == exam_id)
    )
    mock_exam = result.scalar_one_or_none()
    if not mock_exam:
        raise HTTPException(
            status_code=404,
            detail={"code": "EXAM_NOT_FOUND", "message": "模拟考试不存在"},
        )

    # 获取题目详情
    questions = []
    if mock_exam.question_ids:
        q_result = await db.execute(
            select(ExamQuestion).where(ExamQuestion.id.in_(mock_exam.question_ids))
        )
        all_q = q_result.scalars().all()
        q_map = {q.id: q for q in all_q}
        questions = [
            ExamQuestionResponse.model_validate(q_map[qid])
            for qid in mock_exam.question_ids
            if qid in q_map
        ]

    response = MockExamResponse.model_validate(mock_exam)
    response.questions = questions
    return response
