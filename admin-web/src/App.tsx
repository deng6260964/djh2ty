import React, { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { getToken } from './api/client'
import MainLayout from './layouts/MainLayout'
import './styles/globals.css'

const LoginPage = lazy(() => import('./pages/Login/index'))
const DashboardPage = lazy(() => import('./pages/Dashboard/index'))
const StudentsPage = lazy(() => import('./pages/Students/index'))
const CoursesPage = lazy(() => import('./pages/Courses/index'))
const AssignmentsPage = lazy(() => import('./pages/Assignments/index'))
const FeedbackPage = lazy(() => import('./pages/Feedback/index'))
const ProgressPage = lazy(() => import('./pages/Progress/index'))
const BillingPage = lazy(() => import('./pages/Billing/index'))
const ResourcesPage = lazy(() => import('./pages/Resources/index'))
const SettingsPage = lazy(() => import('./pages/Settings/index'))

dayjs.locale('zh-cn')

// 路由守卫：检查是否已登录
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

// 登录后重定向：已登录时不允许进入登录页
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getToken()
  if (token) {
    return <Navigate to="/dashboard" replace />
  }
  return <>{children}</>
}

const antdTheme = {
  token: {
    colorPrimary: '#2563EB',
    borderRadius: 6,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif',
    colorBgLayout: '#F3F4F6',
  },
  components: {
    Menu: {
      itemSelectedBg: '#EFF6FF',
      itemSelectedColor: '#2563EB',
      itemHoverBg: '#F9FAFB',
    },
    Table: {
      headerBg: '#F9FAFB',
      headerColor: '#6B7280',
      rowHoverBg: '#EFF6FF',
    },
    Card: {
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    },
  },
}

const LoadingFallback: React.FC = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
    }}
  >
    <Spin size="large" tip="加载中..." />
  </div>
)

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN} theme={antdTheme}>
      <BrowserRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* 公开路由：登录页 */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />

            {/* 受保护路由：主布局 */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="assignments" element={<AssignmentsPage />} />
              <Route path="feedback" element={<FeedbackPage />} />
              <Route path="progress" element={<ProgressPage />} />
              <Route path="billing" element={<BillingPage />} />
              <Route path="resources" element={<ResourcesPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* 404：重定向到首页 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
