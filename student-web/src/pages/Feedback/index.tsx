import React, { useEffect, useState, useCallback } from 'react'
import { Pagination, message } from 'antd'
import { feedbackApi } from '../../api/feedback'
import type { MyFeedback } from '../../types/models'
import FeedbackCard from './FeedbackCard'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

const FeedbackPage: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<MyFeedback[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const fetchFeedback = useCallback(async () => {
    setLoading(true)
    try {
      const result = await feedbackApi.getMyFeedback({ page, page_size: pageSize })
      setFeedbacks(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取反馈列表失败')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    fetchFeedback()
  }, [fetchFeedback])

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 8 }}>
        课堂反馈
        <span style={{ color: '#9CA3AF', fontWeight: 400, marginLeft: 8 }}>({total})</span>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : feedbacks.length === 0 ? (
        <EmptyState description="暂无课堂反馈" />
      ) : (
        <>
          {feedbacks.map((feedback) => (
            <FeedbackCard key={feedback.id} feedback={feedback} />
          ))}
          {total > pageSize && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Pagination
                current={page}
                total={total}
                pageSize={pageSize}
                onChange={setPage}
                simple
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default FeedbackPage
