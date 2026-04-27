import React, { useEffect, useState } from 'react'
import {
  Modal, Form, Select, Button, message, Row, Col, Switch, Typography, Space,
} from 'antd'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { coursesApi } from '../../api/courses'
import { feedbackApi } from '../../api/feedback'
import type { Course, FeedbackTemplate, FeedbackFormData } from '../../types/models'
import { formatDate, formatTime } from '../../utils/format'

const { Text } = Typography

interface FeedbackFormProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  editingId?: number | null
}

interface FormValues {
  course_id: number
  student_id: number
}

const quillModules = {
  toolbar: [
    ['bold', 'italic', 'underline'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['clean'],
  ],
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({ open, onClose, onSuccess }) => {
  const [form] = Form.useForm<FormValues>()
  const [courses, setCourses] = useState<Course[]>([])
  const [templates, setTemplates] = useState<FeedbackTemplate[]>([])
  const [loadingCourses, setLoadingCourses] = useState(false)
  const [saving, setSaving] = useState(false)
  const [shouldPush, setShouldPush] = useState(true)
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)

  // Rich text fields
  const [performance, setPerformance] = useState('')
  const [knowledgeMastery, setKnowledgeMastery] = useState('')
  const [problems, setProblems] = useState('')
  const [nextPlan, setNextPlan] = useState('')

  useEffect(() => {
    if (open) {
      fetchCourses()
      fetchTemplates()
      resetForm()
    }
  }, [open])

  const resetForm = () => {
    form.resetFields()
    setPerformance('')
    setKnowledgeMastery('')
    setProblems('')
    setNextPlan('')
    setSelectedCourse(null)
    setShouldPush(true)
  }

  const fetchCourses = async () => {
    setLoadingCourses(true)
    try {
      const result = await coursesApi.list({ page_size: 50, status: 'completed' })
      setCourses(result.items)
    } catch {
      // ignore
    } finally {
      setLoadingCourses(false)
    }
  }

  const fetchTemplates = async () => {
    try {
      const result = await feedbackApi.getTemplates()
      setTemplates(result)
    } catch {
      // ignore
    }
  }

  const handleCourseSelect = (courseId: number) => {
    const course = courses.find((c) => c.id === courseId)
    setSelectedCourse(course || null)
  }

  const handleApplyTemplate = (templateId: number) => {
    const template = templates.find((t) => t.id === templateId)
    if (!template) return

    if (template.performance) setPerformance((prev) => prev + template.performance)
    if (template.knowledge_mastery) setKnowledgeMastery((prev) => prev + template.knowledge_mastery)
    if (template.problems) setProblems((prev) => prev + template.problems)
    if (template.next_plan) setNextPlan((prev) => prev + template.next_plan)

    message.success('模板内容已填充')
  }

  const handleSave = async (values: FormValues) => {
    if (!performance || performance === '<p><br></p>') {
      message.warning('请填写本节课表现')
      return
    }

    setSaving(true)
    try {
      const data: FeedbackFormData = {
        course_id: values.course_id,
        student_id: selectedCourse?.student_id || 0,
        performance,
        knowledge_mastery: knowledgeMastery,
        problems,
        next_plan: nextPlan,
      }

      const feedback = await feedbackApi.create(data)

      if (shouldPush) {
        try {
          await feedbackApi.push(feedback.id)
        } catch {
          // push failed, ignore
        }
      }

      message.success('反馈已保存' + (shouldPush ? '并推送' : ''))
      resetForm()
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } }
      message.error(axiosError.response?.data?.message || '保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      title="新建课堂反馈"
      open={open}
      onCancel={() => { resetForm(); onClose() }}
      onOk={() => form.submit()}
      confirmLoading={saving}
      okText={shouldPush ? '保存并推送' : '保存'}
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
        <Row gutter={16} align="bottom">
          <Col span={16}>
            <Form.Item
              name="course_id"
              label="关联课程"
              rules={[{ required: true, message: '请选择关联课程' }]}
            >
              <Select
                placeholder="请选择本次课程"
                loading={loadingCourses}
                onChange={handleCourseSelect}
                options={courses.map((c) => ({
                  value: c.id,
                  label: `${c.student_name} / ${c.subject} / ${formatDate(c.start_time)} ${formatTime(c.start_time)}`,
                }))}
                showSearch
                filterOption={(input, option) =>
                  String(option?.label || '').toLowerCase().includes(input.toLowerCase())
                }
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            {templates.length > 0 && (
              <Form.Item label="使用模板">
                <Select
                  placeholder="选择快速填充模板"
                  onChange={handleApplyTemplate}
                  options={templates.map((t) => ({ value: t.id, label: t.title }))}
                  allowClear
                />
              </Form.Item>
            )}
          </Col>
        </Row>

        {selectedCourse && (
          <div
            style={{
              padding: '8px 12px',
              background: '#EFF6FF',
              borderRadius: 6,
              marginBottom: 16,
              fontSize: 13,
              color: '#2563EB',
            }}
          >
            已选课程：<strong>{selectedCourse.student_name}</strong> ·{' '}
            {selectedCourse.subject} · {formatDate(selectedCourse.start_time)}
          </div>
        )}

        <Form.Item
          label={
            <span>
              本节课表现 <Text type="danger">*</Text>
            </span>
          }
        >
          <ReactQuill
            value={performance}
            onChange={setPerformance}
            modules={quillModules}
            placeholder="描述学生本节课的整体表现..."
          />
        </Form.Item>

        <Form.Item label="知识点掌握情况">
          <ReactQuill
            value={knowledgeMastery}
            onChange={setKnowledgeMastery}
            modules={quillModules}
            placeholder="本节课知识点的掌握情况..."
          />
        </Form.Item>

        <Form.Item label="存在问题">
          <ReactQuill
            value={problems}
            onChange={setProblems}
            modules={quillModules}
            placeholder="本次课发现的问题和薄弱点..."
          />
        </Form.Item>

        <Form.Item label="下节课计划">
          <ReactQuill
            value={nextPlan}
            onChange={setNextPlan}
            modules={quillModules}
            placeholder="下节课的学习计划和重点..."
          />
        </Form.Item>

        <Form.Item>
          <Space>
            <Switch
              checked={shouldPush}
              onChange={setShouldPush}
              checkedChildren="推送"
              unCheckedChildren="不推送"
            />
            <Text style={{ color: '#6B7280', fontSize: 13 }}>
              {shouldPush ? '保存后自动推送微信消息给学生/家长' : '仅保存，不推送'}
            </Text>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default FeedbackForm
