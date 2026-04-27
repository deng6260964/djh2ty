import React from 'react'
import { Typography, Space, Breadcrumb } from 'antd'
import { Link } from 'react-router-dom'

const { Title } = Typography

interface BreadcrumbItem {
  title: string
  path?: string
}

interface PageHeaderProps {
  title: string
  breadcrumbs?: BreadcrumbItem[]
  extra?: React.ReactNode
  subtitle?: string
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, breadcrumbs, extra, subtitle }) => {
  return (
    <div
      style={{
        marginBottom: 24,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
      }}
    >
      <div>
        {breadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumb
            style={{ marginBottom: 8 }}
            items={breadcrumbs.map((item) => ({
              title: item.path ? <Link to={item.path}>{item.title}</Link> : item.title,
            }))}
          />
        )}
        <Title level={4} style={{ margin: 0, color: '#111827' }}>
          {title}
        </Title>
        {subtitle && (
          <p style={{ margin: '4px 0 0', color: '#6B7280', fontSize: 14 }}>{subtitle}</p>
        )}
      </div>
      {extra && <Space>{extra}</Space>}
    </div>
  )
}

export default PageHeader
