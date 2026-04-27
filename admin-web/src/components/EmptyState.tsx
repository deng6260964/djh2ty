import React from 'react'
import { Empty, Button } from 'antd'

interface EmptyStateProps {
  description?: string
  subtitle?: string
  actionText?: string
  onAction?: () => void
  image?: React.ReactNode
}

const EmptyState: React.FC<EmptyStateProps> = ({
  description = '暂无数据',
  subtitle,
  actionText,
  onAction,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 0',
      }}
    >
      <Empty
        description={
          <div>
            <div style={{ color: '#374151', fontSize: 14, marginBottom: subtitle ? 4 : 0 }}>
              {description}
            </div>
            {subtitle && (
              <div style={{ color: '#9CA3AF', fontSize: 13 }}>{subtitle}</div>
            )}
          </div>
        }
      />
      {actionText && onAction && (
        <Button type="primary" onClick={onAction} style={{ marginTop: 16 }}>
          {actionText}
        </Button>
      )}
    </div>
  )
}

export default EmptyState
