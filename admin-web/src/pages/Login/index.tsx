import React, { useState } from 'react'
import { Form, Input, Button, Typography, Alert } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'

const { Title, Text } = Typography

interface LoginFormValues {
  username: string
  password: string
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form] = Form.useForm<LoginFormValues>()

  const handleSubmit = async (values: LoginFormValues) => {
    setLoading(true)
    setError(null)
    try {
      const response = await authApi.login(values)
      login(response.access_token, response.user)
      navigate('/dashboard', { replace: true })
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string }; status?: number } }
      if (axiosError.response?.status === 401) {
        setError('用户名或密码错误，请重新输入')
      } else {
        setError('登录失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #F0F4FF 0%, #E8F0FE 100%)',
        padding: 24,
      }}
    >
      {/* 登录卡片 */}
      <div
        style={{
          width: '100%',
          maxWidth: 400,
          background: '#FFFFFF',
          borderRadius: 12,
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          padding: 40,
        }}
      >
        {/* Logo + 标题 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 14,
              background: '#2563EB',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16,
              color: '#FFFFFF',
              fontWeight: 700,
              fontSize: 24,
            }}
          >
            教
          </div>
          <Title level={3} style={{ margin: 0, color: '#111827' }}>
            家教辅助系统
          </Title>
          <Text style={{ color: '#6B7280', fontSize: 14, display: 'block', marginTop: 4 }}>
            欢迎回来，请登录您的账户
          </Text>
        </div>

        {/* 错误提示 */}
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 20, borderRadius: 6 }}
          />
        )}

        {/* 登录表单 */}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          size="large"
          autoComplete="off"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#9CA3AF' }} />}
              placeholder="请输入用户名"
              style={{ borderRadius: 6 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#9CA3AF' }} />}
              placeholder="请输入密码"
              style={{ borderRadius: 6 }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  form.submit()
                }
              }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{
                height: 44,
                borderRadius: 6,
                fontSize: 15,
                fontWeight: 500,
                background: '#2563EB',
                border: 'none',
              }}
            >
              {loading ? '登录中...' : '登 录'}
            </Button>
          </Form.Item>
        </Form>
      </div>

      {/* 底部版本信息 */}
      <Text
        style={{
          color: '#9CA3AF',
          fontSize: 12,
          marginTop: 24,
          textAlign: 'center',
          display: 'block',
        }}
      >
        家教辅助系统 v0.1.0 · 仅限授权用户使用
      </Text>
    </div>
  )
}

export default LoginPage
