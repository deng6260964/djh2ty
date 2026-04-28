import React, { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Input, Select, Space, Tag, Modal, Form,
  message, Popconfirm, Row, Col, Typography, Card,
} from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { studentsApi } from '../../api/students'
import type { Student, StudentFormData } from '../../types/models'
import { GRADES, SUBJECTS } from '../../utils/constants'
import { formatDate } from '../../utils/format'
import StudentDetail from './StudentDetail'
import PageHeader from '../../components/PageHeader'

const { Text } = Typography

const StudentsPage: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 搜索筛选
  const [searchText, setSearchText] = useState('')
  const [filterSubject, setFilterSubject] = useState<string | undefined>()
  const [filterGrade, setFilterGrade] = useState<string | undefined>()

  // 详情抽屉
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null)

  // 新增/编辑 Modal
  const [modalOpen, setModalOpen] = useState(false)
  const [editingStudent, setEditingStudent] = useState<Student | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<StudentFormData>()

  const fetchStudents = useCallback(async () => {
    setLoading(true)
    try {
      const result = await studentsApi.list({
        page,
        page_size: pageSize,
        search: searchText || undefined,
        subject: filterSubject,
        grade: filterGrade,
        is_active: true,
      })
      setStudents(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取学生列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, searchText, filterSubject, filterGrade])

  useEffect(() => {
    fetchStudents()
  }, [fetchStudents])

  const handleSearch = () => {
    setPage(1)
  }

  const handleOpenDetail = (studentId: number) => {
    setSelectedStudentId(studentId)
    setDetailOpen(true)
  }

  const handleOpenAdd = () => {
    setEditingStudent(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleOpenEdit = (student: Student) => {
    setEditingStudent(student)
    form.setFieldsValue({
      name: student.name,
      grade: student.grade,
      subjects: student.subjects,
      parent_name: student.parent_name,
      parent_phone: student.parent_phone,
      school: student.school,
      notes: student.notes,
      username: student.username,
    })
    setModalOpen(true)
    setDetailOpen(false)
  }

  const handleSave = async (values: StudentFormData) => {
    setSaving(true)
    try {
      if (editingStudent) {
        await studentsApi.update(editingStudent.id, values)
        message.success('学生信息已更新')
      } else {
        await studentsApi.create(values)
        message.success('学生添加成功')
      }
      setModalOpen(false)
      setPage(1)
      fetchStudents()
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } }
      message.error(axiosError.response?.data?.message || '保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number, name: string) => {
    try {
      await studentsApi.delete(id)
      message.success(`已删除学生 ${name}`)
      fetchStudents()
    } catch {
      message.error('删除失败，请重试')
    }
  }

  const columns: ColumnsType<Student> = [
    {
      title: '姓名',
      dataIndex: 'name',
      render: (name: string, record: Student) => (
        <Button
          type="link"
          onClick={() => handleOpenDetail(record.id)}
          style={{ padding: 0, fontWeight: 500, color: '#2563EB' }}
        >
          {name}
        </Button>
      ),
      width: 100,
    },
    {
      title: '年级',
      dataIndex: 'grade',
      width: 100,
    },
    {
      title: '辅导科目',
      dataIndex: 'subjects',
      render: (subjects: string[]) => (
        <Space wrap>
          {subjects?.map((s) => (
            <Tag key={s} color="blue" style={{ fontSize: 12 }}>
              {s}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '家长电话',
      dataIndex: 'parent_phone',
      width: 130,
      render: (phone: string) => phone || '-',
    },
    {
      title: 'Web账号',
      dataIndex: 'username',
      width: 100,
      render: (username: string) => username || '-',
    },
    {
      title: '添加时间',
      dataIndex: 'created_at',
      render: (v: string) => formatDate(v),
      width: 110,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 70,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'default'}>{active ? '在读' : '停课'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      fixed: 'right',
      render: (_: unknown, record: Student) => (
        <Space size={4}>
          <Button
            type="link"
            size="small"
            onClick={() => handleOpenDetail(record.id)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleOpenEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title={`确认删除学生"${record.name}"？`}
            description="删除后其相关课程记录将保留，但学生信息不可恢复。"
            onConfirm={() => handleDelete(record.id, record.name)}
            okText="确认删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="学生管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenAdd}>
            新增学生
          </Button>
        }
      />

      {/* 搜索筛选栏 */}
      <Card style={{ marginBottom: 16, borderRadius: 8 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={10} md={8}>
            <Input
              placeholder="搜索姓名"
              prefix={<SearchOutlined style={{ color: '#9CA3AF' }} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={handleSearch}
              allowClear
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
            <Select
              placeholder="科目筛选"
              style={{ width: '100%' }}
              allowClear
              value={filterSubject}
              onChange={(v) => { setFilterSubject(v); setPage(1) }}
              options={SUBJECTS.map((s) => ({ value: s, label: s }))}
            />
          </Col>
          <Col xs={12} sm={6} md={5}>
            <Select
              placeholder="年级筛选"
              style={{ width: '100%' }}
              allowClear
              value={filterGrade}
              onChange={(v) => { setFilterGrade(v); setPage(1) }}
              options={GRADES.map((g) => ({ value: g, label: g }))}
            />
          </Col>
          <Col xs={24} sm={2} md={2}>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} block>
              搜索
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 学生表格 */}
      <Card style={{ borderRadius: 8 }}>
        <div style={{ marginBottom: 12 }}>
          <Text style={{ color: '#6B7280', fontSize: 13 }}>共 {total} 名学生</Text>
        </div>
        <Table
          columns={columns}
          dataSource={students}
          rowKey="id"
          loading={loading}
          scroll={{ x: 800 }}
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => { setPage(p); setPageSize(ps || 20) },
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            pageSizeOptions: ['10', '20', '50'],
          }}
          locale={{ emptyText: '暂无学生，点击右上角新增学生' }}
        />
      </Card>

      {/* 学生详情抽屉 */}
      <StudentDetail
        studentId={selectedStudentId}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        onEdit={handleOpenEdit}
      />

      {/* 新增/编辑 Modal */}
      <Modal
        title={editingStudent ? '编辑学生信息' : '新增学生'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        okText="保存学生"
        cancelText="取消"
        width={560}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="学生姓名"
                rules={[{ required: true, message: '请输入学生姓名' }]}
              >
                <Input placeholder="请输入姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="grade"
                label="年级"
                rules={[{ required: true, message: '请选择年级' }]}
              >
                <Select
                  placeholder="请选择年级"
                  options={GRADES.map((g) => ({ value: g, label: g }))}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="subjects"
            label="辅导科目"
            rules={[{ required: true, message: '请选择辅导科目' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择科目（可多选）"
              options={SUBJECTS.map((s) => ({ value: s, label: s }))}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="parent_name" label="家长姓名">
                <Input placeholder="请输入家长姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="parent_phone"
                label="家长电话"
                rules={[
                  {
                    pattern: /^1[3-9]\d{9}$/,
                    message: '请输入正确的手机号码',
                  },
                ]}
              >
                <Input placeholder="请输入手机号" maxLength={11} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="school" label="学校">
            <Input placeholder="请输入学校名称（选填）" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="username" label="Web登录用户名">
                <Input placeholder="设置后学生可通过Web端登录" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="password" label="Web登录密码">
                <Input.Password placeholder="设置Web登录密码" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="备注">
            <Input.TextArea
              placeholder="请输入备注信息（选填）"
              rows={3}
              showCount
              maxLength={500}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StudentsPage
