import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  message,
  Modal,
  Popconfirm,
  Radio,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { CalendarOutlined, CopyOutlined, LeftOutlined, PlusOutlined, RightOutlined, UnorderedListOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

import { coursesApi } from '../../api/courses'
import type { CopyWeekPreviewItem, Course, WeekCourseItem } from '../../types/models'
import {
  formatDate,
  formatDuration,
  formatMoney,
  formatTime,
  getCourseStatusColor,
  getCourseStatusLabel,
} from '../../utils/format'
import PageHeader from '../../components/PageHeader'
import CourseForm from './CourseForm'

type ViewMode = 'calendar' | 'list'

const { Text } = Typography

const weekdayLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const getWeekStart = (value: dayjs.Dayjs) => {
  const jsDay = value.day()
  const offset = jsDay === 0 ? -6 : 1 - jsDay
  return value.add(offset, 'day').startOf('day')
}

const CoursesPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('calendar')
  const [courses, setCourses] = useState<Course[]>([])
  const [weekCourses, setWeekCourses] = useState<WeekCourseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [currentWeekStart, setCurrentWeekStart] = useState(getWeekStart(dayjs()))
  const [formOpen, setFormOpen] = useState(false)
  const [formInitialDate, setFormInitialDate] = useState<string | undefined>()
  const [editingCourse, setEditingCourse] = useState<Course | null>(null)
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [copyModalOpen, setCopyModalOpen] = useState(false)
  const [copyPreviewLoading, setCopyPreviewLoading] = useState(false)
  const [copySubmitting, setCopySubmitting] = useState(false)
  const [copyPreview, setCopyPreview] = useState<CopyWeekPreviewItem[]>([])
  const [selectedCopyIds, setSelectedCopyIds] = useState<number[]>([])

  const fetchListCourses = async () => {
    setLoading(true)
    try {
      const result = await coursesApi.list({
        page,
        page_size: 20,
        status: filterStatus,
      })
      setCourses(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取课程列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchWeekCourses = async () => {
    setLoading(true)
    try {
      const result = await coursesApi.getWeek({
        week_start: currentWeekStart.format('YYYY-MM-DD'),
        status: filterStatus,
      })
      setWeekCourses(result.items)
    } catch {
      message.error('获取周课程视图失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (viewMode === 'calendar') {
      fetchWeekCourses()
      return
    }
    fetchListCourses()
  }, [viewMode, page, filterStatus, currentWeekStart])

  const handleStatusChange = async (id: number, status: string) => {
    try {
      await coursesApi.updateStatus(id, status)
      message.success('课程状态已更新')
      if (viewMode === 'calendar') {
        fetchWeekCourses()
      } else {
        fetchListCourses()
      }
    } catch {
      message.error('更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await coursesApi.delete(id)
      message.success('课程已删除')
      if (viewMode === 'calendar') {
        fetchWeekCourses()
      } else {
        fetchListCourses()
      }
    } catch {
      message.error('删除失败')
    }
  }

  const handleFormSuccess = () => {
    setEditingCourse(null)
    if (viewMode === 'calendar') {
      fetchWeekCourses()
    } else {
      fetchListCourses()
    }
  }

  const openCreateForm = (date?: string) => {
    setEditingCourse(null)
    setFormInitialDate(date)
    setFormOpen(true)
  }

  const openEditForm = (course: Course) => {
    setEditingCourse(course)
    setFormInitialDate(undefined)
    setFormOpen(true)
  }

  const loadCopyWeekPreview = async () => {
    setCopyPreviewLoading(true)
    try {
      const result = await coursesApi.copyWeekPreview({
        source_week_start: currentWeekStart.subtract(7, 'day').format('YYYY-MM-DD'),
        target_week_start: currentWeekStart.format('YYYY-MM-DD'),
      })
      setCopyPreview(result.items)
      setSelectedCopyIds(
        result.items
          .filter((item) => !item.has_conflict)
          .map((item) => item.source_course_id)
      )
    } catch {
      message.error('获取复制预览失败')
    } finally {
      setCopyPreviewLoading(false)
    }
  }

  const handleCopyWeek = async () => {
    setCopyModalOpen(true)
    await loadCopyWeekPreview()
  }

  const handleConfirmCopyWeek = async () => {
    if (!selectedCopyIds.length) {
      message.warning('请至少选择一节可复制课程')
      return
    }
    setCopySubmitting(true)
    try {
      const result = await coursesApi.copyWeekConfirm({
        source_week_start: currentWeekStart.subtract(7, 'day').format('YYYY-MM-DD'),
        target_week_start: currentWeekStart.format('YYYY-MM-DD'),
        selected_course_ids: selectedCopyIds,
      })
      message.success(`已复制 ${result.created_count} 节课程`)
      setCopyModalOpen(false)
      setCopyPreview([])
      setSelectedCopyIds([])
      fetchWeekCourses()
    } catch {
      message.error('复制课程失败')
    } finally {
      setCopySubmitting(false)
    }
  }

  const weekDays = useMemo(
    () => Array.from({ length: 7 }, (_, index) => currentWeekStart.add(index, 'day')),
    [currentWeekStart]
  )

  const weekData = useMemo(() => {
    return weekDays.map((day, index) => ({
      key: day.format('YYYY-MM-DD'),
      label: `${weekdayLabels[index]} ${day.format('MM/DD')}`,
      courses: weekCourses.filter((course) => dayjs(course.start_time).isSame(day, 'day')),
    }))
  }, [weekDays, weekCourses])

  const columns: ColumnsType<Course> = [
    {
      title: '日期',
      dataIndex: 'start_time',
      render: (v: string) => formatDate(v),
      width: 110,
    },
    {
      title: '时间',
      key: 'time',
      width: 130,
      render: (_: unknown, record: Course) =>
        `${formatTime(record.start_time)} - ${formatTime(record.end_time)}`,
    },
    {
      title: '学生',
      dataIndex: 'student_name',
      width: 90,
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '时长',
      dataIndex: 'duration',
      width: 90,
      render: (v: number) => formatDuration(v),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v: string) => (
        <Tag color={getCourseStatusColor(v)}>{getCourseStatusLabel(v)}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: Course) => (
        <Space size={4}>
          {record.status === 'scheduled' && (
            <Button type="link" size="small" onClick={() => openEditForm(record)}>
              调课
            </Button>
          )}
          {record.status === 'scheduled' && (
            <Button type="link" size="small" style={{ color: '#10B981' }} onClick={() => handleStatusChange(record.id, 'completed')}>
              完成
            </Button>
          )}
          {record.status === 'scheduled' && (
            <Button type="link" size="small" style={{ color: '#9CA3AF' }} onClick={() => handleStatusChange(record.id, 'cancelled')}>
              取消
            </Button>
          )}
          <Popconfirm
            title="确认删除此课程？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const copyColumns: ColumnsType<CopyWeekPreviewItem> = [
    {
      title: '复制',
      dataIndex: 'source_course_id',
      width: 72,
      render: (value: number, record: CopyWeekPreviewItem) => (
        <Checkbox
          checked={selectedCopyIds.includes(value)}
          disabled={record.has_conflict}
          onChange={(e) => {
            setSelectedCopyIds((prev) => {
              if (e.target.checked) {
                return [...prev, value]
              }
              return prev.filter((id) => id !== value)
            })
          }}
        />
      ),
    },
    {
      title: '学生 / 科目',
      key: 'student',
      width: 170,
      render: (_value: unknown, record: CopyWeekPreviewItem) => (
        <Space direction="vertical" size={0}>
          <Text strong>{record.student_name}</Text>
          <Text type="secondary">{record.subject}</Text>
        </Space>
      ),
    },
    {
      title: '来源时间',
      dataIndex: 'source_start_time',
      width: 170,
      render: (_value: string, record: CopyWeekPreviewItem) => (
        <Text>{formatDate(record.source_start_time)} {formatTime(record.source_start_time)}-{formatTime(record.source_end_time)}</Text>
      ),
    },
    {
      title: '复制后时间',
      dataIndex: 'target_start_time',
      width: 170,
      render: (_value: string, record: CopyWeekPreviewItem) => (
        <Text>{formatDate(record.target_start_time)} {formatTime(record.target_start_time)}-{formatTime(record.target_end_time)}</Text>
      ),
    },
    {
      title: '账户状态',
      key: 'balance',
      width: 160,
      render: (_value: unknown, record: CopyWeekPreviewItem) => (
        <Space direction="vertical" size={0}>
          <Text>扣费 {formatMoney(record.projected_charge)}</Text>
          <Text type="secondary">余额 {formatMoney(record.current_balance)}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 170,
      render: (_value: string, record: CopyWeekPreviewItem) => (
        <Space wrap>
          {record.has_conflict && <Tag color="error">时间冲突</Tag>}
          {!record.has_conflict && record.needs_payment && <Tag color="warning">会触发收费提醒</Tag>}
          {!record.has_conflict && !record.needs_payment && <Tag color="success">可直接复制</Tag>}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="课程管理"
        extra={
          <Space wrap>
            <Radio.Group
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              optionType="button"
              buttonStyle="solid"
            >
              <Radio.Button value="calendar">
                <CalendarOutlined /> 周视图
              </Radio.Button>
              <Radio.Button value="list">
                <UnorderedListOutlined /> 列表
              </Radio.Button>
            </Radio.Group>
            {viewMode === 'calendar' && (
                <Button icon={<CopyOutlined />} onClick={handleCopyWeek}>
                  复制上一周
                </Button>
            )}
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                openCreateForm(viewMode === 'calendar' ? currentWeekStart.format('YYYY-MM-DD') : undefined)
              }}
            >
              排课
            </Button>
          </Space>
        }
      />

      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} md={8}>
            <Select
              placeholder="状态筛选"
              style={{ width: '100%' }}
              allowClear
              value={filterStatus}
              onChange={(v) => {
                setFilterStatus(v)
                setPage(1)
              }}
              options={[
                { value: 'scheduled', label: '待上课' },
                { value: 'completed', label: '已完成' },
                { value: 'cancelled', label: '已取消' },
              ]}
            />
          </Col>
          {viewMode === 'calendar' && (
            <Col xs={24} md={16}>
              <Space wrap>
                <Button icon={<LeftOutlined />} onClick={() => setCurrentWeekStart((prev) => prev.subtract(7, 'day'))}>
                  上一周
                </Button>
                <Button onClick={() => setCurrentWeekStart(getWeekStart(dayjs()))}>本周</Button>
                <Button icon={<RightOutlined />} onClick={() => setCurrentWeekStart((prev) => prev.add(7, 'day'))}>
                  下一周
                </Button>
                <Typography.Text type="secondary">
                  {currentWeekStart.format('YYYY-MM-DD')} 至 {currentWeekStart.add(6, 'day').format('YYYY-MM-DD')}
                </Typography.Text>
              </Space>
            </Col>
          )}
        </Row>
      </Card>

      {viewMode === 'calendar' ? (
        <Row gutter={[16, 16]}>
          {weekData.map((day) => (
            <Col xs={24} sm={12} lg={8} xl={6} xxl={3} key={day.key}>
              <Card
                title={day.label}
                loading={loading}
                style={{
                  borderRadius: 12,
                  minHeight: 260,
                  borderColor: dayjs(day.key).day() >= 6 ? '#ffe7ba' : undefined,
                }}
                extra={
                  <Button
                    type="link"
                    size="small"
                    onClick={() => {
                      openCreateForm(day.key)
                    }}
                  >
                    新增
                  </Button>
                }
              >
                {!day.courses.length ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无课程" />
                ) : (
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    {day.courses.map((course) => (
                      <Card
                        key={course.id}
                        size="small"
                        style={{
                          borderRadius: 10,
                          background: course.needs_payment ? '#fff2f0' : '#f8fafc',
                          borderColor: course.needs_payment ? '#ffccc7' : '#e5e7eb',
                        }}
                      >
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                          <Space wrap>
                            <Text strong>{formatTime(course.start_time)}</Text>
                            <Tag>{course.subject}</Tag>
                            {course.needs_payment && <Tag color="error">需收费</Tag>}
                            {course.is_weekend && <Tag color="gold">周末</Tag>}
                          </Space>
                          <Text>{course.student_name}</Text>
                          <Text type="secondary">
                            预计扣费 {formatMoney(course.projected_charge)} · 余额 {formatMoney(course.current_balance)}
                          </Text>
                          <Space wrap>
                            <Tag color={getCourseStatusColor(course.status)}>{getCourseStatusLabel(course.status)}</Tag>
                            {course.status === 'scheduled' && (
                              <Button
                                size="small"
                                type="link"
                                style={{ paddingInline: 0 }}
                                onClick={async () => {
                                  const courseDetail = await coursesApi.get(course.id)
                                  openEditForm(courseDetail)
                                }}
                              >
                                调课
                              </Button>
                            )}
                            {course.status === 'scheduled' && (
                              <Button
                                size="small"
                                type="link"
                                style={{ paddingInline: 0, color: '#10B981' }}
                                onClick={() => handleStatusChange(course.id, 'completed')}
                              >
                                完成
                              </Button>
                            )}
                            {course.status === 'scheduled' && (
                              <Button
                                size="small"
                                type="link"
                                style={{ paddingInline: 0, color: '#9CA3AF' }}
                                onClick={() => handleStatusChange(course.id, 'cancelled')}
                              >
                                取消
                              </Button>
                            )}
                          </Space>
                        </Space>
                      </Card>
                    ))}
                  </Space>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Card style={{ borderRadius: 12 }}>
          <Table
            columns={columns}
            dataSource={courses}
            rowKey="id"
            loading={loading}
            scroll={{ x: 900 }}
            pagination={{
              current: page,
              pageSize: 20,
              total,
              onChange: (p) => setPage(p),
              showTotal: (t) => `共 ${t} 条`,
            }}
            locale={{ emptyText: '暂无课程记录' }}
          />
        </Card>
      )}

      <CourseForm
        open={formOpen}
        onClose={() => {
          setFormOpen(false)
          setEditingCourse(null)
        }}
        onSuccess={handleFormSuccess}
        initialDate={formInitialDate}
        initialCourse={editingCourse}
      />

      <Modal
        title="复制上一周课程"
        open={copyModalOpen}
        onCancel={() => {
          setCopyModalOpen(false)
          setCopyPreview([])
          setSelectedCopyIds([])
        }}
        onOk={handleConfirmCopyWeek}
        confirmLoading={copySubmitting}
        okText="确认复制"
        cancelText="取消"
        width={980}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Alert
            type="info"
            showIcon
            message={`将 ${currentWeekStart.subtract(7, 'day').format('YYYY-MM-DD')} 至 ${currentWeekStart.subtract(1, 'day').format('YYYY-MM-DD')} 的课程复制到 ${currentWeekStart.format('YYYY-MM-DD')} 这一周`}
          />
          <Space wrap>
            <Tag color="success">可复制 {copyPreview.filter((item) => !item.has_conflict).length}</Tag>
            <Tag color="error">冲突 {copyPreview.filter((item) => item.has_conflict).length}</Tag>
            <Tag color="warning">需收费提醒 {copyPreview.filter((item) => item.needs_payment).length}</Tag>
            <Tag>已选 {selectedCopyIds.length}</Tag>
          </Space>
          <Table
            rowKey="source_course_id"
            columns={copyColumns}
            dataSource={copyPreview}
            loading={copyPreviewLoading}
            pagination={false}
            scroll={{ x: 860 }}
            locale={{ emptyText: '上一周暂无可复制课程' }}
          />
        </Space>
      </Modal>
    </div>
  )
}

export default CoursesPage
