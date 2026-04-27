import React, { useEffect, useState } from 'react'
import { Alert, Descriptions, Drawer, Row, Col, Spin, Statistic, Table, Tabs, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { studentsApi } from '../../api/students'
import type { Student, StudentAccount } from '../../types/models'
import { formatDate, formatDateTime, formatMoney, getCourseStatusLabel, getCourseStatusColor } from '../../utils/format'

const { Text } = Typography

interface StudentDetailProps {
  studentId: number | null
  open: boolean
  onClose: () => void
  onEdit?: (student: Student) => void
}

interface CourseHistory {
  id: number
  subject: string
  start_time: string
  status: string
  duration: number
}

interface AssignmentRecord {
  id: number
  title: string
  due_date: string
  status: string
  score?: number | null
}

const StudentDetail: React.FC<StudentDetailProps> = ({ studentId, open, onClose, onEdit }) => {
  const [loading, setLoading] = useState(false)
  const [student, setStudent] = useState<Student | null>(null)
  const [courses, setCourses] = useState<CourseHistory[]>([])
  const [assignments, setAssignments] = useState<AssignmentRecord[]>([])
  const [account, setAccount] = useState<StudentAccount | null>(null)
  const [activeTab, setActiveTab] = useState('info')

  useEffect(() => {
    if (studentId && open) {
      fetchStudentData(studentId)
    }
  }, [studentId, open])

  const fetchStudentData = async (id: number) => {
    setLoading(true)
    try {
      const [studentData, coursesData, assignmentsData, accountData] = await Promise.allSettled([
        studentsApi.get(id),
        studentsApi.getCourses(id, { page_size: 20 }),
        studentsApi.getAssignments(id, { page_size: 20 }),
        studentsApi.getAccount(id),
      ])

      if (studentData.status === 'fulfilled') setStudent(studentData.value)
      if (coursesData.status === 'fulfilled') setCourses(coursesData.value?.items || [])
      if (assignmentsData.status === 'fulfilled') setAssignments(assignmentsData.value?.items || [])
      if (accountData.status === 'fulfilled') setAccount(accountData.value)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const courseColumns: ColumnsType<CourseHistory> = [
    {
      title: '日期',
      dataIndex: 'start_time',
      render: (v: string) => formatDate(v),
      width: 100,
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '时长',
      dataIndex: 'duration',
      render: (v: number) => `${v}分钟`,
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: (v: string) => (
        <Tag color={getCourseStatusColor(v)}>{getCourseStatusLabel(v)}</Tag>
      ),
    },
  ]

  const assignmentColumns: ColumnsType<AssignmentRecord> = [
    {
      title: '作业标题',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      render: (v: string) => formatDate(v),
      width: 100,
    },
    {
      title: '分数',
      dataIndex: 'score',
      render: (v: number | null | undefined) => (v != null ? `${v}分` : '-'),
      width: 70,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (v: string) => {
        const colorMap: Record<string, string> = { pending: 'orange', submitted: 'green', graded: 'blue' }
        const labelMap: Record<string, string> = { pending: '待提交', submitted: '待批改', graded: '已批改' }
        return <Tag color={colorMap[v] || 'default'}>{labelMap[v] || v}</Tag>
      },
    },
  ]

  const tabItems = [
    {
      key: 'info',
      label: '基本信息',
      children: (
        <div>
          {student && (
            <>
              <Descriptions column={1} labelStyle={{ color: '#6B7280', width: 90 }} contentStyle={{ color: '#111827' }}>
                <Descriptions.Item label="年级">{student.grade}</Descriptions.Item>
                <Descriptions.Item label="辅导科目">
                  {student.subjects?.map((s) => (
                    <Tag key={s} color="blue" style={{ marginBottom: 4 }}>
                      {s}
                    </Tag>
                  ))}
                </Descriptions.Item>
                <Descriptions.Item label="家长姓名">{student.parent_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="家长电话">{student.parent_phone || '-'}</Descriptions.Item>
                <Descriptions.Item label="学校">{student.school || '-'}</Descriptions.Item>
                <Descriptions.Item label="添加时间">{formatDate(student.created_at)}</Descriptions.Item>
                <Descriptions.Item label="备注">
                  <Text style={{ color: '#374151' }}>{student.notes || '无'}</Text>
                </Descriptions.Item>
              </Descriptions>

              {student.stats && (
                <div style={{ marginTop: 20 }}>
                  <Text strong style={{ color: '#374151', display: 'block', marginBottom: 12 }}>
                    学习概况
                  </Text>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic
                        title="完成课程"
                        value={student.stats.completed_courses}
                        suffix={`/ ${student.stats.total_courses}`}
                        valueStyle={{ fontSize: 20, color: '#2563EB' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="待完成作业"
                        value={student.stats.pending_assignments}
                        suffix="份"
                        valueStyle={{ fontSize: 20, color: '#F59E0B' }}
                      />
                    </Col>
                    <Col span={12} style={{ marginTop: 12 }}>
                      <Statistic
                        title="已收费用"
                        value={student.stats.total_paid}
                        prefix="¥"
                        precision={0}
                        valueStyle={{ fontSize: 20, color: '#10B981' }}
                      />
                    </Col>
                    <Col span={12} style={{ marginTop: 12 }}>
                      <Statistic
                        title="欠费金额"
                        value={student.stats.outstanding}
                        prefix="¥"
                        precision={0}
                        valueStyle={{
                          fontSize: 20,
                          color: student.stats.outstanding > 0 ? '#EF4444' : '#10B981',
                        }}
                      />
                    </Col>
                  </Row>
                </div>
              )}
            </>
          )}
        </div>
      ),
    },
    {
      key: 'courses',
      label: '课程历史',
      children: (
        <Table
          columns={courseColumns}
          dataSource={courses}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10, size: 'small' }}
          locale={{ emptyText: '暂无课程记录' }}
        />
      ),
    },
    {
      key: 'assignments',
      label: '作业情况',
      children: (
        <Table
          columns={assignmentColumns}
          dataSource={assignments}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 10, size: 'small' }}
          locale={{ emptyText: '暂无作业记录' }}
        />
      ),
    },
    {
      key: 'account',
      label: '账户',
      children: (
        <div>
          {account ? (
            <>
              {account.has_payment_alert && (
                <Alert
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                  message="余额不足覆盖下一节课"
                  description={
                    account.next_course_time
                      ? `下一节课 ${formatDateTime(account.next_course_time)} ${account.next_course_subject || ''}，预计扣费 ${formatMoney(account.next_course_projected_charge || 0)}`
                      : '请尽快补录收款或调整课程安排'
                  }
                />
              )}

              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="当前余额" value={account.current_balance} prefix="¥" precision={2} valueStyle={{ color: account.current_balance < 0 ? '#cf1322' : '#1677ff' }} />
                </Col>
                <Col span={12}>
                  <Statistic title="预计还能上" value={account.estimated_lessons_left} suffix="节" precision={1} />
                </Col>
                <Col span={12} style={{ marginTop: 12 }}>
                  <Statistic title="累计收款" value={account.total_received} prefix="¥" precision={2} valueStyle={{ color: '#10B981' }} />
                </Col>
                <Col span={12} style={{ marginTop: 12 }}>
                  <Statistic title="累计扣费" value={account.total_charged} prefix="¥" precision={2} valueStyle={{ color: '#FA8C16' }} />
                </Col>
              </Row>

              <Descriptions
                column={1}
                style={{ marginTop: 16, marginBottom: 16 }}
                labelStyle={{ color: '#6B7280', width: 110 }}
              >
                <Descriptions.Item label="主科">{account.main_subject || '-'}</Descriptions.Item>
                <Descriptions.Item label="主科单价">
                  {account.main_subject_hourly_rate != null ? formatMoney(account.main_subject_hourly_rate) : '-'} / 小时
                </Descriptions.Item>
                <Descriptions.Item label="下一节课">
                  {account.next_course_time ? `${formatDateTime(account.next_course_time)} ${account.next_course_subject || ''}` : '-'}
                </Descriptions.Item>
              </Descriptions>

              <Text strong style={{ display: 'block', marginBottom: 8 }}>最近收款</Text>
              <Table
                size="small"
                rowKey="record_id"
                pagination={false}
                locale={{ emptyText: '暂无收款记录' }}
                dataSource={account.recent_payments}
                columns={[
                  {
                    title: '时间',
                    dataIndex: 'paid_at',
                    render: (v: string | undefined) => formatDateTime(v),
                  },
                  {
                    title: '金额',
                    dataIndex: 'amount',
                    render: (v: number) => formatMoney(v),
                  },
                  {
                    title: '方式',
                    dataIndex: 'payment_method',
                    render: (v: string | undefined) => v || '-',
                  },
                ]}
              />

              <Text strong style={{ display: 'block', marginTop: 16, marginBottom: 8 }}>最近扣费</Text>
              <Table
                size="small"
                rowKey="record_id"
                pagination={false}
                locale={{ emptyText: '暂无扣费记录' }}
                dataSource={account.recent_charges}
                columns={[
                  {
                    title: '时间',
                    dataIndex: 'created_at',
                    render: (v: string) => formatDateTime(v),
                  },
                  {
                    title: '科目',
                    dataIndex: 'subject',
                    render: (v: string | undefined) => v || '-',
                  },
                  {
                    title: '金额',
                    dataIndex: 'amount',
                    render: (v: number) => formatMoney(v),
                  },
                ]}
              />
            </>
          ) : (
            <Text type="secondary">暂无账户数据</Text>
          )}
        </div>
      ),
    },
  ]

  return (
    <Drawer
      title={student ? `${student.name} 的详情` : '学生详情'}
      open={open}
      onClose={onClose}
      width={540}
      extra={
        student && onEdit ? (
          <Tag
            color="blue"
            style={{ cursor: 'pointer', padding: '2px 12px', fontSize: 13 }}
            onClick={() => onEdit(student)}
          >
            编辑信息
          </Tag>
        ) : null
      }
    >
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          {student && (
            <div style={{ marginBottom: 20 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '16px',
                  background: '#F9FAFB',
                  borderRadius: 8,
                  marginBottom: 16,
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: '#2563EB',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#FFFFFF',
                    fontSize: 18,
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  {student.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 16, color: '#111827' }}>{student.name}</div>
                  <div style={{ color: '#6B7280', fontSize: 13, marginTop: 2 }}>
                    {student.grade} · {student.subjects?.join('、')}
                  </div>
                </div>
              </div>
            </div>
          )}

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            size="small"
          />
        </>
      )}
    </Drawer>
  )
}

export default StudentDetail
