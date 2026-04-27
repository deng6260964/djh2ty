import React from 'react'
import { Modal, Typography } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

interface ConfirmModalProps {
  open: boolean
  title?: string
  content: string
  subContent?: string
  onConfirm: () => void | Promise<void>
  onCancel: () => void
  confirmText?: string
  cancelText?: string
  danger?: boolean
  loading?: boolean
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  title = '确认操作',
  content,
  subContent,
  onConfirm,
  onCancel,
  confirmText = '确认',
  cancelText = '取消',
  danger = false,
  loading = false,
}) => {
  return (
    <Modal
      open={open}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ExclamationCircleOutlined style={{ color: danger ? '#EF4444' : '#F59E0B', fontSize: 18 }} />
          <span>{title}</span>
        </div>
      }
      onOk={onConfirm}
      onCancel={onCancel}
      okText={confirmText}
      cancelText={cancelText}
      okButtonProps={{
        danger,
        loading,
      }}
      maskClosable={!danger}
      width={400}
    >
      <div style={{ padding: '8px 0' }}>
        <p style={{ color: '#374151', fontSize: 14, margin: 0 }}>{content}</p>
        {subContent && (
          <Text type="secondary" style={{ fontSize: 13, display: 'block', marginTop: 8 }}>
            {subContent}
          </Text>
        )}
      </div>
    </Modal>
  )
}

export default ConfirmModal
