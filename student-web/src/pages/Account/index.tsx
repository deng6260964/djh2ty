import React, { useEffect, useState } from 'react'
import { Alert, Button, Tag, message } from 'antd'
import { ArrowLeftOutlined, WalletOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import { billingApi, type StudentAccount } from '../../api/billing'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'
import { formatCurrency } from '../../utils/format'

const panelStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  padding: '12px 16px',
  marginBottom: 8,
}

const AccountPage: React.FC = () => {
  const navigate = useNavigate()
  const [account, setAccount] = useState<StudentAccount | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAccount = async () => {
      setLoading(true)
      try {
        setAccount(await billingApi.getMyAccount())
      } catch {
        message.error('获取账户信息失败')
      } finally {
        setLoading(false)
      }
    }

    fetchAccount()
  }, [])

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} />
        <div>
          <div style={{ color: '#111827', fontSize: 18, fontWeight: 700 }}>账户明细</div>
          <div style={{ color: '#9CA3AF', fontSize: 12 }}>{account?.student_name}</div>
        </div>
      </div>

      {account?.has_payment_alert && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12, borderRadius: 8 }}
          message="余额提醒"
          description="当前余额不足覆盖下一节课，建议和老师确认后续充值安排。"
        />
      )}

      <div style={panelStyle}>
        <div style={{ color: '#6B7280', fontSize: 13, marginBottom: 8 }}>
          <WalletOutlined style={{ marginRight: 6 }} />
          当前余额
        </div>
        <div style={{ color: account && account.current_balance < 0 ? '#EF4444' : '#111827', fontSize: 30, fontWeight: 700 }}>
          {formatCurrency(account?.current_balance)}
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 10, color: '#6B7280', fontSize: 12 }}>
          <span>累计收款 {formatCurrency(account?.total_received)}</span>
          <span>累计扣费 {formatCurrency(account?.total_charged)}</span>
        </div>
      </div>

      <div style={{ color: '#111827', fontSize: 15, fontWeight: 600, margin: '14px 0 8px' }}>
        最近扣费
      </div>
      {account?.recent_charges.length ? (
        account.recent_charges.map((record) => (
          <div key={record.record_id} style={panelStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <div style={{ color: '#111827', fontWeight: 600 }}>
                {record.subject || '课程扣费'}
              </div>
              <span style={{ color: '#EF4444', fontWeight: 700 }}>
                -{formatCurrency(record.amount)}
              </span>
            </div>
            <div style={{ color: '#9CA3AF', fontSize: 12 }}>
              {dayjs(record.created_at).format('YYYY-MM-DD HH:mm')}
              {record.notes ? ` · ${record.notes}` : ''}
            </div>
          </div>
        ))
      ) : (
        <EmptyState description="暂无扣费记录" />
      )}

      <div style={{ color: '#111827', fontSize: 15, fontWeight: 600, margin: '14px 0 8px' }}>
        最近收款
      </div>
      {account?.recent_payments.length ? (
        account.recent_payments.map((record) => (
          <div key={record.record_id} style={panelStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#111827', fontWeight: 600 }}>预收充值</span>
                {record.payment_method && <Tag color="green" style={{ margin: 0 }}>{record.payment_method}</Tag>}
              </div>
              <span style={{ color: '#10B981', fontWeight: 700 }}>
                +{formatCurrency(record.amount)}
              </span>
            </div>
            <div style={{ color: '#9CA3AF', fontSize: 12 }}>
              {record.paid_at ? dayjs(record.paid_at).format('YYYY-MM-DD HH:mm') : '时间未记录'}
              {record.notes ? ` · ${record.notes}` : ''}
            </div>
          </div>
        ))
      ) : (
        <EmptyState description="暂无收款记录" />
      )}
    </div>
  )
}

export default AccountPage
