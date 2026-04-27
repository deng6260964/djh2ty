import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  InputNumber,
  Row,
  Space,
  Statistic,
  Table,
  Typography,
  message,
} from 'antd'
import { BellOutlined, SaveOutlined, SettingOutlined } from '@ant-design/icons'

import { billingApi } from '../../api/billing'
import { studentsApi } from '../../api/students'
import type { Student, SubjectPrice } from '../../types/models'
import { formatMoney } from '../../utils/format'
import PageHeader from '../../components/PageHeader'

const { Title, Text } = Typography

const SettingsPage: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [prices, setPrices] = useState<SubjectPrice[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [studentsResult, pricesResult] = await Promise.all([
        studentsApi.list({ page_size: 100 }),
        billingApi.listSubjectPrices(),
      ])
      setStudents(studentsResult.items)
      setPrices(pricesResult)
      const values: Record<string, number> = {}
      pricesResult.forEach((item) => {
        values[item.subject] = item.price_per_hour
      })
      form.setFieldsValue(values)
    } catch {
      message.error('获取系统设置失败')
    } finally {
      setLoading(false)
    }
  }, [form])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const usedSubjects = useMemo(
    () => Array.from(new Set(students.flatMap((student) => student.subjects))).sort(),
    [students]
  )

  const handleSavePrices = async () => {
    setSaving(true)
    try {
      const values = form.getFieldsValue()
      const entries = Object.entries(values).filter(([, value]) => value !== undefined && value !== null && value !== '')
      await Promise.all(entries.map(([subject, value]) => billingApi.updateSubjectPrice(subject, Number(value))))
      message.success('课时单价已保存')
      fetchData()
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="设置"
        extra={
          <Button type="primary" icon={<SaveOutlined />} onClick={handleSavePrices} loading={saving}>
            保存课时单价
          </Button>
        }
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="已配置科目单价" value={prices.length} prefix={<SettingOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="在教科目数" value={usedSubjects.length} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="收费提醒规则" value="提前一节课" prefix={<BellOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={14}>
          <Card loading={loading} style={{ borderRadius: 12 }}>
            <div style={{ marginBottom: 16 }}>
              <Title level={5} style={{ marginBottom: 4 }}>课时单价</Title>
              <Text type="secondary">课程完成后会按“实际课时 × 课时单价”自动扣减余额，这里维护全局默认单价。</Text>
            </div>

            <Form form={form} layout="vertical">
              <Row gutter={12}>
                {usedSubjects.map((subject) => (
                  <Col xs={24} md={12} key={subject}>
                    <Form.Item name={subject} label={`${subject} 单价`}>
                      <InputNumber min={0} precision={2} style={{ width: '100%' }} prefix="¥" placeholder="输入每小时单价" />
                    </Form.Item>
                  </Col>
                ))}
              </Row>
            </Form>
          </Card>
        </Col>

        <Col xs={24} xl={10}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Card style={{ borderRadius: 12 }}>
              <Title level={5} style={{ marginBottom: 12 }}>提醒规则</Title>
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Alert
                  showIcon
                  type="warning"
                  message="余额不足时提前一节课提醒"
                  description="当当前余额不足覆盖下一节已排课程的预计费用时，老师工作台和收费页会同步出现收费提醒。"
                />
                <Alert
                  showIcon
                  type="info"
                  message="课程完成后自动扣费"
                  description="如果课程填写了实际课时，系统会按本节课的科目单价自动计算并扣减学生余额。"
                />
              </Space>
            </Card>

            <Card style={{ borderRadius: 12 }}>
              <Title level={5} style={{ marginBottom: 12 }}>当前单价一览</Title>
              <Table
                rowKey="id"
                dataSource={prices}
                size="small"
                pagination={false}
                columns={[
                  { title: '科目', dataIndex: 'subject', width: 100 },
                  {
                    title: '默认单价',
                    dataIndex: 'price_per_hour',
                    render: (value: number) => <Text strong>{formatMoney(value)}/小时</Text>,
                  },
                ]}
                locale={{ emptyText: '暂无单价配置' }}
              />
            </Card>
          </Space>
        </Col>
      </Row>
    </div>
  )
}

export default SettingsPage
