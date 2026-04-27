import React, { useEffect, useState } from 'react'
import { Modal, Form, Input, Select, DatePicker, message, Row, Col } from 'antd'
import dayjs from 'dayjs'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { studentsApi } from '../../api/students'
import { assignmentsApi } from '../../api/assignments'
import type { Student } from '../../types/models'
import type { AssignmentFormData } from '../../types/models'
import { SUBJECTS } from '../../utils/constants'

interface AssignmentFormProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FormValues {
  title: string
  subject: string
  due_date: dayjs.Dayjs
  student_ids: number[]
  content: string
}

const quillModules = {
  toolbar: [
    [{ header: [1, 2, false] }],
    ['bold', 'italic', 'underline'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['clean'],
  ],
}

const AssignmentForm: React.FC<AssignmentFormProps> = ({ open, onClose, onSuccess }) => {
  const [form] = Form.useForm<FormValues>()
  const [students, setStudents] = useState<Student[]>([])
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [saving, setSaving] = useState(false)
  const [content, setContent] = useState('')

  useEffect(() => {
    if (open) {
      fetchStudents()
      setContent('')
      form.resetFields()
    }
  }, [open])

  const fetchStudents = async () => {
    setLoadingStudents(true)
    try {
      const result = await studentsApi.list({ page_size: 100 })
      setStudents(result.items)
    } catch {
      // ignore
    } finally {
      setLoadingStudents(false)
    }
  }

  const handleSave = async (values: FormValues) => {
    if (!content || content === '<p><br></p>') {
      message.warning('请填写作业内容')
      return
    }

    setSaving(true)
    try {
      const data: AssignmentFormData = {
        title: values.title,
        subject: values.subject,
        content,
        due_date: values.due_date.format('YYYY-MM-DD'),
        student_ids: values.student_ids,
      }
      await assignmentsApi.create(data)
      message.success(`作业布置成功，已发布给 ${values.student_ids.length} 名学生`)
      form.resetFields()
      setContent('')
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } }
      message.error(axiosError.response?.data?.message || '布置失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      title="布置作业"
      open={open}
      onCancel={() => { form.resetFields(); setContent(''); onClose() }}
      onOk={() => form.submit()}
      confirmLoading={saving}
      okText="发布作业"
      cancelText="取消"
      width={720}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="title"
          label="作业标题"
          rules={[{ required: true, message: '请输入作业标题' }]}
        >
          <Input placeholder="如：第三章练习题 1-20" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
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
          </Col>
          <Col span={12}>
            <Form.Item
              name="due_date"
              label="截止日期"
              rules={[{ required: true, message: '请选择截止日期' }]}
            >
              <DatePicker
                style={{ width: '100%' }}
                placeholder="请选择截止日期"
                disabledDate={(current) => current && current < dayjs().startOf('day')}
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="student_ids"
          label="指定学生"
          rules={[{ required: true, message: '请至少选择一名学生' }]}
        >
          <Select
            mode="multiple"
            placeholder="请选择学生（可多选）"
            loading={loadingStudents}
            options={students.map((s) => ({
              value: s.id,
              label: `${s.name} (${s.grade})`,
            }))}
            optionFilterProp="label"
            allowClear
          />
        </Form.Item>

        <Form.Item
          label="作业内容"
          required
          help="请填写详细的作业要求"
        >
          <ReactQuill
            value={content}
            onChange={setContent}
            modules={quillModules}
            placeholder="请填写作业要求，支持富文本格式..."
            style={{ minHeight: 180 }}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default AssignmentForm
