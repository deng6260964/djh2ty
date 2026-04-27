import React, { useEffect, useState } from 'react'
import { Button, Card, Empty, List, Skeleton, Space, Statistic, Tag, Typography } from 'antd'
import {
  CalendarOutlined,
  CreditCardOutlined,
  FileDoneOutlined,
  FormOutlined,
  PlusOutlined,
  ReloadOutlined,
  SwapOutlined,
  UserAddOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'

import { workbenchApi } from '../../api/workbench'
import type {
  WorkbenchAssignmentItem,
  WorkbenchCourseItem,
  WorkbenchPaymentAlertItem,
  WorkbenchPendingRecordItem,
  WorkbenchResponse,
} from '../../types/api'
import { formatMoney, formatTime, getCourseStatusColor, getCourseStatusLabel } from '../../utils/format'
import CourseForm from '../Courses/CourseForm'
import './style.css'

const { Title, Text } = Typography

const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<WorkbenchResponse | null>(null)
  const [courseFormOpen, setCourseFormOpen] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await workbenchApi.get()
      setData(response)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const today = dayjs(data?.today || undefined)
  const todayText = `${today.format('M月D日')} ${weekdayLabels[today.day()]}`

  const renderCourseMeta = (item: WorkbenchCourseItem | WorkbenchPendingRecordItem) => (
    <Space className="workbench-item-meta" size={8} wrap>
      <Text type="secondary">{formatTime(item.start_time)} - {formatTime(item.end_time)}</Text>
      <Tag color={getCourseStatusColor(item.status)}>{getCourseStatusLabel(item.status)}</Tag>
      <Text type="secondary">预计扣费 {formatMoney(item.projected_charge)}</Text>
      <Text type={item.needs_payment ? 'danger' : 'secondary'}>
        当前余额 {formatMoney(item.current_balance)}
      </Text>
    </Space>
  )

  const renderLoading = () => (
    <Card className="workbench-card">
      <Skeleton active paragraph={{ rows: 10 }} />
    </Card>
  )

  const summaryCards = [
    {
      key: 'pending-records',
      title: '待补记录',
      value: data?.summary.pending_record_count ?? 0,
      icon: <FormOutlined />,
      color: '#d4380d',
      onClick: () => navigate('/courses'),
    },
    {
      key: 'today-courses',
      title: '今日课程',
      value: data?.summary.today_course_count ?? 0,
      icon: <CalendarOutlined />,
      color: '#2563eb',
      onClick: () => navigate('/courses'),
    },
    {
      key: 'payment-alerts',
      title: '待收费',
      value: data?.summary.payment_alert_count ?? 0,
      icon: <CreditCardOutlined />,
      color: '#cf1322',
      onClick: () => navigate('/billing'),
    },
    {
      key: 'assignment-reviews',
      title: '待批改',
      value: data?.summary.assignment_review_count ?? 0,
      icon: <FileDoneOutlined />,
      color: '#0891b2',
      onClick: () => navigate('/assignments'),
    },
  ]

  return (
    <div className="workbench-page">
      <div className="workbench-header">
        <div>
          <Title level={3} className="workbench-title">工作台</Title>
          <Text type="secondary">今天是 {todayText}，优先处理待补记录、收费提醒和待批改作业。</Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>
            今天
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCourseFormOpen(true)}>
            快速排课
          </Button>
        </Space>
      </div>

      <section className="workbench-section">
        <div className="workbench-section-title">关键提醒</div>
        <div className="workbench-summary-grid">
          {summaryCards.map((item) => (
            <Card
              key={item.key}
              className="workbench-card workbench-summary-card"
              hoverable
              onClick={item.onClick}
            >
              <Statistic
                title={item.title}
                value={item.value}
                prefix={item.icon}
                valueStyle={{ color: item.color }}
              />
            </Card>
          ))}
        </div>
      </section>

      <div className="workbench-grid">
        <section className="workbench-panel workbench-panel-large">
          {loading ? renderLoading() : (
            <Card
              title="今日课程"
              extra={<Button type="link" onClick={() => navigate('/courses')}>查看全部课程</Button>}
              className="workbench-card workbench-section-card"
            >
              {!data?.today_courses.length ? (
                <Empty description="今天暂无课程" />
              ) : (
                <List
                  dataSource={data.today_courses}
                  renderItem={(item) => (
                    <List.Item
                      className={item.needs_payment ? 'workbench-list-item is-warning' : 'workbench-list-item'}
                      actions={[
                        <Button key="view" type="link" onClick={() => navigate('/courses')}>查看</Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <Space wrap>
                            <Text strong>{item.student_name}</Text>
                            <Tag>{item.subject}</Tag>
                            {item.needs_payment && <Tag color="error">余额预警</Tag>}
                          </Space>
                        }
                        description={renderCourseMeta(item)}
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>
          )}
        </section>

        <section className="workbench-panel">
          {loading ? renderLoading() : (
            <Card
              title="待补记录"
              extra={<Tag color="red">{data?.summary.pending_record_count ?? 0}</Tag>}
              className="workbench-card workbench-section-card"
            >
              {!data?.pending_records.length ? (
                <Empty description="没有待补记录课程" />
              ) : (
                <List
                  dataSource={data?.pending_records}
                  renderItem={(item) => (
                    <List.Item
                      className="workbench-list-item"
                      actions={[<Button key="record" type="link" onClick={() => navigate('/courses')}>去补记录</Button>]}
                    >
                      <List.Item.Meta
                        title={<Space><Text strong>{item.student_name}</Text><Tag color="orange">{item.subject}</Tag></Space>}
                        description={renderCourseMeta(item)}
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>
          )}
        </section>

        <section className="workbench-panel">
          {loading ? renderLoading() : (
            <Card title="待收费提醒" className="workbench-card workbench-section-card">
              {!data?.payment_alerts.length ? (
                <Empty description="暂无待收费学生" />
              ) : (
                <List
                  dataSource={data.payment_alerts}
                  renderItem={(item: WorkbenchPaymentAlertItem) => (
                    <List.Item
                      className="workbench-list-item is-danger"
                      actions={[
                        <Button key="recharge" type="link" onClick={() => navigate('/billing')}>录入收款</Button>,
                        <Button key="account" type="link" onClick={() => navigate('/billing')}>查看账户</Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={<Space wrap><Text strong>{item.student_name}</Text><Tag color="red">{item.next_course_subject}</Tag></Space>}
                        description={
                          <Space direction="vertical" size={2}>
                            <Text type="secondary">
                              下一节课：{formatTime(item.next_course_time)}，预计扣费 {formatMoney(item.projected_charge)}
                            </Text>
                            <Text type="danger">
                              当前余额 {formatMoney(item.current_balance)}，预计不足 {formatMoney(item.shortage_amount)}
                            </Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>
          )}
        </section>

        <section className="workbench-panel">
          {loading ? renderLoading() : (
            <Card title="待批改作业" className="workbench-card workbench-section-card">
              {!data?.assignment_reviews.length ? (
                <Empty description="暂无待批改作业" />
              ) : (
                <List
                  dataSource={data.assignment_reviews}
                  renderItem={(item: WorkbenchAssignmentItem) => (
                    <List.Item
                      className="workbench-list-item"
                      actions={[<Button key="review" type="link" onClick={() => navigate('/assignments')}>去批改</Button>]}
                    >
                      <List.Item.Meta
                        title={<Space><Text strong>{item.student_name}</Text><Tag>{item.subject}</Tag></Space>}
                        description={
                          <Space direction="vertical" size={2}>
                            <Text>{item.assignment_title}</Text>
                            <Text type="secondary">{item.submitted_at ? `提交于 ${formatTime(item.submitted_at)}` : '已提交，待批改'}</Text>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>
          )}
        </section>
      </div>

      <Card className="workbench-card workbench-actions-card" title="快速操作">
        <Space wrap>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCourseFormOpen(true)}>
            快速排课
          </Button>
          <Button icon={<SwapOutlined />} onClick={() => navigate('/courses')}>
            快速调课
          </Button>
          <Button icon={<UserAddOutlined />} onClick={() => navigate('/students')}>
            新增学生
          </Button>
          <Button icon={<CreditCardOutlined />} onClick={() => navigate('/billing')}>
            录入收款
          </Button>
        </Space>
      </Card>

      <CourseForm
        open={courseFormOpen}
        onClose={() => setCourseFormOpen(false)}
        onSuccess={fetchData}
        initialDate={today.format('YYYY-MM-DD')}
        createTitle="快速排课"
      />
    </div>
  )
}

export default DashboardPage
