import React from 'react'
import { Tag } from 'antd'
import type { KnowledgePoint } from '../../types/models'
import { KNOWLEDGE_STATUSES } from '../../utils/constants'
import EmptyState from '../../components/EmptyState'

interface KnowledgeListProps {
  points: KnowledgePoint[]
  loading: boolean
}

const KnowledgeList: React.FC<KnowledgeListProps> = ({ points, loading }) => {
  if (loading) {
    return (
      <div style={{ background: '#fff', borderRadius: 8, padding: 16, textAlign: 'center', color: '#9CA3AF' }}>
        加载中...
      </div>
    )
  }

  if (points.length === 0) {
    return <EmptyState description="暂无知识点数据" />
  }

  // Group by chapter
  const grouped: Record<string, KnowledgePoint[]> = {}
  for (const kp of points) {
    const chapter = kp.chapter || '未分类'
    if (!grouped[chapter]) {
      grouped[chapter] = []
    }
    grouped[chapter].push(kp)
  }

  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: 16 }}>
      <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 12 }}>
        知识点掌握
        <span style={{ color: '#9CA3AF', fontWeight: 400, marginLeft: 8 }}>({points.length})</span>
      </div>
      {Object.entries(grouped).map(([chapter, kps]) => (
        <div key={chapter} style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: '#6B7280', marginBottom: 6 }}>
            {chapter}
          </div>
          {kps.map((kp) => {
            const config = KNOWLEDGE_STATUSES[kp.status] || { label: kp.status, color: '#9CA3AF' }
            return (
              <div
                key={kp.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '6px 0',
                  borderBottom: '1px solid #F3F4F6',
                }}
              >
                <span style={{ fontSize: 14, color: '#374151' }}>{kp.point_name}</span>
                <Tag
                  color={config.color}
                  style={{ margin: 0, fontSize: 12, borderColor: config.color, color: config.color, background: 'transparent' }}
                >
                  {config.label}
                </Tag>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

export default KnowledgeList
