import React, { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Tag, Space, Card, Modal, Divider,
  message, Popconfirm, Select, Typography, Row, Col,
  Statistic,
} from 'antd'
import {
  PlusOutlined, SendOutlined, EyeOutlined, DeleteOutlined, FormOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { feedbackApi } from '../../api/feedback'
import { studentsApi } from '../../api/students'
import type { Feedback, Student } from '../../types/models'
import { formatDate, formatDateTime } from '../../utils/format'
import PageHeader from '../../components/PageHeader'
import FeedbackForm from './FeedbackForm'

const { Text, Title } = Typography

const FeedbackPage: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filterStudent, setFilterStudent] = useState<number | undefined>()
  const [students, setStudents] = useState<Student[]>([])
  const [formOpen, setFormOpen] = useState(false)
  const [viewingFeedback, setViewingFeedback] = useState<Feedback | null>(null)
  const [viewOpen, setViewOpen] = useState(false)
  const [pushing, setPushing] = useState<number | null>(null)
  const [filterPushStatus, setFilterPushStatus] = useState<string | undefined>()

  const fetchStudents = async () => {
    try {
      const result = await studentsApi.list({ page_size: 100 })
      setStudents(result.items)
    } catch {
      // ignore
    }
  }

  const fetchFeedbacks = useCallback(async () => {
    setLoading(true)
    try {
      const result = await feedbackApi.list({
        page,
        page_size: 20,
        student_id: filterStudent,
        is_pushed: filterPushStatus === undefined ? undefined : filterPushStatus === 'pushed',
      })
      setFeedbacks(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取反馈列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, filterStudent, filterPushStatus])

  useEffect(() => {
    fetchStudents()
  }, [])

  useEffect(() => {
    fetchFeedbacks()
  }, [fetchFeedbacks])

  const handleView = (feedback: Feedback) => {
    setViewingFeedback(feedback)
    setViewOpen(true)
  }

  const handlePush = async (id: number) => {
    setPushing(id)
    try {
      await feedbackApi.push(id)
      message.success('推送成功')
      fetchFeedbacks()
    } catch {
      message.error('推送失败，请检查微信配置')
    } finally {
      setPushing(null)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await feedbackApi.delete(id)
      message.success('反馈已删除')
      fetchFeedbacks()
    } catch {
      message.error('删除失败')
    }
  }

  const getTextPreview = (html: string, maxLen = 40): string => {
    const text = html.replace(/<[^>]+>/g, '').trim()
    return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
  }

  const pushedCount = feedbacks.filter((item) => item.is_pushed).length
  const pendingPushCount = feedbacks.filter((item) => !item.is_pushed).length

  const columns: ColumnsType<Feedback> = [
    {
      title: '学生',
      dataIndex: 'student_name',
      width: 90,
      render: (name: string) => <Text style={{ fontWeight: 500 }}>{name}</Text>,
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '上课日期',
      dataIndex: 'course_date',
      width: 110,
      render: (v: string) => formatDate(v),
    },
    {
      title: '内容摘要',
      dataIndex: 'performance',
      render: (v: string) => (
        <Text style={{ color: '#6B7280', fontSize: 13 }}>
          {getTextPreview(v)}
        </Text>
      ),
    },
    {
      title: '推送状态',
      dataIndex: 'is_pushed',
      width: 90,
      render: (pushed: boolean) => (
        <Tag color={pushed ? 'green' : 'default'}>
          {pushed ? '已推送' : '未推送'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 130,
      render: (v: string) => formatDateTime(v),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      fixed: 'right',
      render: (_: unknown, record: Feedback) => (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          {!record.is_pushed && (
            <Button
              type="link"
              size="small"
              icon={<SendOutlined />}
              loading={pushing === record.id}
              onClick={() => handlePush(record.id)}
              style={{ color: '#10B981' }}
            >
              推送
            </Button>
          )}
          <Popconfirm
            title="确认删除此反馈？"
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

  return (
    <div>
      <PageHeader
        title="课后反馈"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>
            新增反馈
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="本页反馈数" value={feedbacks.length} prefix={<FormOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="待推送" value={pendingPushCount} valueStyle={{ color: '#d4380d' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="已推送" value={pushedCount} valueStyle={{ color: '#10B981' }} />
          </Card>
        </Col>
      </Row>

      <Card style={{ borderRadius: 8 }}>
        <div style={{ marginBottom: 16 }}>
          <Title level={5} style={{ marginBottom: 4 }}>反馈复盘区</Title>
          <Text type="secondary">反馈应该紧跟课程记录产生，这里主要用于补推送、查历史和集中复盘。</Text>
        </div>
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="学生筛选"
              style={{ width: '100%' }}
              allowClear
              value={filterStudent}
              onChange={(v) => { setFilterStudent(v); setPage(1) }}
              options={students.map((s) => ({
                value: s.id,
                label: `${s.name} (${s.grade})`,
              }))}
              showSearch
              filterOption={(input, option) =>
                String(option?.label || '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="推送状态"
              style={{ width: '100%' }}
              allowClear
              value={filterPushStatus}
              onChange={(v) => { setFilterPushStatus(v); setPage(1) }}
              options={[
                { value: 'pending', label: '待推送' },
                { value: 'pushed', label: '已推送' },
              ]}
            />
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={feedbacks}
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
          locale={{ emptyText: '暂无课堂反馈记录' }}
        />
      </Card>

      <FeedbackForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSuccess={() => fetchFeedbacks()}
      />

      {/* 反馈详情 Modal */}
      <Modal
        title="课堂反馈详情"
        open={viewOpen}
        onCancel={() => setViewOpen(false)}
        footer={
          viewingFeedback && !viewingFeedback.is_pushed ? (
            <Space>
              <Button onClick={() => setViewOpen(false)}>关闭</Button>
              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={pushing === viewingFeedback.id}
                onClick={() => {
                  if (viewingFeedback) {
                    handlePush(viewingFeedback.id)
                    setViewOpen(false)
                  }
                }}
              >
                推送给学生/家长
              </Button>
            </Space>
          ) : (
            <Button onClick={() => setViewOpen(false)}>关闭</Button>
          )
        }
        width={640}
      >
        {viewingFeedback && (
          <div>
            <div
              style={{
                display: 'flex',
                gap: 16,
                padding: '12px 16px',
                background: '#F9FAFB',
                borderRadius: 8,
                marginBottom: 20,
              }}
            >
              <div>
                <Text strong style={{ color: '#111827' }}>{viewingFeedback.student_name}</Text>
                <Text style={{ color: '#6B7280', marginLeft: 8 }}>
                  {viewingFeedback.subject} · {formatDate(viewingFeedback.course_date)}
                </Text>
              </div>
              {viewingFeedback.is_pushed && (
                <Tag color="green" style={{ marginLeft: 'auto' }}>
                  已推送 {viewingFeedback.pushed_at ? formatDateTime(viewingFeedback.pushed_at) : ''}
                </Tag>
              )}
            </div>

            <FeedbackSection title="本节课表现" content={viewingFeedback.performance} />
            <Divider style={{ margin: '12px 0' }} />
            <FeedbackSection title="知识点掌握情况" content={viewingFeedback.knowledge_mastery} />
            <Divider style={{ margin: '12px 0' }} />
            <FeedbackSection title="存在问题" content={viewingFeedback.problems} />
            <Divider style={{ margin: '12px 0' }} />
            <FeedbackSection title="下节课计划" content={viewingFeedback.next_plan} />
          </div>
        )}
      </Modal>
    </div>
  )
}

const FeedbackSection: React.FC<{ title: string; content: string }> = ({ title, content }) => (
  <div style={{ marginBottom: 4 }}>
    <Title level={5} style={{ color: '#374151', marginBottom: 8, fontSize: 14 }}>
      {title}
    </Title>
    {content ? (
      <div
        style={{ color: '#374151', fontSize: 14, lineHeight: 1.7 }}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    ) : (
      <Text style={{ color: '#9CA3AF' }}>（未填写）</Text>
    )}
  </div>
)

export default FeedbackPage
