import React, { useEffect, useState, useCallback } from 'react'
import { message } from 'antd'
import { progressApi } from '../../api/progress'
import type { MyProgressResponse, GradeTrendResponse } from '../../api/progress'
import type { KnowledgePoint } from '../../types/models'
import SubjectTabs from '../../components/SubjectTabs'
import GradeChart from './GradeChart'
import KnowledgeList from './KnowledgeList'
import LoadingSpinner from '../../components/LoadingSpinner'

const ProgressPage: React.FC = () => {
  const [progressData, setProgressData] = useState<MyProgressResponse | null>(null)
  const [trendData, setTrendData] = useState<GradeTrendResponse | null>(null)
  const [knowledgePoints, setKnowledgePoints] = useState<KnowledgePoint[]>([])
  const [loading, setLoading] = useState(true)
  const [trendLoading, setTrendLoading] = useState(false)
  const [kpLoading, setKpLoading] = useState(false)
  const [subjects, setSubjects] = useState<string[]>([])
  const [activeSubject, setActiveSubject] = useState<string | null>(null)

  const fetchProgress = useCallback(async () => {
    setLoading(true)
    try {
      const data = await progressApi.getMyProgress()
      setProgressData(data)

      // Extract unique subjects from recent_grades
      const uniqueSubjects = [...new Set(data.recent_grades.map((g) => g.subject))]
      setSubjects(uniqueSubjects)
      if (uniqueSubjects.length > 0 && !activeSubject) {
        setActiveSubject(uniqueSubjects[0])
      }
    } catch {
      message.error('获取进度数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchTrend = useCallback(async (subject: string) => {
    setTrendLoading(true)
    try {
      const data = await progressApi.getGradeTrend(subject)
      setTrendData(data)
    } catch {
      setTrendData(null)
    } finally {
      setTrendLoading(false)
    }
  }, [])

  const fetchKnowledgePoints = useCallback(async (subject: string) => {
    setKpLoading(true)
    try {
      const data = await progressApi.getKnowledgePoints(subject)
      setKnowledgePoints(data)
    } catch {
      setKnowledgePoints([])
    } finally {
      setKpLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProgress()
  }, [fetchProgress])

  useEffect(() => {
    if (activeSubject) {
      fetchTrend(activeSubject)
      fetchKnowledgePoints(activeSubject)
    }
  }, [activeSubject, fetchTrend, fetchKnowledgePoints])

  const handleSubjectChange = (subject: string | null) => {
    if (subject) {
      setActiveSubject(subject)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      {/* Summary stats */}
      {progressData && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <div style={{ flex: 1, background: '#fff', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 600, color: '#10B981' }}>
              {progressData.knowledge_points.mastered}
            </div>
            <div style={{ fontSize: 12, color: '#6B7280' }}>已掌握</div>
          </div>
          <div style={{ flex: 1, background: '#fff', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 600, color: '#F59E0B' }}>
              {progressData.knowledge_points.learning}
            </div>
            <div style={{ fontSize: 12, color: '#6B7280' }}>学习中</div>
          </div>
          <div style={{ flex: 1, background: '#fff', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 600, color: '#9CA3AF' }}>
              {progressData.knowledge_points.todo}
            </div>
            <div style={{ fontSize: 12, color: '#6B7280' }}>待学习</div>
          </div>
        </div>
      )}

      {/* Subject tabs */}
      {subjects.length > 0 && (
        <SubjectTabs
          subjects={subjects}
          activeSubject={activeSubject}
          onChange={handleSubjectChange}
          showAll={false}
        />
      )}

      {/* Grade trend chart */}
      <div style={{ marginTop: 8, marginBottom: 12 }}>
        <GradeChart trendData={trendData} loading={trendLoading} />
      </div>

      {/* Knowledge points */}
      <KnowledgeList points={knowledgePoints} loading={kpLoading} />
    </div>
  )
}

export default ProgressPage
