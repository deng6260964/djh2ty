import React from 'react'
import { Empty } from 'antd'

interface EmptyStateProps {
  description?: string
}

const EmptyState: React.FC<EmptyStateProps> = ({ description = '暂无数据' }) => {
  return (
    <div style={{ padding: '48px 0' }}>
      <Empty description={description} />
    </div>
  )
}

export default EmptyState
