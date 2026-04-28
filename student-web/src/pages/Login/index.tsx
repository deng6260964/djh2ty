import React, { useState } from 'react'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const result = await authApi.login(values)
      login(result.access_token, {
        id: result.user.id,
        username: result.user.username,
        role: result.user.role,
        display_name: result.user.display_name,
        student_id: result.user.student_id,
      })
      message.success('登录成功')
      navigate('/', { replace: true })
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: { message?: string } } } }
      message.error(axiosError.response?.data?.detail?.message || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        maxWidth: 640,
        margin: '0 auto',
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #2563EB 0%, #1D4ED8 40%, #F3F4F6 40%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '0 24px',
      }}
    >
      <div style={{ marginTop: '15vh', marginBottom: 40, textAlign: 'center' }}>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: 'rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <UserOutlined style={{ fontSize: 32, color: '#fff' }} />
        </div>
        <h1 style={{ color: '#fff', fontSize: 24, fontWeight: 600, margin: 0 }}>
          学习助手
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14, marginTop: 4 }}>
          学生登录
        </p>
      </div>

      <div
        style={{
          width: '100%',
          maxWidth: 360,
          background: '#fff',
          borderRadius: 12,
          padding: '32px 24px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        }}
      >
        <Form onFinish={handleSubmit} size="large" autoComplete="off">
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#9CA3AF' }} />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#9CA3AF' }} />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}

export default LoginPage
