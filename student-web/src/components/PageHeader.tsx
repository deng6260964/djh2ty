import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LeftOutlined } from '@ant-design/icons'

interface PageHeaderProps {
  title: string
  onBack?: () => void
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, onBack }) => {
  const navigate = useNavigate()

  const handleBack = () => {
    if (onBack) {
      onBack()
    } else {
      navigate(-1)
    }
  }

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        height: 48,
        background: '#fff',
        borderBottom: '1px solid #E5E7EB',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 12,
      }}
    >
      <LeftOutlined
        onClick={handleBack}
        style={{ fontSize: 18, color: '#374151', cursor: 'pointer' }}
      />
      <span style={{ fontSize: 16, fontWeight: 500, color: '#111827' }}>{title}</span>
    </div>
  )
}

export default PageHeader
