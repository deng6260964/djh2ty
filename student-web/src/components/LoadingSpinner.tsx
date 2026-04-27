import React from 'react'
import { Spin } from 'antd'

const LoadingSpinner: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '64px 0',
      }}
    >
      <Spin size="large" />
    </div>
  )
}

export default LoadingSpinner
