import React, { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Tag, message } from 'antd'
import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { billingApi, type StudentAccount } from '../../api/billing'
import { coursesApi } from '../../api/courses'
import { assignmentsApi } from '../../api/assignments'
import { feedbackApi } from '../../api/feedback'
import type { Course, MyAssignment, MyFeedback } from '../../types/models'
import LoadingSpinner from '../../components/LoadingSpinner'
import EmptyState from '../../components/EmptyState'
import { formatCurrency, formatTime, formatDuration, getCourseStatusLabel } from '../../utils/format'

const sectionTitleStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  margin: '14px 0 8px',
  color: '#111827',
  fontSize: 15,
  fontWeight: 600,
}

const panelStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  padding: '12px 16px',
}

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const [account, setAccount] = useState<StudentAccount | null>(null)
  const [courses, setCourses] = useState<Course[]>([])
  const [assignments, setAssignments] = useState<MyAssignment[]>([])
  const [feedbacks, setFeedbacks] = useState<MyFeedback[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHome = async () => {
      setLoading(true)
      try {
        const today = dayjs().format('YYYY-MM-DD')
        const monthLater = dayjs().add(30, 'day').format('YYYY-MM-DD')
        const [accountResult, courseResult, assignmentResult, feedbackResult] = await Promise.all([
          billingApi.getMyAccount(),
          coursesApi.getMyCourses({
            start_date: today,
            end_date: monthLater,
            page_size: 20,
          }),
          assignmentsApi.getMyAssignments({
            status: 'pending',
            page_size: 3,
          }),
          feedbackApi.getMyFeedback({
            page: 1,
            page_size: 2,
          }),
        ])
        setAccount(accountResult)
        setCourses(courseResult.items)
        setAssignments(assignmentResult.items)
        setFeedbacks(feedbackResult.items)
      } catch {
        message.error('获取首页数据失败')
      } finally {
        setLoading(false)
      }
    }

    fetchHome()
  }, [])

  const nextCourses = useMemo(
    () =>
      [...courses]
        .filter((course) => course.status === 'scheduled')
        .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
        .slice(0, 3),
    [courses]
  )

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: '#6B7280', fontSize: 13 }}>{dayjs().format('M月D日 dddd')}</div>
        <div style={{ color: '#111827', fontSize: 22, fontWeight: 700 }}>
          {account?.student_name || '我的学习'}
        </div>
      </div>

      {account?.has_payment_alert && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12, borderRadius: 8 }}
          message="余额不足覆盖下一节课"
          description={
            account.next_course_projected_charge
              ? `下一节${account.next_course_subject || ''}预计扣费 ${formatCurrency(account.next_course_projected_charge)}`
              : undefined
          }
        />
      )}

      <div style={panelStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ color: '#6B7280', fontSize: 13 }}>
            <WalletOutlined style={{ marginRight: 6 }} />
            账户余额
          </div>
          {account?.main_subject_hourly_rate != null && (
            <Tag color="blue" style={{ margin: 0 }}>
              {account.main_subject || '课时'} {formatCurrency(account.main_subject_hourly_rate)}/小时
            </Tag>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
          <span
            style={{
              color: account && account.current_balance < 0 ? '#EF4444' : '#111827',
              fontSize: 30,
              lineHeight: 1,
              fontWeight: 700,
            }}
          >
            {formatCurrency(account?.current_balance)}
          </span>
          <span style={{ color: '#9CA3AF', fontSize: 12 }}>
            约 {account?.estimated_lessons_left ?? 0} 小时
          </span>
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 12, color: '#6B7280', fontSize: 12 }}>
          <span>累计收款 {formatCurrency(account?.total_received)}</span>
          <span>累计扣费 {formatCurrency(account?.total_charged)}</span>
        </div>
        <Button type="link" size="small" style={{ padding: 0, marginTop: 8 }} onClick={() => navigate('/account')}>
          查看账户明细
        </Button>
      </div>

      <div style={sectionTitleStyle}>
        <span>
          <CalendarOutlined style={{ marginRight: 6 }} />
          最近课程
        </span>
        <Button type="link" size="small" onClick={() => navigate('/courses')}>
          全部
        </Button>
      </div>
      {nextCourses.length === 0 ? (
        <EmptyState description="近期暂无课程" />
      ) : (
        nextCourses.map((course) => (
          <div key={course.id} style={{ ...panelStyle, marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ color: '#111827', fontWeight: 600 }}>{course.subject}</span>
              <Tag color="blue" style={{ margin: 0 }}>{getCourseStatusLabel(course.status)}</Tag>
            </div>
            <div style={{ color: '#6B7280', fontSize: 13 }}>
              <ClockCircleOutlined style={{ marginRight: 4 }} />
              {dayjs(course.start_time).format('M月D日')} {formatTime(course.start_time)} - {formatTime(course.end_time)}
              <span style={{ marginLeft: 4, color: '#9CA3AF' }}>({formatDuration(course.duration)})</span>
            </div>
          </div>
        ))
      )}

      <div style={sectionTitleStyle}>
        <span>
          <CheckCircleOutlined style={{ marginRight: 6 }} />
          待完成作业
        </span>
        <Button type="link" size="small" onClick={() => navigate('/assignments')}>
          全部
        </Button>
      </div>
      {assignments.length === 0 ? (
        <EmptyState description="暂无待完成作业" />
      ) : (
        assignments.map((assignment) => (
          <div key={assignment.id} style={{ ...panelStyle, marginBottom: 8 }} onClick={() => navigate(`/assignments/${assignment.id}`)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ color: '#111827', fontWeight: 600 }}>{assignment.title}</span>
              <Tag color="orange" style={{ margin: 0, flexShrink: 0 }}>{assignment.subject}</Tag>
            </div>
            <div style={{ color: '#9CA3AF', fontSize: 12, marginTop: 4 }}>
              {dayjs(assignment.due_date).format('M月D日')} 截止
            </div>
          </div>
        ))
      )}

      <div style={sectionTitleStyle}>
        <span>
          <FileTextOutlined style={{ marginRight: 6 }} />
          最新反馈
        </span>
        <Button type="link" size="small" onClick={() => navigate('/feedback')}>
          全部
        </Button>
      </div>
      {feedbacks.length === 0 ? (
        <EmptyState description="暂无课堂反馈" />
      ) : (
        feedbacks.map((feedback) => (
          <div key={feedback.id} style={{ ...panelStyle, marginBottom: 8 }} onClick={() => navigate(`/feedback/${feedback.id}`)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <Tag color="blue" style={{ margin: 0 }}>{feedback.subject}</Tag>
              <span style={{ color: '#9CA3AF', fontSize: 12 }}>
                {dayjs(feedback.course_date).format('M月D日')}
              </span>
            </div>
            <div style={{ color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {feedback.performance || feedback.knowledge_mastery || '课堂反馈已更新'}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

export default HomePage
