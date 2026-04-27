import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Tag, message } from 'antd'
import dayjs from 'dayjs'
import { assignmentsApi } from '../../api/assignments'
import type { MyAssignmentDetail } from '../../types/models'
import { ASSIGNMENT_STATUSES } from '../../utils/constants'
import PageHeader from '../../components/PageHeader'
import LoadingSpinner from '../../components/LoadingSpinner'

const AssignmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<MyAssignmentDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return
      setLoading(true)
      try {
        const data = await assignmentsApi.getDetail(Number(id))
        setDetail(data)
      } catch {
        message.error('加载作业详情失败')
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [id])

  if (loading) {
    return (
      <>
        <PageHeader title="作业详情" />
        <LoadingSpinner />
      </>
    )
  }

  if (!detail) {
    return (
      <>
        <PageHeader title="作业详情" />
        <div style={{ padding: 24, textAlign: 'center', color: '#9CA3AF' }}>作业不存在</div>
      </>
    )
  }

  const statusConfig = ASSIGNMENT_STATUSES[detail.status] || { label: detail.status, color: 'default' }

  return (
    <>
      <PageHeader title="作业详情" />
      <div style={{ padding: 12 }}>
        {/* Header card */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <h2 style={{ fontSize: 17, fontWeight: 600, color: '#111827', margin: 0, flex: 1 }}>
              {detail.title}
            </h2>
            <Tag color={statusConfig.color} style={{ margin: 0, marginLeft: 8, flexShrink: 0 }}>
              {statusConfig.label}
            </Tag>
          </div>
          <div style={{ display: 'flex', gap: 16, color: '#6B7280', fontSize: 13 }}>
            <Tag color="blue" style={{ margin: 0 }}>{detail.subject}</Tag>
            <span>截止: {dayjs(detail.due_date).format('YYYY-MM-DD')}</span>
          </div>
        </div>

        {/* Content */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 8 }}>作业内容</div>
          <div
            style={{ fontSize: 14, color: '#374151', lineHeight: 1.8 }}
            dangerouslySetInnerHTML={{ __html: detail.content || '无内容' }}
          />
        </div>

        {/* Score & Comment */}
        {detail.status === 'graded' && (
          <div style={{ background: '#fff', borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 12 }}>批改结果</div>
            {detail.score != null && (
              <div style={{ marginBottom: 12 }}>
                <span style={{ fontSize: 13, color: '#6B7280' }}>分数: </span>
                <span style={{ fontSize: 24, fontWeight: 600, color: '#2563EB' }}>{detail.score}</span>
                <span style={{ fontSize: 13, color: '#9CA3AF' }}> / 100</span>
              </div>
            )}
            {detail.comment && (
              <div>
                <span style={{ fontSize: 13, color: '#6B7280' }}>老师评语: </span>
                <div style={{ marginTop: 4, fontSize: 14, color: '#374151', lineHeight: 1.6, padding: '8px 12px', background: '#F9FAFB', borderRadius: 6 }}>
                  {detail.comment}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

export default AssignmentDetailPage
