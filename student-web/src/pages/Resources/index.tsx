import React, { useEffect, useState, useCallback } from 'react'
import { Pagination, message } from 'antd'
import { resourcesApi } from '../../api/resources'
import type { SharedResource } from '../../types/models'
import { SUBJECTS } from '../../utils/constants'
import SubjectTabs from '../../components/SubjectTabs'
import ResourceCard from './ResourceCard'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

const ResourcesPage: React.FC = () => {
  const [resources, setResources] = useState<SharedResource[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [activeSubject, setActiveSubject] = useState<string | null>(null)
  const pageSize = 20

  const fetchResources = useCallback(async () => {
    setLoading(true)
    try {
      const result = await resourcesApi.getShared({
        subject: activeSubject || undefined,
        page,
        page_size: pageSize,
      })
      setResources(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取资料列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, activeSubject])

  useEffect(() => {
    fetchResources()
  }, [fetchResources])

  const handleSubjectChange = (subject: string | null) => {
    setActiveSubject(subject)
    setPage(1)
  }

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 4 }}>
        学习资料
        <span style={{ color: '#9CA3AF', fontWeight: 400, marginLeft: 8 }}>({total})</span>
      </div>

      <SubjectTabs
        subjects={SUBJECTS}
        activeSubject={activeSubject}
        onChange={handleSubjectChange}
      />

      <div style={{ marginTop: 8 }}>
        {loading ? (
          <LoadingSpinner />
        ) : resources.length === 0 ? (
          <EmptyState description="暂无学习资料" />
        ) : (
          <>
            {resources.map((resource) => (
              <ResourceCard key={resource.id} resource={resource} />
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
    </div>
  )
}

export default ResourcesPage
