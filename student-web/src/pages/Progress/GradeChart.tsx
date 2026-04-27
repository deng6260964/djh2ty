import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { GradeTrendResponse } from '../../api/progress'

interface GradeChartProps {
  trendData: GradeTrendResponse | null
  loading: boolean
}

const GradeChart: React.FC<GradeChartProps> = ({ trendData, loading }) => {
  if (loading) {
    return (
      <div style={{ background: '#fff', borderRadius: 8, padding: 16, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#9CA3AF' }}>加载中...</span>
      </div>
    )
  }

  if (!trendData || trendData.data.length === 0) {
    return (
      <div style={{ background: '#fff', borderRadius: 8, padding: 16, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#9CA3AF' }}>暂无成绩数据</span>
      </div>
    )
  }

  const chartData = trendData.data.map((d) => ({
    ...d,
    label: d.exam_name || d.exam_date,
  }))

  return (
    <div style={{ background: '#fff', borderRadius: 8, padding: '16px 8px 8px 0' }}>
      <div style={{ fontSize: 14, fontWeight: 500, color: '#374151', marginBottom: 12, paddingLeft: 16 }}>
        成绩趋势
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#9CA3AF' }}
            axisLine={{ stroke: '#E5E7EB' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: '#9CA3AF' }}
            axisLine={{ stroke: '#E5E7EB' }}
            width={35}
          />
          <Tooltip
            formatter={(value: number) => [`${value}%`, '得分率']}
            labelFormatter={(label: string) => label}
          />
          <Line
            type="monotone"
            dataKey="percentage"
            stroke="#2563EB"
            strokeWidth={2}
            dot={{ fill: '#2563EB', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default GradeChart
