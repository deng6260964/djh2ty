import React from 'react'
import { Tag, Rate } from 'antd'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import type { MyFeedback } from '../../types/models'

interface FeedbackCardProps {
  feedback: MyFeedback
}

const FeedbackCard: React.FC<FeedbackCardProps> = ({ feedback }) => {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/feedback/${feedback.id}`)}
      style={{
        background: '#fff',
        borderRadius: 8,
        padding: '12px 16px',
        marginBottom: 8,
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tag color="blue" style={{ margin: 0 }}>{feedback.subject}</Tag>
          <span style={{ fontSize: 13, color: '#9CA3AF' }}>
            {dayjs(feedback.course_date).format('MM-DD')}
          </span>
        </div>
        {feedback.rating != null && feedback.rating > 0 && (
          <Rate disabled defaultValue={feedback.rating} style={{ fontSize: 14 }} />
        )}
      </div>
      <div style={{ fontSize: 14, color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {feedback.performance}
      </div>
    </div>
  )
}

export default FeedbackCard
