import React, { useEffect, useState, useCallback } from 'react'
import { Tabs, message } from 'antd'
import { assignmentsApi } from '../../api/assignments'
import type { MyAssignment } from '../../types/models'
import AssignmentCard from './AssignmentCard'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

const AssignmentsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('pending')
  const [assignments, setAssignments] = useState<MyAssignment[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAssignments = useCallback(async () => {
    setLoading(true)
    try {
      const statusFilter = activeTab === 'pending' ? 'pending' : undefined
      const result = await assignmentsApi.getMyAssignments({
        status: statusFilter,
        page_size: 50,
      })
      const items = activeTab === 'pending'
        ? result.items
        : result.items.filter((a) => a.status !== 'pending')

      // Re-fetch all if showing completed
      if (activeTab === 'completed') {
        const allResult = await assignmentsApi.getMyAssignments({ page_size: 100 })
        setAssignments(allResult.items.filter((a) => a.status !== 'pending'))
      } else {
        setAssignments(items)
      }
    } catch {
      message.error('获取作业列表失败')
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    fetchAssignments()
  }, [fetchAssignments])

  return (
    <div>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'pending', label: '待完成' },
          { key: 'completed', label: '已完成' },
        ]}
        style={{ marginBottom: 4 }}
      />

      {loading ? (
        <LoadingSpinner />
      ) : assignments.length === 0 ? (
        <EmptyState description={activeTab === 'pending' ? '暂无待完成作业' : '暂无已完成作业'} />
      ) : (
        assignments.map((assignment) => (
          <AssignmentCard key={assignment.id} assignment={assignment} />
        ))
      )}
    </div>
  )
}

export default AssignmentsPage
