import React from 'react'
import { Outlet } from 'react-router-dom'
import { Dropdown } from 'antd'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { useAuthStore } from '../store/authStore'
import TabBar from '../components/TabBar'

const MobileLayout: React.FC = () => {
  const { user, logout } = useAuthStore()

  const menuItems: MenuProps['items'] = [
    {
      key: 'user',
      label: user?.display_name || '学生',
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
      onClick: () => {
        logout()
        window.location.href = '/login'
      },
    },
  ]

  return (
    <div
      style={{
        maxWidth: 640,
        margin: '0 auto',
        minHeight: '100vh',
        background: '#F3F4F6',
        position: 'relative',
      }}
    >
      {/* Top header */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          height: 48,
          background: '#2563EB',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
        }}
      >
        <span style={{ color: '#fff', fontSize: 17, fontWeight: 600 }}>
          学习助手
        </span>
        <Dropdown menu={{ items: menuItems }} placement="bottomRight" trigger={['click']}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <UserOutlined style={{ color: '#fff', fontSize: 16 }} />
          </div>
        </Dropdown>
      </div>

      {/* Page content */}
      <div style={{ padding: '12px 12px 72px 12px' }}>
        <Outlet />
      </div>

      {/* Bottom TabBar */}
      <TabBar />
    </div>
  )
}

export default MobileLayout
