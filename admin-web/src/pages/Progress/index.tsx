import React, { useEffect, useState, useCallback } from 'react'
import {
  Row, Col, Card, Select, Button, Table, Tag, Modal, Form, Input,
  InputNumber, DatePicker, message, Typography, Space, Tabs, Badge, Statistic,
} from 'antd'
import { PlusOutlined, DeleteOutlined, LineChartOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import dayjs from 'dayjs'
import { studentsApi } from '../../api/students'
import { progressApi } from '../../api/progress'
import type { Student, Grade, KnowledgePoint, GradeFormData } from '../../types/models'
import { SUBJECTS, EXAM_TYPES, KNOWLEDGE_POINT_STATUSES } from '../../utils/constants'
import { formatDate, getKnowledgeStatusLabel, getKnowledgeStatusColor } from '../../utils/format'
import PageHeader from '../../components/PageHeader'

const { Text, Title } = Typography

const ProgressPage: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [selectedStudentId, setSelectedStudentId] = useState<number | undefined>()
  const [grades, setGrades] = useState<Grade[]>([])
  const [trendData, setTrendData] = useState<Array<Record<string, unknown>>>([])
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([])
  const [loadingGrades, setLoadingGrades] = useState(false)
  const [gradeFormOpen, setGradeFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<GradeFormData>()
  const [selectedSubject, setSelectedSubject] = useState<string | undefined>()
  const [activeTab, setActiveTab] = useState('grades')

  useEffect(() => {
    fetchStudents()
  }, [])

  const fetchStudents = async () => {
    try {
      const result = await studentsApi.list({ page_size: 100 })
      setStudents(result.items)
      if (result.items.length > 0) {
        setSelectedStudentId(result.items[0].id)
      }
    } catch {
      message.error('获取学生列表失败')
    }
  }

  const fetchGrades = useCallback(async () => {
    if (!selectedStudentId) return
    setLoadingGrades(true)
    try {
      const result = await progressApi.listGrades({
        student_id: selectedStudentId,
        page_size: 50,
      })
      setGrades(result.items)
    } catch {
      // ignore
    } finally {
      setLoadingGrades(false)
    }
  }, [selectedStudentId])

  const fetchTrend = useCallback(async () => {
    if (!selectedStudentId) return
    try {
      const result = await progressApi.getGradeTrend(selectedStudentId, selectedSubject)
      // 转换为 recharts 格式
      const data = result.data.map((point) => ({
        date: point.exam_date,
        score: point.score,
        percentage: point.percentage,
        exam_name: point.exam_name,
        subject: result.subject,
      }))
      setTrendData(data)
    } catch {
      setTrendData([])
    }
  }, [selectedStudentId, selectedSubject])

  const fetchKnowledgePoints = useCallback(async () => {
    if (!selectedStudentId) return
    try {
      const result = await progressApi.listKnowledgePoints({
        student_id: selectedStudentId,
        subject: selectedSubject,
      })
      setKnowledgePoints(result)
    } catch {
      setKnowledgePoints([])
    }
  }, [selectedStudentId, selectedSubject])

  useEffect(() => {
    if (selectedStudentId) {
      fetchGrades()
      fetchTrend()
      fetchKnowledgePoints()
    }
  }, [selectedStudentId, fetchGrades, fetchTrend, fetchKnowledgePoints])

  const handleAddGrade = async (values: GradeFormData) => {
    if (!selectedStudentId) return
    setSaving(true)
    try {
      await progressApi.createGrade({
        ...values,
        student_id: selectedStudentId,
        exam_date: (values.exam_date as unknown as dayjs.Dayjs).format('YYYY-MM-DD'),
      })
      message.success('成绩记录已保存')
      form.resetFields()
      setGradeFormOpen(false)
      fetchGrades()
      fetchTrend()
    } catch {
      message.error('保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteGrade = async (id: number) => {
    try {
      await progressApi.deleteGrade(id)
      message.success('成绩记录已删除')
      fetchGrades()
      fetchTrend()
    } catch {
      message.error('删除失败')
    }
  }

  const gradeColumns: ColumnsType<Grade> = [
    {
      title: '考试名称',
      dataIndex: 'exam_name',
      render: (v: string) => v || '-',
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '类型',
      dataIndex: 'exam_type',
      width: 80,
      render: (v: string) => {
        const type = EXAM_TYPES.find((t) => t.value === v)
        return type?.label || v
      },
    },
    {
      title: '得分',
      key: 'score',
      width: 100,
      render: (_: unknown, record: Grade) => (
        <Space>
          <Text strong style={{ color: '#2563EB' }}>{record.score}</Text>
          <Text style={{ color: '#9CA3AF' }}>/ {record.full_score}</Text>
        </Space>
      ),
    },
    {
      title: '得分率',
      key: 'rate',
      width: 80,
      render: (_: unknown, record: Grade) => {
        const rate = Math.round((record.score / record.full_score) * 100)
        return (
          <Text style={{ color: rate >= 90 ? '#10B981' : rate >= 60 ? '#2563EB' : '#EF4444' }}>
            {rate}%
          </Text>
        )
      },
    },
    {
      title: '考试日期',
      dataIndex: 'exam_date',
      width: 110,
      render: (v: string) => formatDate(v),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      render: (v: string) => v || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 60,
      render: (_: unknown, record: Grade) => (
        <Button
          type="link"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteGrade(record.id)}
        />
      ),
    },
  ]

  const kpColumns: ColumnsType<KnowledgePoint> = [
    {
      title: '章节',
      dataIndex: 'chapter',
      width: 120,
    },
    {
      title: '知识点',
      dataIndex: 'point_name',
    },
    {
      title: '科目',
      dataIndex: 'subject',
      width: 80,
    },
    {
      title: '掌握状态',
      dataIndex: 'status',
      width: 100,
      render: (v: string) => (
        <Tag
          style={{
            background: getKnowledgeStatusColor(v) + '20',
            borderColor: getKnowledgeStatusColor(v),
            color: getKnowledgeStatusColor(v),
          }}
        >
          {getKnowledgeStatusLabel(v)}
        </Tag>
      ),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      render: (v: string) => v || '-',
    },
  ]

  const tabItems = [
    {
      key: 'grades',
      label: '成绩记录',
      children: (
        <Table
          columns={gradeColumns}
          dataSource={grades}
          rowKey="id"
          loading={loadingGrades}
          size="small"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无成绩记录' }}
        />
      ),
    },
    {
      key: 'knowledge',
      label: '知识点',
      children: (
        <Table
          columns={kpColumns}
          dataSource={knowledgePoints}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 15 }}
          locale={{ emptyText: '暂无知识点记录' }}
        />
      ),
    },
  ]

  // 汇总知识点状态
  const masteredCount = knowledgePoints.filter((k) => k.status === 'mastered').length
  const learningCount = knowledgePoints.filter((k) => k.status === 'learning').length
  const todoCount = knowledgePoints.filter((k) => k.status === 'todo').length
  const averagePercentage = grades.length
    ? Math.round(grades.reduce((sum, item) => sum + (item.score / item.full_score) * 100, 0) / grades.length)
    : 0

  return (
    <div>
      <PageHeader
        title="学习复盘"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setGradeFormOpen(true)}
            disabled={!selectedStudentId}
          >
            记录成绩
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="已记录成绩" value={grades.length} prefix={<LineChartOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="平均得分率" value={averagePercentage} suffix="%" valueStyle={{ color: averagePercentage >= 80 ? '#10B981' : '#2563EB' }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="知识点总数" value={knowledgePoints.length} />
          </Card>
        </Col>
      </Row>

      {/* 学生选择器 */}
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <div style={{ marginBottom: 16 }}>
          <Title level={5} style={{ marginBottom: 4 }}>学生长期跟踪</Title>
          <Text type="secondary">这里用于看成绩走势和知识点状态，日常教学动作仍应优先在课程和学生页完成。</Text>
        </div>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Text style={{ color: '#374151', marginRight: 12 }}>选择学生：</Text>
            <Select
              style={{ width: 200 }}
              placeholder="请选择学生"
              value={selectedStudentId}
              onChange={setSelectedStudentId}
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
          <Col xs={24} sm={12} md={8}>
            <Text style={{ color: '#374151', marginRight: 12 }}>科目筛选：</Text>
            <Select
              style={{ width: 150 }}
              placeholder="全部科目"
              value={selectedSubject}
              onChange={(v) => setSelectedSubject(v)}
              allowClear
              options={SUBJECTS.map((s) => ({ value: s, label: s }))}
            />
          </Col>
          {knowledgePoints.length > 0 && (
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Badge color="#10B981" text={`已掌握 ${masteredCount}`} />
                <Badge color="#F59E0B" text={`学习中 ${learningCount}`} />
                <Badge color="#9CA3AF" text={`待学习 ${todoCount}`} />
              </Space>
            </Col>
          )}
        </Row>
      </Card>

      {selectedStudentId ? (
        <>
          {/* 成绩趋势图 */}
          <Card
            title="成绩趋势"
            style={{ borderRadius: 8, marginBottom: 16 }}
          >
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    tickFormatter={(v) => v.slice(5)}
                  />
                  <YAxis
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    formatter={(value: number, name: string, props: { payload?: { exam_name?: string } }) => [
                      `${value}% (${props.payload?.exam_name || ''})`,
                      name,
                    ]}
                    contentStyle={{ borderRadius: 6, border: '1px solid #E5E7EB' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="percentage"
                    name="得分率"
                    stroke="#2563EB"
                    strokeWidth={2}
                    dot={{ fill: '#2563EB', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '32px 0', color: '#9CA3AF' }}>
                暂无成绩数据，点击右上角"记录成绩"开始记录
              </div>
            )}
          </Card>

          {/* 成绩记录 + 知识点 */}
          <Card style={{ borderRadius: 8 }}>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={tabItems}
            />
          </Card>
        </>
      ) : (
        <Card style={{ borderRadius: 8 }}>
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#9CA3AF' }}>
            请先选择一名学生
          </div>
        </Card>
      )}

      {/* 记录成绩 Modal */}
      <Modal
        title="记录成绩"
        open={gradeFormOpen}
        onCancel={() => { form.resetFields(); setGradeFormOpen(false) }}
        onOk={() => form.submit()}
        confirmLoading={saving}
        okText="保存成绩"
        cancelText="取消"
        width={480}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddGrade}
          style={{ marginTop: 16 }}
          initialValues={{ full_score: 100 }}
        >
          <Form.Item
            name="subject"
            label="科目"
            rules={[{ required: true, message: '请选择科目' }]}
          >
            <Select
              placeholder="请选择科目"
              options={SUBJECTS.map((s) => ({ value: s, label: s }))}
            />
          </Form.Item>

          <Form.Item
            name="exam_type"
            label="考试类型"
            rules={[{ required: true, message: '请选择考试类型' }]}
          >
            <Select
              placeholder="请选择类型"
              options={EXAM_TYPES}
            />
          </Form.Item>

          <Form.Item name="exam_name" label="考试名称">
            <Input placeholder="如：2024年春季期中考试（选填）" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="score"
                label="得分"
                rules={[{ required: true, message: '请输入得分' }]}
              >
                <InputNumber
                  min={0}
                  style={{ width: '100%' }}
                  placeholder="得分"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="full_score"
                label="满分"
                rules={[{ required: true, message: '请输入满分' }]}
              >
                <InputNumber
                  min={1}
                  style={{ width: '100%' }}
                  placeholder="满分"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="exam_date"
            label="考试日期"
            rules={[{ required: true, message: '请选择考试日期' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="请选择日期" />
          </Form.Item>

          <Form.Item name="notes" label="备注">
            <Input.TextArea placeholder="备注信息（选填）" rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ProgressPage
