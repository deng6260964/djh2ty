import React, { useState } from 'react'
import { Tag, Button, message } from 'antd'
import { DownloadOutlined, FileOutlined } from '@ant-design/icons'
import type { SharedResource } from '../../types/models'
import { formatFileSize, getFileTypeLabel, getFileTypeColor } from '../../utils/format'
import { resourcesApi } from '../../api/resources'
import dayjs from 'dayjs'

interface ResourceCardProps {
  resource: SharedResource
}

const ResourceCard: React.FC<ResourceCardProps> = ({ resource }) => {
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setDownloading(true)
    try {
      await resourcesApi.download(resource.id, resource.original_name)
    } catch {
      message.error('下载失败')
    } finally {
      setDownloading(false)
    }
  }

  const typeColor = getFileTypeColor(resource.file_type)
  const typeLabel = getFileTypeLabel(resource.file_type)

  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 8,
        padding: '12px 16px',
        marginBottom: 8,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 8,
          background: `${typeColor}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <FileOutlined style={{ fontSize: 20, color: typeColor }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, fontSize: 14, color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {resource.title}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
          <Tag style={{ margin: 0, fontSize: 11, color: typeColor, borderColor: typeColor, background: 'transparent' }}>
            {typeLabel}
          </Tag>
          {resource.subject && (
            <Tag color="blue" style={{ margin: 0, fontSize: 11 }}>{resource.subject}</Tag>
          )}
          <span style={{ fontSize: 12, color: '#9CA3AF' }}>
            {formatFileSize(resource.file_size)}
          </span>
          <span style={{ fontSize: 12, color: '#9CA3AF' }}>
            {dayjs(resource.created_at).format('MM-DD')}
          </span>
        </div>
      </div>
      <Button
        type="text"
        icon={<DownloadOutlined />}
        loading={downloading}
        onClick={handleDownload}
        style={{ color: '#2563EB', flexShrink: 0 }}
      />
    </div>
  )
}

export default ResourceCard
