import React, { useEffect, useState, useRef } from 'react'
import {
  Modal, Form, Select, DatePicker, TimePicker, Row, Col,
  Input, Alert, Spin, Typography,
} from 'antd'
import dayjs from 'dayjs'
import { studentsApi } from '../../api/students'
import { coursesApi } from '../../api/courses'
import type { Student, Course, CourseFormData } from '../../types/models'
import { SUBJECTS } from '../../utils/constants'

const { Text } = Typography

interface CourseFormProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  initialDate?: string
  initialCourse?: Course | null
  createTitle?: string
}

interface FormValues {
  student_id: number
  subject: string
  date: dayjs.Dayjs
  start_time: dayjs.Dayjs
  end_time: dayjs.Dayjs
  location?: string
  notes?: string
}

const CourseForm: React.FC<CourseFormProps> = ({ open, onClose, onSuccess, initialDate, initialCourse, createTitle }) => {
  const [form] = Form.useForm<FormValues>()
  const [students, setStudents] = useState<Student[]>([])
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [saving, setSaving] = useState(false)
  const [conflict, setConflict] = useState<{
    student_name: string
    start_time: string
    end_time: string
  } | null>(null)
  const [checkingConflict, setCheckingConflict] = useState(false)
  const conflictTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (open) {
      fetchStudents()
      if (initialCourse) {
        form.setFieldsValue({
          student_id: initialCourse.student_id,
          subject: initialCourse.subject,
          date: dayjs(initialCourse.start_time),
          start_time: dayjs(initialCourse.start_time),
          end_time: dayjs(initialCourse.end_time),
          location: initialCourse.location,
          notes: initialCourse.notes,
        })
      } else if (initialDate) {
        form.setFieldValue('date', dayjs(initialDate))
      }
    }
  }, [open, initialDate, initialCourse])

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

  const checkConflict = async () => {
    const values = form.getFieldsValue()
    if (!values.date || !values.start_time || !values.end_time) return

    setCheckingConflict(true)
    setConflict(null)

    try {
      const date = values.date.format('YYYY-MM-DD')
      const startTime = `${date}T${values.start_time.format('HH:mm')}:00`
      const endTime = `${date}T${values.end_time.format('HH:mm')}:00`

      const result = await coursesApi.checkConflict({
        start_time: startTime,
        end_time: endTime,
        exclude_id: initialCourse?.id ?? null,
      })

      if (result.has_conflict && result.conflict) {
        setConflict(result.conflict)
      } else {
        setConflict(null)
      }
    } catch {
      // ignore conflict check errors
    } finally {
      setCheckingConflict(false)
    }
  }

  const handleTimeChange = () => {
    if (conflictTimerRef.current) {
      clearTimeout(conflictTimerRef.current)
    }
    conflictTimerRef.current = setTimeout(checkConflict, 800)
  }

  const handleSave = async (values: FormValues) => {
    setSaving(true)
    try {
      const date = values.date.format('YYYY-MM-DD')
      const startTime = `${date}T${values.start_time.format('HH:mm')}:00`
      const endTime = `${date}T${values.end_time.format('HH:mm')}:00`

      const data: CourseFormData = {
        student_id: values.student_id,
        subject: values.subject,
        start_time: startTime,
        end_time: endTime,
        location: values.location,
        notes: values.notes,
      }

      if (initialCourse) {
        await coursesApi.update(initialCourse.id, data)
      } else {
        await coursesApi.create(data)
      }
      form.resetFields()
      setConflict(null)
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const axiosError = err as { response?: { status?: number; data?: { message?: string } } }
      if (axiosError.response?.status === 409) {
        setConflict({ student_name: '已有课程', start_time: '', end_time: '' })
      }
    } finally {
      setSaving(false)
    }
  }

  const handleClose = () => {
    form.resetFields()
    setConflict(null)
    onClose()
  }

  return (
    <Modal
      title={initialCourse ? '调整课程' : createTitle || '安排课程'}
      open={open}
      onCancel={handleClose}
      onOk={() => form.submit()}
      confirmLoading={saving}
      okText={initialCourse ? '保存调整' : '保存课程'}
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
        <Form.Item
          name="student_id"
          label="学生"
          rules={[{ required: true, message: '请选择学生' }]}
        >
          <Select
            placeholder="请选择学生"
            loading={loadingStudents}
            showSearch
            filterOption={(input, option) =>
              String(option?.label || '').toLowerCase().includes(input.toLowerCase())
            }
            options={students.map((s) => ({
              value: s.id,
              label: `${s.name} (${s.grade})`,
            }))}
          />
        </Form.Item>

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
          name="date"
          label="上课日期"
          rules={[{ required: true, message: '请选择上课日期' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            placeholder="请选择日期"
            disabledDate={(current) => current && current < dayjs().startOf('day')}
            onChange={handleTimeChange}
          />
        </Form.Item>

        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              name="start_time"
              label="开始时间"
              rules={[{ required: true, message: '请选择开始时间' }]}
            >
              <TimePicker
                style={{ width: '100%' }}
                format="HH:mm"
                minuteStep={30}
                placeholder="开始时间"
                onChange={handleTimeChange}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="end_time"
              label="结束时间"
              rules={[
                { required: true, message: '请选择结束时间' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    const start = getFieldValue('start_time')
                    if (!start || !value || value.isAfter(start)) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('结束时间必须晚于开始时间'))
                  },
                }),
              ]}
            >
              <TimePicker
                style={{ width: '100%' }}
                format="HH:mm"
                minuteStep={30}
                placeholder="结束时间"
                onChange={handleTimeChange}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 冲突检测结果 */}
        {checkingConflict && (
          <div style={{ marginBottom: 16 }}>
            <Spin size="small" /> <Text style={{ color: '#6B7280', fontSize: 13 }}> 正在检测时间冲突...</Text>
          </div>
        )}
        {conflict && (
          <Alert
            message={`时间冲突：该时间段已有 ${conflict.student_name} 的课程安排，请调整时间。`}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form.Item name="location" label="上课地点">
          <Input placeholder="如：线上、家中（选填）" />
        </Form.Item>

        <Form.Item name="notes" label="备注">
          <Input.TextArea placeholder="备注信息（选填）" rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CourseForm
