import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Tag, Rate, message } from 'antd'
import dayjs from 'dayjs'
import { feedbackApi } from '../../api/feedback'
import type { MyFeedback } from '../../types/models'
import PageHeader from '../../components/PageHeader'
import LoadingSpinner from '../../components/LoadingSpinner'

const SectionCard: React.FC<{ title: string; content: string }> = ({ title, content }) => (
  <div style={{ background: '#fff', borderRadius: 8, padding: 16, marginBottom: 8 }}>
    <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 8 }}>{title}</div>
    <div style={{ fontSize: 14, color: '#374151', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
      {content || '暂无内容'}
    </div>
  </div>
)

const FeedbackDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<MyFeedback | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return
      setLoading(true)
      try {
        const data = await feedbackApi.getDetail(Number(id))
        setDetail(data)
      } catch {
        message.error('加载反馈详情失败')
      } finally {
        setLoading(false)
      }
    }
    fetchDetail()
  }, [id])

  if (loading) {
    return (
      <>
        <PageHeader title="反馈详情" />
        <LoadingSpinner />
      </>
    )
  }

  if (!detail) {
    return (
      <>
        <PageHeader title="反馈详情" />
        <div style={{ padding: 24, textAlign: 'center', color: '#9CA3AF' }}>反馈不存在</div>
      </>
    )
  }

  return (
    <>
      <PageHeader title="反馈详情" />
      <div style={{ padding: 12 }}>
        {/* Header */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Tag color="blue" style={{ margin: 0 }}>{detail.subject}</Tag>
              <span style={{ fontSize: 13, color: '#6B7280' }}>
                {dayjs(detail.course_date).format('YYYY年MM月DD日')}
              </span>
            </div>
          </div>
          {detail.rating != null && detail.rating > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 13, color: '#6B7280' }}>评级:</span>
              <Rate disabled defaultValue={detail.rating} style={{ fontSize: 16 }} />
            </div>
          )}
        </div>

        <SectionCard title="课堂表现" content={detail.performance} />
        <SectionCard title="知识掌握" content={detail.knowledge_mastery} />
        <SectionCard title="存在问题" content={detail.problems} />
        <SectionCard title="下次计划" content={detail.next_plan} />
      </div>
    </>
  )
}

export default FeedbackDetailPage
