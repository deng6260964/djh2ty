import React from 'react'
import { Tag } from 'antd'
import { ClockCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import type { MyAssignment } from '../../types/models'
import { ASSIGNMENT_STATUSES } from '../../utils/constants'

interface AssignmentCardProps {
  assignment: MyAssignment
}

const AssignmentCard: React.FC<AssignmentCardProps> = ({ assignment }) => {
  const navigate = useNavigate()
  const dueDate = dayjs(assignment.due_date)
  const now = dayjs()
  const daysLeft = dueDate.diff(now, 'day')
  const isOverdue = daysLeft < 0 && assignment.status === 'pending'
  const isUrgent = daysLeft >= 0 && daysLeft <= 1 && assignment.status === 'pending'

  const statusConfig = ASSIGNMENT_STATUSES[assignment.status] || { label: assignment.status, color: 'default' }

  return (
    <div
      onClick={() => navigate(`/assignments/${assignment.id}`)}
      style={{
        background: '#fff',
        borderRadius: 8,
        padding: '12px 16px',
        marginBottom: 8,
        cursor: 'pointer',
        borderLeft: isOverdue ? '3px solid #EF4444' : isUrgent ? '3px solid #F59E0B' : '3px solid transparent',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontWeight: 500, fontSize: 15, color: '#111827', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {assignment.title}
        </span>
        <Tag color={statusConfig.color} style={{ margin: 0, marginLeft: 8, flexShrink: 0 }}>
          {statusConfig.label}
        </Tag>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#6B7280', fontSize: 13 }}>
        <Tag color="blue" style={{ margin: 0, fontSize: 12 }}>{assignment.subject}</Tag>
        <span style={{ color: isOverdue ? '#EF4444' : isUrgent ? '#F59E0B' : '#9CA3AF' }}>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {isOverdue ? '已过期' : isUrgent ? '即将截止' : dueDate.format('MM-DD')} 截止
        </span>
      </div>
      {assignment.status === 'graded' && assignment.score != null && (
        <div style={{ marginTop: 6, fontSize: 13, color: '#2563EB', fontWeight: 500 }}>
          得分: {assignment.score}分
        </div>
      )}
    </div>
  )
}

export default AssignmentCard
