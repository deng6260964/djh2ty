import React, { useEffect, useState } from 'react'
import {
  Drawer, Typography, Tag, Divider, List, Avatar, InputNumber,
  Input, Button, message, Space, Spin,
} from 'antd'
import { UserOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { assignmentsApi } from '../../api/assignments'
import type { AssignmentDetail, AssignmentStudent } from '../../types/models'
import { formatDateTime, getAssignmentStatusLabel, getAssignmentStatusColor } from '../../utils/format'

const { Text, Title } = Typography
const { TextArea } = Input

interface GradePanelProps {
  assignmentId: number | null
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

const GradePanel: React.FC<GradePanelProps> = ({ assignmentId, open, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState<AssignmentDetail | null>(null)
  const [selectedStudent, setSelectedStudent] = useState<AssignmentStudent | null>(null)
  const [score, setScore] = useState<number | null>(null)
  const [comment, setComment] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (assignmentId && open) {
      fetchDetail(assignmentId)
    }
  }, [assignmentId, open])

  const fetchDetail = async (id: number) => {
    setLoading(true)
    try {
      const result = await assignmentsApi.get(id)
      setDetail(result)
      setSelectedStudent(null)
      setScore(null)
      setComment('')
    } catch {
      message.error('获取作业详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectStudent = (student: AssignmentStudent) => {
    setSelectedStudent(student)
    setScore(student.score ?? null)
    setComment(student.comment ?? '')
  }

  const handleGrade = async () => {
    if (!selectedStudent || !assignmentId) return
    if (score === null || score === undefined) {
      message.warning('请输入评分')
      return
    }

    setSaving(true)
    try {
      await assignmentsApi.grade(assignmentId, {
        student_id: selectedStudent.student_id,
        score,
        comment,
      })
      message.success('批改成功')
      fetchDetail(assignmentId)
      onSuccess()
    } catch {
      message.error('批改失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  const getGradeLevel = (s: number): string => {
    if (s >= 90) return 'A'
    if (s >= 75) return 'B'
    if (s >= 60) return 'C'
    return 'D'
  }

  return (
    <Drawer
      title={detail ? `批改作业：${detail.title}` : '批改作业'}
      open={open}
      onClose={onClose}
      width={600}
      bodyStyle={{ padding: 0 }}
    >
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <Spin size="large" />
        </div>
      ) : detail ? (
        <div style={{ display: 'flex', height: '100%' }}>
          {/* 左侧：学生列表 */}
          <div
            style={{
              width: 200,
              borderRight: '1px solid #E5E7EB',
              overflow: 'auto',
              flexShrink: 0,
            }}
          >
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #E5E7EB' }}>
              <Text style={{ fontSize: 12, color: '#6B7280', fontWeight: 600, textTransform: 'uppercase' }}>
                学生列表
              </Text>
            </div>
            <List
              dataSource={detail.students}
              renderItem={(student) => (
                <List.Item
                  style={{
                    padding: '10px 16px',
                    cursor: 'pointer',
                    background:
                      selectedStudent?.student_id === student.student_id
                        ? '#EFF6FF'
                        : 'transparent',
                    borderLeft:
                      selectedStudent?.student_id === student.student_id
                        ? '3px solid #2563EB'
                        : '3px solid transparent',
                  }}
                  onClick={() => handleSelectStudent(student)}
                >
                  <Space size={8}>
                    <Avatar size={28} icon={<UserOutlined />} style={{ background: '#2563EB' }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: '#111827' }}>
                        {student.student_name}
                      </div>
                      <Tag
                        color={getAssignmentStatusColor(student.status)}
                        style={{ fontSize: 11, marginTop: 2 }}
                      >
                        {getAssignmentStatusLabel(student.status)}
                      </Tag>
                    </div>
                  </Space>
                </List.Item>
              )}
            />
          </div>

          {/* 右侧：批改区域 */}
          <div style={{ flex: 1, padding: 20, overflow: 'auto' }}>
            {selectedStudent ? (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Title level={5} style={{ margin: 0 }}>
                    {selectedStudent.student_name}
                  </Title>
                  <Text style={{ color: '#6B7280', fontSize: 13 }}>
                    {selectedStudent.submitted_at
                      ? `提交时间：${formatDateTime(selectedStudent.submitted_at)}`
                      : '尚未提交'}
                  </Text>
                </div>

                <Divider style={{ margin: '12px 0' }} />

                {selectedStudent.status === 'pending' ? (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '32px 0',
                      color: '#9CA3AF',
                    }}
                  >
                    <ClockCircleOutlined style={{ fontSize: 32, marginBottom: 8 }} />
                    <div>学生尚未提交作业</div>
                  </div>
                ) : (
                  <>
                    {/* 作业内容 */}
                    <div style={{ marginBottom: 20 }}>
                      <Text style={{ color: '#6B7280', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 8 }}>
                        提交内容
                      </Text>
                      <div
                        style={{
                          padding: 12,
                          background: '#F9FAFB',
                          borderRadius: 6,
                          border: '1px solid #E5E7EB',
                          fontSize: 13,
                          color: '#374151',
                          minHeight: 60,
                        }}
                      >
                        <div dangerouslySetInnerHTML={{ __html: detail.content || '（学生未上传内容）' }} />
                      </div>
                    </div>

                    <Divider style={{ margin: '12px 0' }} />

                    {/* 评分区 */}
                    <div style={{ marginBottom: 16 }}>
                      <Text style={{ color: '#374151', fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 8 }}>
                        评分（0-100分）
                      </Text>
                      <Space>
                        <InputNumber
                          min={0}
                          max={100}
                          value={score}
                          onChange={(v) => setScore(v)}
                          placeholder="请输入分数"
                          style={{ width: 120 }}
                          addonAfter="分"
                        />
                        {score !== null && (
                          <Tag
                            color={score >= 90 ? 'green' : score >= 75 ? 'blue' : score >= 60 ? 'orange' : 'red'}
                            style={{ fontSize: 14, padding: '0 12px' }}
                          >
                            等级 {getGradeLevel(score)}
                          </Tag>
                        )}
                      </Space>
                    </div>

                    {/* 评语 */}
                    <div style={{ marginBottom: 20 }}>
                      <Text style={{ color: '#374151', fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 8 }}>
                        批改评语
                      </Text>
                      <TextArea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        placeholder="请填写批改评语（选填）"
                        rows={4}
                        showCount
                        maxLength={500}
                      />
                    </div>

                    <Button
                      type="primary"
                      block
                      loading={saving}
                      onClick={handleGrade}
                      icon={<CheckCircleOutlined />}
                    >
                      保存批改结果
                    </Button>
                  </>
                )}
              </>
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: '#9CA3AF',
                  padding: '60px 0',
                }}
              >
                <UserOutlined style={{ fontSize: 40, marginBottom: 12 }} />
                <Text style={{ color: '#9CA3AF' }}>请从左侧选择学生进行批改</Text>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </Drawer>
  )
}

export default GradePanel
