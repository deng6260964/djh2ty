import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  CalendarOutlined,
  FormOutlined,
  MessageOutlined,
  LineChartOutlined,
  FolderOutlined,
} from '@ant-design/icons'
import '../styles/tabbar.css'

const tabs = [
  { path: '/', label: '首页', icon: <HomeOutlined /> },
  { path: '/courses', label: '课程', icon: <CalendarOutlined /> },
  { path: '/assignments', label: '作业', icon: <FormOutlined /> },
  { path: '/feedback', label: '反馈', icon: <MessageOutlined /> },
  { path: '/progress', label: '进度', icon: <LineChartOutlined /> },
  { path: '/resources', label: '资料', icon: <FolderOutlined /> },
]

const TabBar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="tabbar">
      {tabs.map((tab) => (
        <div
          key={tab.path}
          className={`tabbar-item ${location.pathname === tab.path || (tab.path === '/' && location.pathname === '') ? 'active' : ''}`}
          onClick={() => navigate(tab.path)}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </div>
      ))}
    </div>
  )
}

export default TabBar
