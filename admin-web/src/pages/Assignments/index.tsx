import React, { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Tag, Space, Tabs, Card, Typography,
  message, Popconfirm, Badge, Progress, Tooltip, Row, Col, Statistic,
} from 'antd'
import { PlusOutlined, DeleteOutlined, CheckSquareOutlined, ClockCircleOutlined, FileDoneOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { assignmentsApi } from '../../api/assignments'
import type { Assignment } from '../../types/models'
import { formatDate } from '../../utils/format'
import PageHeader from '../../components/PageHeader'
import AssignmentForm from './AssignmentForm'
import GradePanel from './GradePanel'

const { Text } = Typography

const AssignmentsPage: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState('all')
  const [formOpen, setFormOpen] = useState(false)
  const [gradePanelOpen, setGradePanelOpen] = useState(false)
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<number | null>(null)

  const getStatusFilter = (): string | undefined => {
    if (activeTab === 'pending') return 'pending'
    if (activeTab === 'submitted') return 'submitted'
    if (activeTab === 'graded') return 'graded'
    return undefined
  }

  const fetchAssignments = useCallback(async () => {
    setLoading(true)
    try {
      const result = await assignmentsApi.list({
        page,
        page_size: 20,
        status: getStatusFilter(),
      })
      setAssignments(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取作业列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, activeTab])

  useEffect(() => {
    fetchAssignments()
  }, [fetchAssignments])

  const handleTabChange = (key: string) => {
    setActiveTab(key)
    setPage(1)
  }

  const handleOpenGrade = (assignmentId: number) => {
    setSelectedAssignmentId(assignmentId)
    setGradePanelOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await assignmentsApi.delete(id)
      message.success('作业已删除')
      fetchAssignments()
    } catch {
      message.error('删除失败')
    }
  }

  const isOverdue = (dueDate: string): boolean => {
    return dayjs(dueDate).isBefore(dayjs(), 'day')
  }

  const pendingSubmitCount = assignments.filter((item) => item.submitted_count < item.student_count).length
  const pendingReviewCount = assignments.filter((item) => item.submitted_count > item.graded_count).length
  const overdueCount = assignments.filter((item) => isOverdue(item.due_date) && item.submitted_count < item.student_count).length

  const columns: ColumnsType<Assignment> = [
    {
      title: '作业标题',
      dataIndex: 'title',
      render: (title: string, record: Assignment) => (
        <div>
          <Text style={{ fontWeight: 500, color: '#111827' }}>{title}</Text>
          {isOverdue(record.due_date) && record.submitted_count < record.student_count && (
            <Tag color="red" style={{ marginLeft: 8, fontSize: 11 }}>已逾期</Tag>
          )}
        </div>
      ),
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '布置日期',
      dataIndex: 'created_at',
      render: (v: string) => formatDate(v),
      width: 110,
    },
    {
      title: '截止日期',
      dataIndex: 'due_date',
      render: (v: string) => (
        <Text
          style={{
            color: isOverdue(v) ? '#EF4444' : '#374151',
            fontWeight: isOverdue(v) ? 500 : 400,
          }}
        >
          {formatDate(v)}
        </Text>
      ),
      width: 110,
    },
    {
      title: '提交情况',
      key: 'submit_stats',
      width: 150,
      render: (_: unknown, record: Assignment) => {
        const rate = record.student_count > 0
          ? Math.round((record.submitted_count / record.student_count) * 100)
          : 0
        return (
          <Tooltip title={`${record.submitted_count}/${record.student_count} 人已提交`}>
            <div style={{ width: 120 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <Text style={{ fontSize: 12, color: '#6B7280' }}>
                  {record.submitted_count}/{record.student_count} 人
                </Text>
                <Text style={{ fontSize: 12, color: '#6B7280' }}>{rate}%</Text>
              </div>
              <Progress
                percent={rate}
                size="small"
                showInfo={false}
                strokeColor={rate === 100 ? '#10B981' : '#2563EB'}
              />
            </div>
          </Tooltip>
        )
      },
    },
    {
      title: '待批改',
      key: 'pending_grade',
      width: 80,
      render: (_: unknown, record: Assignment) => {
        const pending = record.submitted_count - record.graded_count
        return pending > 0 ? (
          <Badge count={pending} style={{ background: '#F59E0B' }} />
        ) : (
          <Text style={{ color: '#10B981', fontSize: 12 }}>全部批改</Text>
        )
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      fixed: 'right',
      render: (_: unknown, record: Assignment) => (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            icon={<CheckSquareOutlined />}
            onClick={() => handleOpenGrade(record.id)}
            style={{ color: '#7C3AED' }}
          >
            批改
          </Button>
          <Popconfirm
            title="确认删除此作业？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部', children: null },
    { key: 'pending', label: '待提交', children: null },
    { key: 'submitted', label: '待批改', children: null },
    { key: 'graded', label: '已批改', children: null },
  ]

  return (
    <div>
      <PageHeader
        title="作业中心"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>
            布置作业
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="待提交作业" value={pendingSubmitCount} prefix={<ClockCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="待批改作业" value={pendingReviewCount} prefix={<CheckSquareOutlined />} valueStyle={{ color: '#7C3AED' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="已逾期作业" value={overdueCount} prefix={<FileDoneOutlined />} valueStyle={{ color: '#d4380d' }} />
          </Card>
        </Col>
      </Row>

      <Card style={{ borderRadius: 8 }}>
        <div style={{ marginBottom: 16 }}>
          <Typography.Title level={5} style={{ marginBottom: 4 }}>跨学生集中处理</Typography.Title>
          <Text type="secondary">这里优先处理待批改和逾期作业，布置动作仍然建议从课程记录进入。</Text>
        </div>
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          items={tabItems}
          style={{ marginBottom: 0 }}
        />
        <Table
          columns={columns}
          dataSource={assignments}
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
          locale={{ emptyText: '暂无作业记录' }}
          rowClassName={(record) =>
            isOverdue(record.due_date) && record.submitted_count < record.student_count
              ? 'overdue-row'
              : ''
          }
        />
      </Card>

      <AssignmentForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSuccess={() => { fetchAssignments() }}
      />

      <GradePanel
        assignmentId={selectedAssignmentId}
        open={gradePanelOpen}
        onClose={() => setGradePanelOpen(false)}
        onSuccess={() => fetchAssignments()}
      />
    </div>
  )
}

export default AssignmentsPage
