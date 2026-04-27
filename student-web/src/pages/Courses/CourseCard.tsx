import React from 'react'
import { Tag } from 'antd'
import { ClockCircleOutlined, EnvironmentOutlined } from '@ant-design/icons'
import type { Course } from '../../types/models'
import { formatTime, formatDuration, getCourseStatusColor, getCourseStatusLabel } from '../../utils/format'

interface CourseCardProps {
  course: Course
}

const CourseCard: React.FC<CourseCardProps> = ({ course }) => {
  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 8,
        padding: '12px 16px',
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 500, fontSize: 15, color: '#111827' }}>
          {course.subject}
        </span>
        <Tag color={getCourseStatusColor(course.status)} style={{ margin: 0 }}>
          {getCourseStatusLabel(course.status)}
        </Tag>
      </div>
      <div style={{ display: 'flex', gap: 16, color: '#6B7280', fontSize: 13 }}>
        <span>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {formatTime(course.start_time)} - {formatTime(course.end_time)}
          <span style={{ marginLeft: 4, color: '#9CA3AF' }}>({formatDuration(course.duration)})</span>
        </span>
        {course.location && (
          <span>
            <EnvironmentOutlined style={{ marginRight: 4 }} />
            {course.location}
          </span>
        )}
      </div>
      {course.notes && (
        <div style={{ marginTop: 6, fontSize: 12, color: '#9CA3AF' }}>
          {course.notes}
        </div>
      )}
    </div>
  )
}

export default CourseCard
