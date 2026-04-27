import React from 'react'
import dayjs from 'dayjs'
import type { Course } from '../../types/models'

interface CourseCalendarProps {
  year: number
  month: number
  courses: Course[]
  selectedDate: string | null
  onSelectDate: (date: string) => void
}

const WEEKDAY_LABELS = ['日', '一', '二', '三', '四', '五', '六']

const CourseCalendar: React.FC<CourseCalendarProps> = ({
  year,
  month,
  courses,
  selectedDate,
  onSelectDate,
}) => {
  const firstDay = dayjs(`${year}-${String(month).padStart(2, '0')}-01`)
  const daysInMonth = firstDay.daysInMonth()
  const startWeekday = firstDay.day()
  const today = dayjs().format('YYYY-MM-DD')

  // Build a set of dates that have courses
  const courseDates = new Set<string>()
  for (const c of courses) {
    const dateKey = dayjs(c.start_time).format('YYYY-MM-DD')
    courseDates.add(dateKey)
  }

  const cells: React.ReactNode[] = []

  // Empty cells before first day
  for (let i = 0; i < startWeekday; i++) {
    cells.push(<div key={`empty-${i}`} style={{ flex: '0 0 calc(100% / 7)' }} />)
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const isToday = dateStr === today
    const isSelected = dateStr === selectedDate
    const hasCourse = courseDates.has(dateStr)

    cells.push(
      <div
        key={day}
        onClick={() => onSelectDate(dateStr)}
        style={{
          flex: '0 0 calc(100% / 7)',
          textAlign: 'center',
          padding: '6px 0',
          cursor: 'pointer',
        }}
      >
        <div
          style={{
            width: 32,
            height: 32,
            lineHeight: '32px',
            borderRadius: '50%',
            margin: '0 auto',
            fontSize: 14,
            fontWeight: isToday ? 600 : 400,
            background: isSelected ? '#2563EB' : isToday ? '#EFF6FF' : 'transparent',
            color: isSelected ? '#fff' : isToday ? '#2563EB' : '#374151',
          }}
        >
          {day}
        </div>
        {hasCourse && (
          <div
            style={{
              width: 4,
              height: 4,
              borderRadius: '50%',
              background: isSelected ? '#fff' : '#2563EB',
              margin: '2px auto 0',
            }}
          />
        )}
      </div>
    )
  }

  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: '8px 4px' }}>
      {/* Weekday headers */}
      <div style={{ display: 'flex' }}>
        {WEEKDAY_LABELS.map((label) => (
          <div
            key={label}
            style={{
              flex: '0 0 calc(100% / 7)',
              textAlign: 'center',
              fontSize: 12,
              color: '#9CA3AF',
              padding: '4px 0',
            }}
          >
            {label}
          </div>
        ))}
      </div>
      {/* Day cells */}
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>{cells}</div>
    </div>
  )
}

export default CourseCalendar
