import React, { Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { getToken } from './api/client'
import MobileLayout from './layouts/MobileLayout'
import LoginPage from './pages/Login/index'
import './styles/globals.css'

dayjs.locale('zh-cn')

const HomePage = React.lazy(() => import('./pages/Home/index'))
const AccountPage = React.lazy(() => import('./pages/Account/index'))
const CoursesPage = React.lazy(() => import('./pages/Courses/index'))
const AssignmentsPage = React.lazy(() => import('./pages/Assignments/index'))
const AssignmentDetailPage = React.lazy(() => import('./pages/Assignments/DetailPage'))
const FeedbackPage = React.lazy(() => import('./pages/Feedback/index'))
const FeedbackDetailPage = React.lazy(() => import('./pages/Feedback/DetailPage'))
const ProgressPage = React.lazy(() => import('./pages/Progress/index'))
const ResourcesPage = React.lazy(() => import('./pages/Resources/index'))

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getToken()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getToken()
  if (token) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

const antdTheme = {
  token: {
    colorPrimary: '#2563EB',
    borderRadius: 8,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif',
    colorBgLayout: '#F3F4F6',
  },
}

const LoadingFallback: React.FC = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" />
  </div>
)

const DetailPageShell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ maxWidth: 640, margin: '0 auto', minHeight: '100vh', background: '#F3F4F6' }}>
    {children}
  </div>
)

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN} theme={antdTheme}>
      <BrowserRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />

            {/* Detail pages without TabBar */}
            <Route
              path="/assignments/:id"
              element={
                <ProtectedRoute>
                  <DetailPageShell>
                    <AssignmentDetailPage />
                  </DetailPageShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/feedback/:id"
              element={
                <ProtectedRoute>
                  <DetailPageShell>
                    <FeedbackDetailPage />
                  </DetailPageShell>
                </ProtectedRoute>
              }
            />

            {/* Main layout with TabBar */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MobileLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<HomePage />} />
              <Route path="account" element={<AccountPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="assignments" element={<AssignmentsPage />} />
              <Route path="feedback" element={<FeedbackPage />} />
              <Route path="progress" element={<ProgressPage />} />
              <Route path="resources" element={<ResourcesPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
