import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  CreditCardOutlined,
  DollarOutlined,
  PlusOutlined,
  SettingOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { billingApi } from '../../api/billing'
import { studentsApi } from '../../api/students'
import { workbenchApi } from '../../api/workbench'
import type { WorkbenchPaymentAlertItem } from '../../types/api'
import type {
  BillingRecord,
  BillingSummary,
  OutstandingStudent,
  Student,
  SubjectPrice,
} from '../../types/models'
import { PAYMENT_METHODS } from '../../utils/constants'
import { formatDate, formatMoney, formatTime } from '../../utils/format'
import PageHeader from '../../components/PageHeader'

const { Text, Title } = Typography

const cardStyle: React.CSSProperties = {
  borderRadius: 12,
  boxShadow: '0 8px 24px rgba(15, 23, 42, 0.06)',
}

const BillingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [students, setStudents] = useState<Student[]>([])
  const [prices, setPrices] = useState<SubjectPrice[]>([])
  const [summary, setSummary] = useState<BillingSummary | null>(null)
  const [paymentAlerts, setPaymentAlerts] = useState<WorkbenchPaymentAlertItem[]>([])
  const [outstandingStudents, setOutstandingStudents] = useState<OutstandingStudent[]>([])
  const [records, setRecords] = useState<BillingRecord[]>([])
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filterStudent, setFilterStudent] = useState<number | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [reportDateRange, setReportDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ])

  const [rechargeModalOpen, setRechargeModalOpen] = useState(false)
  const [recharging, setRecharging] = useState(false)
  const [rechargeForm] = Form.useForm()

  const [priceModalOpen, setPriceModalOpen] = useState(false)
  const [savingPrice, setSavingPrice] = useState(false)
  const [priceForm] = Form.useForm()

  const [payModalOpen, setPayModalOpen] = useState(false)
  const [payingRecord, setPayingRecord] = useState<BillingRecord | null>(null)
  const [paying, setPaying] = useState(false)
  const [payForm] = Form.useForm()

  const fetchBaseData = useCallback(async () => {
    try {
      const [studentsResult, pricesResult, summaryResult, workbenchResult, outstandingResult] = await Promise.all([
        studentsApi.list({ page_size: 100 }),
        billingApi.listSubjectPrices(),
        billingApi.getSummary(reportDateRange[0].format('YYYY-MM-DD'), reportDateRange[1].format('YYYY-MM-DD')),
        workbenchApi.get(),
        billingApi.getOutstanding(),
      ])
      setStudents(studentsResult.items)
      setPrices(pricesResult)
      setSummary(summaryResult)
      setPaymentAlerts(workbenchResult.payment_alerts)
      setOutstandingStudents(outstandingResult)
    } catch {
      message.error('获取收费与账户数据失败')
    }
  }, [reportDateRange])

  const fetchRecords = useCallback(async () => {
    setRecordsLoading(true)
    try {
      const result = await billingApi.listRecords({
        page,
        page_size: 20,
        student_id: filterStudent,
        status: filterStatus,
      })
      setRecords(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取收支记录失败')
    } finally {
      setRecordsLoading(false)
    }
  }, [page, filterStudent, filterStatus])

  useEffect(() => {
    fetchBaseData()
  }, [fetchBaseData])

  useEffect(() => {
    fetchRecords()
  }, [fetchRecords])

  const paymentAlertCount = paymentAlerts.length
  const totalShortage = useMemo(
    () => paymentAlerts.reduce((sum, item) => sum + item.shortage_amount, 0),
    [paymentAlerts]
  )

  const openRechargeModal = (studentId?: number) => {
    rechargeForm.setFieldsValue({
      student_id: studentId,
      payment_method: 'wechat',
      paid_at: dayjs(),
    })
    setRechargeModalOpen(true)
  }

  const handleRecharge = async (values: {
    student_id: number
    paid_amount: number
    payment_method: string
    paid_at: dayjs.Dayjs
    notes?: string
  }) => {
    setRecharging(true)
    try {
      await billingApi.recharge({
        student_id: values.student_id,
        paid_amount: values.paid_amount,
        payment_method: values.payment_method,
        paid_at: values.paid_at.format('YYYY-MM-DDTHH:mm:ss'),
        notes: values.notes,
      })
      message.success('预收充值已记录')
      setRechargeModalOpen(false)
      rechargeForm.resetFields()
      fetchBaseData()
      fetchRecords()
    } catch {
      message.error('记录充值失败')
    } finally {
      setRecharging(false)
    }
  }

  const handleOpenRecordPayment = (record: BillingRecord) => {
    setPayingRecord(record)
    payForm.setFieldsValue({
      paid_amount: record.amount - (record.paid_amount || 0),
      payment_method: 'wechat',
      paid_at: dayjs(),
    })
    setPayModalOpen(true)
  }

  const handleConfirmPay = async (values: {
    paid_amount: number
    payment_method: string
    paid_at: dayjs.Dayjs
  }) => {
    if (!payingRecord) return
    setPaying(true)
    try {
      const nextPaidAmount = (payingRecord.paid_amount || 0) + values.paid_amount
      await billingApi.recordPayment(payingRecord.id, {
        paid_amount: nextPaidAmount,
        payment_method: values.payment_method,
        paid_at: values.paid_at.format('YYYY-MM-DDTHH:mm:ss'),
      })
      message.success('收款已记录')
      setPayModalOpen(false)
      payForm.resetFields()
      fetchBaseData()
      fetchRecords()
    } catch {
      message.error('记录收款失败')
    } finally {
      setPaying(false)
    }
  }

  const handleSavePrices = async () => {
    setSavingPrice(true)
    try {
      const values = priceForm.getFieldsValue()
      const entries = Object.entries(values).filter(([, price]) => price !== undefined && price !== null && price !== '')
      await Promise.all(
        entries.map(([subject, price]) => billingApi.updateSubjectPrice(subject, Number(price)))
      )
      message.success('课时单价已保存')
      setPriceModalOpen(false)
      fetchBaseData()
    } catch {
      message.error('保存课时单价失败')
    } finally {
      setSavingPrice(false)
    }
  }

  const recordColumns: ColumnsType<BillingRecord> = [
    {
      title: '学生',
      dataIndex: 'student_name',
      width: 110,
      render: (value: string) => <Text strong>{value}</Text>,
    },
    {
      title: '应扣 / 应收',
      dataIndex: 'amount',
      width: 120,
      render: (value: number) => formatMoney(value),
    },
    {
      title: '已收',
      dataIndex: 'paid_amount',
      width: 120,
      render: (value: number) => <Text style={{ color: '#10B981' }}>{formatMoney(value || 0)}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (value: string) => {
        const labelMap: Record<string, string> = {
          unpaid: '未收',
          partial: '部分收',
          paid: '已收',
        }
        const colorMap: Record<string, string> = {
          unpaid: 'red',
          partial: 'orange',
          paid: 'green',
        }
        return <Tag color={colorMap[value] || 'default'}>{labelMap[value] || value}</Tag>
      },
    },
    {
      title: '方式',
      dataIndex: 'payment_method',
      width: 90,
      render: (value?: string) => PAYMENT_METHODS.find((item) => item.value === value)?.label || '-',
    },
    {
      title: '日期',
      dataIndex: 'created_at',
      width: 120,
      render: (value: string) => formatDate(value),
    },
    {
      title: '备注',
      dataIndex: 'notes',
      render: (value?: string) => value || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_value: unknown, record: BillingRecord) => (
        record.status !== 'paid' ? (
          <Button type="link" size="small" onClick={() => handleOpenRecordPayment(record)}>
            补收
          </Button>
        ) : null
      ),
    },
  ]

  const outstandingColumns: ColumnsType<OutstandingStudent> = [
    {
      title: '学生',
      dataIndex: 'student_name',
      render: (value: string, record: OutstandingStudent) => (
        <Space>
          <Text strong>{value}</Text>
          <Text type="secondary">{record.grade}</Text>
        </Space>
      ),
    },
    {
      title: '未结清金额',
      dataIndex: 'outstanding_amount',
      render: (value: number) => <Text style={{ color: '#cf1322' }}>{formatMoney(value)}</Text>,
    },
    {
      title: '未结清记录',
      dataIndex: 'unpaid_count',
      render: (value: number) => `${value} 条`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_value: unknown, record: OutstandingStudent) => (
        <Button type="link" onClick={() => openRechargeModal(record.student_id)}>
          记录充值
        </Button>
      ),
    },
  ]

  const overviewTab = (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <Card style={cardStyle}>
            <Statistic title="待收费提醒" value={paymentAlertCount} prefix={<CreditCardOutlined />} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card style={cardStyle}>
            <Statistic title="本月已收" value={summary?.total_paid || 0} prefix="¥" precision={2} valueStyle={{ color: '#10B981' }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card style={cardStyle}>
            <Statistic title="需补足金额" value={totalShortage} prefix="¥" precision={2} valueStyle={{ color: '#d4380d' }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card style={cardStyle}>
            <Statistic title="已配置科目单价" value={prices.length} suffix="项" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={14}>
          <Card title="优先收费提醒" style={cardStyle}>
            {!paymentAlerts.length ? (
              <Empty description="当前没有需要优先收费的学生" />
            ) : (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                {paymentAlerts.map((item) => (
                  <Alert
                    key={item.student_id}
                    type="warning"
                    showIcon
                    message={`${item.student_name} · ${item.next_course_subject}`}
                    description={
                      <Space direction="vertical" size={4}>
                        <Text type="secondary">
                          下一节课 {formatDate(item.next_course_time)} {formatTime(item.next_course_time)}，预计扣费 {formatMoney(item.projected_charge)}
                        </Text>
                        <Text type="secondary">
                          当前余额 {formatMoney(item.current_balance)}，还差 {formatMoney(item.shortage_amount)}
                        </Text>
                      </Space>
                    }
                    action={<Button size="small" onClick={() => openRechargeModal(item.student_id)}>记录充值</Button>}
                  />
                ))}
              </Space>
            )}
          </Card>
        </Col>

        <Col xs={24} xl={10}>
          <Card title="当前规则" style={cardStyle}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Alert
                showIcon
                type="info"
                message="预收余额制"
                description="每次课程完成后，按实际课时 × 课时单价自动扣减余额。"
              />
              <Alert
                showIcon
                type="warning"
                message="收费提醒规则"
                description="当余额不足覆盖下一节已排课程时，系统会提前一节课提醒收费。"
              />
              <Card size="small" style={{ background: '#fafafa', borderRadius: 10 }}>
                <Space direction="vertical" size={4}>
                  <Text strong>老师常用动作</Text>
                  <Text type="secondary">1. 在这里看到谁该收费</Text>
                  <Text type="secondary">2. 直接记录本次预收充值</Text>
                  <Text type="secondary">3. 回到课程页继续上课与扣费</Text>
                </Space>
              </Card>
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  )

  const alertsTab = (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card title="下一节课前需收费" style={cardStyle}>
        {!paymentAlerts.length ? (
          <Empty description="暂无待收费提醒" />
        ) : (
          <List
            dataSource={paymentAlerts}
            renderItem={(item) => (
              <List.Item actions={[<Button key="recharge" type="link" onClick={() => openRechargeModal(item.student_id)}>记录充值</Button>]}>
                <List.Item.Meta
                  title={<Space><Text strong>{item.student_name}</Text><Tag color="warning">{item.next_course_subject}</Tag></Space>}
                  description={
                    <Space direction="vertical" size={2}>
                      <Text type="secondary">下一节课：{formatDate(item.next_course_time)} {formatTime(item.next_course_time)}</Text>
                      <Text type="secondary">余额 {formatMoney(item.current_balance)}，预计扣费 {formatMoney(item.projected_charge)}，差额 {formatMoney(item.shortage_amount)}</Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card title="未结清记录" style={cardStyle}>
        <Table
          rowKey="student_id"
          columns={outstandingColumns}
          dataSource={outstandingStudents}
          pagination={false}
          locale={{ emptyText: '暂无未结清学生' }}
        />
      </Card>
    </Space>
  )

  const recordsTab = (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Row gutter={[12, 12]}>
        <Col xs={24} md={8}>
          <Select
            placeholder="按学生筛选"
            style={{ width: '100%' }}
            allowClear
            value={filterStudent}
            onChange={(value) => {
              setFilterStudent(value)
              setPage(1)
            }}
            options={students.map((student) => ({
              value: student.id,
              label: `${student.name} (${student.grade})`,
            }))}
            showSearch
            filterOption={(input, option) => String(option?.label || '').toLowerCase().includes(input.toLowerCase())}
          />
        </Col>
        <Col xs={24} md={8}>
          <Select
            placeholder="按状态筛选"
            style={{ width: '100%' }}
            allowClear
            value={filterStatus}
            onChange={(value) => {
              setFilterStatus(value)
              setPage(1)
            }}
            options={[
              { value: 'unpaid', label: '未收' },
              { value: 'partial', label: '部分收' },
              { value: 'paid', label: '已收' },
            ]}
          />
        </Col>
      </Row>

      <Table
        rowKey="id"
        columns={recordColumns}
        dataSource={records}
        loading={recordsLoading}
        scroll={{ x: 900 }}
        pagination={{
          current: page,
          pageSize: 20,
          total,
          onChange: (value) => setPage(value),
          showTotal: (value) => `共 ${value} 条`,
        }}
        locale={{ emptyText: '暂无收支记录' }}
      />
    </Space>
  )

  const pricesTab = (
    <Card style={cardStyle}>
      <Table
        rowKey="id"
        dataSource={prices}
        pagination={false}
        columns={[
          { title: '科目', dataIndex: 'subject', width: 120 },
          {
            title: '课时单价',
            dataIndex: 'price_per_hour',
            render: (value: number) => <Text strong style={{ color: '#2563EB' }}>{formatMoney(value)}/小时</Text>,
          },
        ]}
        locale={{ emptyText: '暂未配置课时单价' }}
      />
    </Card>
  )

  const summaryTab = (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Row gutter={[12, 12]}>
        <Col xs={24} md={10}>
          <DatePicker.RangePicker
            style={{ width: '100%' }}
            value={reportDateRange}
            picker="month"
            onChange={(dates) => {
              if (dates) {
                setReportDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])
              }
            }}
          />
        </Col>
        <Col>
          <Button type="primary" onClick={fetchBaseData}>刷新报表</Button>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card style={cardStyle}>
            <Statistic title="应收总额" value={summary?.total_receivable || 0} prefix="¥" precision={2} valueStyle={{ color: '#2563EB' }} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card style={cardStyle}>
            <Statistic title="已收总额" value={summary?.total_paid || 0} prefix="¥" precision={2} valueStyle={{ color: '#10B981' }} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card style={cardStyle}>
            <Statistic title="未结清总额" value={summary?.total_outstanding || 0} prefix="¥" precision={2} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      {summary?.monthly_trend?.length ? (
        <Card title="收款趋势" style={cardStyle}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={summary.monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `¥${value}`} />
              <Tooltip formatter={(value: number) => [formatMoney(value), '已收']} />
              <Line type="monotone" dataKey="paid" stroke="#2563EB" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      ) : null}

      <Card title="按学生汇总" style={cardStyle}>
        <Table
          rowKey="student_id"
          dataSource={summary?.by_student || []}
          pagination={false}
          columns={[
            { title: '学生', dataIndex: 'student_name' },
            { title: '应收', dataIndex: 'receivable', render: (value: number) => formatMoney(value) },
            { title: '已收', dataIndex: 'paid', render: (value: number) => <Text style={{ color: '#10B981' }}>{formatMoney(value)}</Text> },
            { title: '未结清', dataIndex: 'outstanding', render: (value: number) => <Text style={{ color: value > 0 ? '#cf1322' : '#10B981' }}>{value > 0 ? formatMoney(value) : '已结清'}</Text> },
          ]}
          locale={{ emptyText: '暂无汇总数据' }}
        />
      </Card>
    </Space>
  )

  return (
    <div>
      <PageHeader
        title="收费与账户"
        extra={
          <Space>
            <Button
              icon={<SettingOutlined />}
              onClick={() => {
                const initialValues: Record<string, number> = {}
                prices.forEach((item) => {
                  initialValues[item.subject] = item.price_per_hour
                })
                priceForm.setFieldsValue(initialValues)
                setPriceModalOpen(true)
              }}
            >
              课时单价设置
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openRechargeModal()}>
              记录预收充值
            </Button>
          </Space>
        }
      />

      <Card style={cardStyle}>
        <div style={{ marginBottom: 16 }}>
          <Title level={5} style={{ marginBottom: 4 }}>老师账户工作台</Title>
          <Text type="secondary">先看谁该收费，再记录预收充值，剩下的账单和报表作为辅助复盘。</Text>
        </div>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'overview', label: '账户总览', children: overviewTab },
            { key: 'alerts', label: `待收费学生 ${paymentAlertCount ? `(${paymentAlertCount})` : ''}`, children: alertsTab },
            { key: 'records', label: '收支记录', children: recordsTab },
            { key: 'prices', label: '课时单价', children: pricesTab },
            { key: 'summary', label: '汇总报表', children: summaryTab },
          ]}
        />
      </Card>

      <Modal
        title="记录预收充值"
        open={rechargeModalOpen}
        onCancel={() => {
          rechargeForm.resetFields()
          setRechargeModalOpen(false)
        }}
        onOk={() => rechargeForm.submit()}
        confirmLoading={recharging}
        okText="确认记录"
        cancelText="取消"
        width={480}
        destroyOnClose
      >
        <Form form={rechargeForm} layout="vertical" onFinish={handleRecharge} style={{ marginTop: 16 }}>
          <Form.Item name="student_id" label="学生" rules={[{ required: true, message: '请选择学生' }]}>
            <Select
              placeholder="请选择学生"
              options={students.map((student) => ({
                value: student.id,
                label: `${student.name} (${student.grade})`,
              }))}
              showSearch
              filterOption={(input, option) => String(option?.label || '').toLowerCase().includes(input.toLowerCase())}
            />
          </Form.Item>
          <Form.Item name="paid_amount" label="充值金额" rules={[{ required: true, message: '请输入充值金额' }]}>
            <InputNumber min={0} precision={2} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="payment_method" label="收款方式" rules={[{ required: true, message: '请选择收款方式' }]}>
            <Select options={PAYMENT_METHODS} />
          </Form.Item>
          <Form.Item name="paid_at" label="收款日期" rules={[{ required: true, message: '请选择收款日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input placeholder="例如：预收 4 节课" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`补记录收款${payingRecord?.student_name ? ` - ${payingRecord.student_name}` : ''}`}
        open={payModalOpen}
        onCancel={() => {
          payForm.resetFields()
          setPayModalOpen(false)
        }}
        onOk={() => payForm.submit()}
        confirmLoading={paying}
        okText="确认收款"
        cancelText="取消"
        width={460}
        destroyOnClose
      >
        <Form form={payForm} layout="vertical" onFinish={handleConfirmPay} style={{ marginTop: 16 }}>
          <Form.Item name="paid_amount" label="本次收款金额" rules={[{ required: true, message: '请输入收款金额' }]}>
            <InputNumber min={0} precision={2} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="payment_method" label="收款方式" rules={[{ required: true, message: '请选择收款方式' }]}>
            <Select options={PAYMENT_METHODS} />
          </Form.Item>
          <Form.Item name="paid_at" label="收款日期" rules={[{ required: true, message: '请选择收款日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="课时单价设置"
        open={priceModalOpen}
        onCancel={() => setPriceModalOpen(false)}
        onOk={handleSavePrices}
        confirmLoading={savingPrice}
        okText="保存"
        cancelText="取消"
        width={560}
        destroyOnClose
      >
        <Form form={priceForm} layout="vertical" style={{ marginTop: 16 }}>
          <Row gutter={12}>
            {Array.from(new Set(students.flatMap((student) => student.subjects))).map((subject) => (
              <Col span={12} key={subject}>
                <Form.Item name={subject} label={`${subject} 单价`}>
                  <InputNumber min={0} precision={2} style={{ width: '100%' }} prefix="¥" />
                </Form.Item>
              </Col>
            ))}
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default BillingPage
