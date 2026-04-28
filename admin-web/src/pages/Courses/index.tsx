import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Radio,
  Row,
  Select,
  Space,
  Table,
  Tag,
  TimePicker,
  Typography,
} from 'antd'
import { CalendarOutlined, CopyOutlined, LeftOutlined, PlusOutlined, RightOutlined, UnorderedListOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

import { coursesApi } from '../../api/courses'
import type { CopyWeekPreviewItem, Course, CourseCompleteFormData, CourseDetailV2, WeekCourseItem } from '../../types/models'
import {
  formatDate,
  formatDateTime,
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
  const [detailOpen, setDetailOpen] = useState(false)
  const [courseDetail, setCourseDetail] = useState<CourseDetailV2 | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [completeSubmitting, setCompleteSubmitting] = useState(false)
  const [leaveOpen, setLeaveOpen] = useState(false)
  const [leaveCourse, setLeaveCourse] = useState<Course | null>(null)
  const [makeupOpen, setMakeupOpen] = useState(false)
  const [makeupCourses, setMakeupCourses] = useState<Course[]>([])
  const [makeupLoading, setMakeupLoading] = useState(false)
  const [completeForm] = Form.useForm<CourseCompleteFormData & { assignment_due_date?: dayjs.Dayjs }>()
  const [leaveForm] = Form.useForm<{ leave_type: 'student' | 'teacher'; reason?: string }>()
  const [makeupForm] = Form.useForm<{ course_id: number; date: dayjs.Dayjs; start_time: dayjs.Dayjs; end_time: dayjs.Dayjs; notes?: string }>()

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

  const refreshCurrentView = () => {
    if (viewMode === 'calendar') {
      fetchWeekCourses()
    } else {
      fetchListCourses()
    }
  }

  const openCourseDetail = async (id: number) => {
    setDetailOpen(true)
    setDetailLoading(true)
    completeForm.resetFields()
    try {
      const detail = await coursesApi.getDetailV2(id)
      setCourseDetail(detail)
    } catch {
      message.error('获取课程详情失败')
      setDetailOpen(false)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleCompleteCourse = async (values: CourseCompleteFormData & { assignment_due_date?: dayjs.Dayjs }) => {
    if (!courseDetail) return
    setCompleteSubmitting(true)
    try {
      const assignmentEnabled = Boolean(values.assignment?.enabled)
      const result = await coursesApi.complete(courseDetail.course.id, {
        performance: values.performance,
        knowledge_mastery: values.knowledge_mastery,
        problems: values.problems,
        next_plan: values.next_plan,
        rating: values.rating,
        assignment: {
          enabled: assignmentEnabled,
          title: values.assignment?.title,
          content: values.assignment?.content,
          due_date: values.assignment_due_date?.format('YYYY-MM-DD'),
        },
      })
      message.success(`课程已完成，自动扣费 ${formatMoney(result.charge_amount)}`)
      setDetailOpen(false)
      setCourseDetail(null)
      refreshCurrentView()
    } catch {
      message.error('完成课程失败，请检查课后记录和作业信息')
    } finally {
      setCompleteSubmitting(false)
    }
  }

  const openLeaveModal = (course: Course) => {
    setLeaveCourse(course)
    leaveForm.setFieldsValue({ leave_type: 'student' })
    setLeaveOpen(true)
  }

  const handleLeave = async (values: { leave_type: 'student' | 'teacher'; reason?: string }) => {
    if (!leaveCourse) return
    try {
      await coursesApi.leave(leaveCourse.id, {
        leave_type: values.leave_type,
        reason: values.reason,
        turn_to_makeup: true,
      })
      message.success('已转入待补课池')
      setLeaveOpen(false)
      setLeaveCourse(null)
      refreshCurrentView()
    } catch {
      message.error('请假处理失败')
    }
  }

  const openMakeupPool = async () => {
    setMakeupOpen(true)
    setMakeupLoading(true)
    try {
      const result = await coursesApi.getMakeupPool()
      setMakeupCourses(result.items)
    } catch {
      message.error('获取待补课池失败')
    } finally {
      setMakeupLoading(false)
    }
  }

  const handleScheduleMakeup = async (values: { course_id: number; date: dayjs.Dayjs; start_time: dayjs.Dayjs; end_time: dayjs.Dayjs; notes?: string }) => {
    const start = values.date.hour(values.start_time.hour()).minute(values.start_time.minute()).second(0)
    const end = values.date.hour(values.end_time.hour()).minute(values.end_time.minute()).second(0)
    try {
      await coursesApi.scheduleMakeup(values.course_id, {
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        notes: values.notes,
      })
      message.success('补课已安排')
      makeupForm.resetFields()
      const result = await coursesApi.getMakeupPool()
      setMakeupCourses(result.items)
      refreshCurrentView()
    } catch {
      message.error('安排补课失败，请检查时间冲突')
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
            <Button type="link" size="small" onClick={() => openCourseDetail(record.id)}>
              详情
            </Button>
          )}
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
            <Button type="link" size="small" style={{ color: '#F59E0B' }} onClick={() => openLeaveModal(record)}>
              请假
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
            <Button onClick={openMakeupPool}>待补课池</Button>
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
                                onClick={() => openCourseDetail(course.id)}
                              >
                                详情
                              </Button>
                            )}
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
                                style={{ paddingInline: 0, color: '#F59E0B' }}
                                onClick={async () => {
                                  const courseDetail = await coursesApi.get(course.id)
                                  openLeaveModal(courseDetail)
                                }}
                              >
                                请假
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
        title="课程详情"
        open={detailOpen}
        onCancel={() => {
          setDetailOpen(false)
          setCourseDetail(null)
        }}
        footer={null}
        width={860}
        destroyOnClose
      >
        {detailLoading || !courseDetail ? (
          <Empty description="正在加载课程详情" />
        ) : (
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Alert
              type={courseDetail.account.needs_payment ? 'warning' : 'info'}
              showIcon
              message={`${courseDetail.student.name} · ${courseDetail.course.subject} · ${formatDate(courseDetail.course.start_time)} ${formatTime(courseDetail.course.start_time)}-${formatTime(courseDetail.course.end_time)}`}
              description={`当前余额 ${formatMoney(courseDetail.account.current_balance)}，本节预计扣费 ${formatMoney(courseDetail.projected_charge)}`}
            />
            <Row gutter={16}>
              <Col xs={24} md={12}>
                <Text strong>最近反馈</Text>
                {!courseDetail.recent_feedback.length ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无反馈" />
                ) : (
                  <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
                    {courseDetail.recent_feedback.map((item) => (
                      <Alert key={item.id} type="info" message={item.performance} description={item.next_plan || item.problems || '无补充'} />
                    ))}
                  </Space>
                )}
              </Col>
              <Col xs={24} md={12}>
                <Text strong>最近作业</Text>
                {!courseDetail.recent_assignments.length ? (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无作业" />
                ) : (
                  <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
                    {courseDetail.recent_assignments.map((item) => (
                      <Alert key={item.id} type="success" message={item.title} description={`${formatDate(item.due_date)} · ${item.status}`} />
                    ))}
                  </Space>
                )}
              </Col>
            </Row>
            <Form form={completeForm} layout="vertical" onFinish={handleCompleteCourse}>
              <Form.Item name="performance" label="课后记录" rules={[{ required: true, message: '请填写课后记录' }]}>
                <Input.TextArea rows={3} placeholder="记录本节课内容、表现和关键结论" />
              </Form.Item>
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name="knowledge_mastery" label="知识掌握">
                    <Input.TextArea rows={2} placeholder="本节知识点掌握情况" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="problems" label="问题与风险">
                    <Input.TextArea rows={2} placeholder="需要关注的问题" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={12}>
                <Col xs={24} md={18}>
                  <Form.Item name="next_plan" label="下节安排">
                    <Input placeholder="下节课计划" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={6}>
                  <Form.Item name="rating" label="评分">
                    <InputNumber min={1} max={5} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item name={['assignment', 'enabled']} valuePropName="checked">
                <Checkbox>同时布置作业</Checkbox>
              </Form.Item>
              <Row gutter={12}>
                <Col xs={24} md={8}>
                  <Form.Item name={['assignment', 'title']} label="作业标题">
                    <Input placeholder="选填" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item name="assignment_due_date" label="截止日期">
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item name={['assignment', 'content']} label="作业内容">
                    <Input placeholder="选填" />
                  </Form.Item>
                </Col>
              </Row>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => setDetailOpen(false)}>取消</Button>
                <Button type="primary" htmlType="submit" loading={completeSubmitting}>保存并完成课程</Button>
              </Space>
            </Form>
          </Space>
        )}
      </Modal>

      <Modal
        title="请假 / 转待补"
        open={leaveOpen}
        onCancel={() => setLeaveOpen(false)}
        onOk={() => leaveForm.submit()}
        okText="确认转入待补"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={leaveForm} layout="vertical" onFinish={handleLeave} style={{ marginTop: 16 }}>
          <Form.Item name="leave_type" label="请假类型" rules={[{ required: true, message: '请选择请假类型' }]}>
            <Radio.Group>
              <Radio value="student">学生请假</Radio>
              <Radio value="teacher">老师请假</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="reason" label="原因">
            <Input.TextArea rows={3} placeholder="记录请假原因，便于之后安排补课" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="待补课池"
        open={makeupOpen}
        onCancel={() => setMakeupOpen(false)}
        footer={null}
        width={760}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Table
            rowKey="id"
            size="small"
            loading={makeupLoading}
            dataSource={makeupCourses}
            pagination={false}
            columns={[
              { title: '学生', dataIndex: 'student_name' },
              { title: '科目', dataIndex: 'subject' },
              { title: '原时间', dataIndex: 'start_time', render: (v: string) => formatDateTime(v) },
              { title: '状态', dataIndex: 'status', render: (v: string) => <Tag color={getCourseStatusColor(v)}>{getCourseStatusLabel(v)}</Tag> },
            ]}
            locale={{ emptyText: '暂无待补课程' }}
          />
          <Form form={makeupForm} layout="vertical" onFinish={handleScheduleMakeup}>
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item name="course_id" label="待补课程" rules={[{ required: true, message: '请选择待补课程' }]}>
                  <Select options={makeupCourses.map((course) => ({ value: course.id, label: `${course.student_name} ${course.subject} ${formatDate(course.start_time)}` }))} />
                </Form.Item>
              </Col>
              <Col xs={24} md={8}>
                <Form.Item name="date" label="补课日期" rules={[{ required: true, message: '请选择日期' }]}>
                  <DatePicker style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col xs={12} md={4}>
                <Form.Item name="start_time" label="开始" rules={[{ required: true, message: '请选择开始时间' }]}>
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col xs={12} md={4}>
                <Form.Item name="end_time" label="结束" rules={[{ required: true, message: '请选择结束时间' }]}>
                  <TimePicker format="HH:mm" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="notes" label="备注">
              <Input placeholder="选填" />
            </Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button type="primary" htmlType="submit">安排补课</Button>
            </Space>
          </Form>
        </Space>
      </Modal>

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
