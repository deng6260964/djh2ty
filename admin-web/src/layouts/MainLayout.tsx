import React, { useEffect, useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Badge, Typography, Space, Button } from 'antd'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import {
  DashboardOutlined,
  TeamOutlined,
  CalendarOutlined,
  FileTextOutlined,
  MessageOutlined,
  LineChartOutlined,
  AccountBookOutlined,
  FolderOutlined,
  BellOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { useAppStore } from '../store/appStore'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '工作台',
  },
  {
    key: '/students',
    icon: <TeamOutlined />,
    label: '学生',
  },
  {
    key: '/courses',
    icon: <CalendarOutlined />,
    label: '课程',
  },
  {
    key: '/assignments',
    icon: <FileTextOutlined />,
    label: '作业',
  },
  {
    key: '/feedback',
    icon: <MessageOutlined />,
    label: '反馈复盘',
  },
  {
    key: '/progress',
    icon: <LineChartOutlined />,
    label: '学习复盘',
  },
  {
    key: '/billing',
    icon: <AccountBookOutlined />,
    label: '收费与账户',
  },
  {
    key: '/resources',
    icon: <FolderOutlined />,
    label: '资料',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '设置',
  },
]

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { sidebarCollapsed, unreadNotifications, toggleSidebar } = useAppStore()

  const [selectedKeys, setSelectedKeys] = useState<string[]>([])

  useEffect(() => {
    const pathname = location.pathname
    const matched = menuItems.find((item) => pathname.startsWith(item.key))
    if (matched) {
      setSelectedKeys([matched.key])
    }
  }, [location.pathname])

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      handleLogout()
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 左侧侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        width={220}
        collapsedWidth={64}
        style={{
          background: '#FFFFFF',
          borderRight: '1px solid #E5E7EB',
          position: 'fixed',
          height: '100vh',
          left: 0,
          top: 0,
          zIndex: 100,
          overflow: 'auto',
        }}
      >
        {/* Logo 区域 */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            padding: sidebarCollapsed ? '0 20px' : '0 20px',
            borderBottom: '1px solid #E5E7EB',
            gap: 10,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: '#2563EB',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              color: '#FFFFFF',
              fontWeight: 700,
              fontSize: 16,
            }}
          >
            教
          </div>
          {!sidebarCollapsed && (
            <Text
              strong
              style={{
                fontSize: 15,
                color: '#111827',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
              }}
            >
              家教辅助系统
            </Text>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            border: 'none',
            paddingTop: 8,
          }}
          theme="light"
        />
      </Sider>

      {/* 右侧主体 */}
      <Layout
        style={{
          marginLeft: sidebarCollapsed ? 64 : 220,
          transition: 'margin-left 0.25s ease-in-out',
        }}
      >
        {/* 顶部导航栏 */}
        <Header
          style={{
            background: '#FFFFFF',
            borderBottom: '1px solid #E5E7EB',
            padding: '0 24px',
            height: 64,
            position: 'fixed',
            top: 0,
            right: 0,
            left: sidebarCollapsed ? 64 : 220,
            zIndex: 99,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'left 0.25s ease-in-out',
          }}
        >
          {/* 左侧：收起按钮 */}
          <Button
            type="text"
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={toggleSidebar}
            style={{ fontSize: 16, color: '#374151' }}
          />

          {/* 右侧：通知 + 用户信息 */}
          <Space size={16}>
            <Badge count={unreadNotifications} size="small" offset={[-2, 2]}>
              <Button
                type="text"
                icon={<BellOutlined style={{ fontSize: 18, color: '#374151' }} />}
                style={{ width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              />
            </Badge>

            <Dropdown
              menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
              placement="bottomRight"
              trigger={['click']}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: 6,
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#F9FAFB'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                <Avatar
                  size={32}
                  style={{ background: '#2563EB', flexShrink: 0 }}
                  icon={<UserOutlined />}
                />
                <Text style={{ color: '#374151', fontSize: 14, fontWeight: 500 }}>
                  {user?.display_name || user?.username || '老师'}
                </Text>
              </div>
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            marginTop: 64,
            padding: 24,
            minHeight: 'calc(100vh - 64px)',
            background: '#F3F4F6',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
