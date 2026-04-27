import React from 'react'
import { Spin } from 'antd'

interface LoadingSpinnerProps {
  tip?: string
  size?: 'small' | 'default' | 'large'
  fullPage?: boolean
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  tip = '加载中...',
  size = 'large',
  fullPage = false,
}) => {
  if (fullPage) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '400px',
          width: '100%',
        }}
      >
        <Spin size={size} tip={tip} />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
      <Spin size={size} tip={tip} />
    </div>
  )
}

export default LoadingSpinner
