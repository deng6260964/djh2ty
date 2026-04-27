import React, { useEffect, useState, useCallback } from 'react'
import { Button } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { coursesApi } from '../../api/courses'
import type { Course } from '../../types/models'
import CourseCalendar from './CourseCalendar'
import CourseCard from './CourseCard'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

const CoursesPage: React.FC = () => {
  const [year, setYear] = useState(dayjs().year())
  const [month, setMonth] = useState(dayjs().month() + 1)
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string | null>(dayjs().format('YYYY-MM-DD'))

  const fetchCourses = useCallback(async () => {
    setLoading(true)
    try {
      const startDate = `${year}-${String(month).padStart(2, '0')}-01`
      const lastDay = dayjs(startDate).daysInMonth()
      const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
      const result = await coursesApi.getMyCourses({
        start_date: startDate,
        end_date: endDate,
        page_size: 200,
      })
      setCourses(result.items)
    } catch {
      setCourses([])
    } finally {
      setLoading(false)
    }
  }, [year, month])

  useEffect(() => {
    fetchCourses()
  }, [fetchCourses])

  const handlePrevMonth = () => {
    if (month === 1) {
      setYear(year - 1)
      setMonth(12)
    } else {
      setMonth(month - 1)
    }
    setSelectedDate(null)
  }

  const handleNextMonth = () => {
    if (month === 12) {
      setYear(year + 1)
      setMonth(1)
    } else {
      setMonth(month + 1)
    }
    setSelectedDate(null)
  }

  const filteredCourses = selectedDate
    ? courses.filter((c) => dayjs(c.start_time).format('YYYY-MM-DD') === selectedDate)
    : courses

  const sortedCourses = [...filteredCourses].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  )

  return (
    <div>
      {/* Month navigation */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8,
        }}
      >
        <Button type="text" icon={<LeftOutlined />} onClick={handlePrevMonth} />
        <span style={{ fontWeight: 600, fontSize: 16, color: '#111827' }}>
          {year}年{month}月
        </span>
        <Button type="text" icon={<RightOutlined />} onClick={handleNextMonth} />
      </div>

      {/* Calendar */}
      <CourseCalendar
        year={year}
        month={month}
        courses={courses}
        selectedDate={selectedDate}
        onSelectDate={setSelectedDate}
      />

      {/* Course list */}
      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 8 }}>
          {selectedDate
            ? `${dayjs(selectedDate).format('M月D日')} 课程`
            : `${month}月全部课程`}
          <span style={{ color: '#9CA3AF', fontWeight: 400, marginLeft: 8 }}>
            ({sortedCourses.length})
          </span>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : sortedCourses.length === 0 ? (
          <EmptyState description={selectedDate ? '当日无课程' : '本月无课程'} />
        ) : (
          sortedCourses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))
        )}
      </div>
    </div>
  )
}

export default CoursesPage
