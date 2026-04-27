import React, { useEffect, useState, useCallback } from 'react'
import {
  Row, Col, Card, Button, Upload, Modal, Form, Input, Select,
  message, Typography, Space, Tag, Popconfirm, Spin, Progress,
  List, Checkbox,
} from 'antd'
import {
  PlusOutlined, CloudUploadOutlined, DownloadOutlined,
  ShareAltOutlined, DeleteOutlined, FileOutlined,
  FilePdfOutlined, FileWordOutlined, FileExcelOutlined, PictureOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import type { RcFile } from 'antd/es/upload'
import { resourcesApi } from '../../api/resources'
import { studentsApi } from '../../api/students'
import type { Resource, Student } from '../../types/models'
import { SUBJECTS, RESOURCE_TYPES, ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from '../../utils/constants'
import { formatDate, formatFileSize, getFileTypeColor, getFileTypeLabel } from '../../utils/format'
import PageHeader from '../../components/PageHeader'

const { Text, Title } = Typography
const { Dragger } = Upload

const getFileIcon = (fileType: string) => {
  const style = { fontSize: 28, color: getFileTypeColor(fileType) }
  if (fileType.includes('pdf')) return <FilePdfOutlined style={style} />
  if (fileType.includes('word') || fileType.includes('document')) return <FileWordOutlined style={style} />
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return <FileExcelOutlined style={style} />
  if (fileType.includes('image')) return <PictureOutlined style={style} />
  return <FileOutlined style={style} />
}

const ResourcesPage: React.FC = () => {
  const [resources, setResources] = useState<Resource[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filterSubject, setFilterSubject] = useState<string | undefined>()
  const [students, setStudents] = useState<Student[]>([])

  // 上传 Modal
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadForm] = Form.useForm()
  const [uploadFile, setUploadFile] = useState<RcFile | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploading, setUploading] = useState(false)

  // 分享 Modal
  const [shareOpen, setShareOpen] = useState(false)
  const [sharingResource, setSharingResource] = useState<Resource | null>(null)
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([])
  const [sharing, setSharing] = useState(false)

  useEffect(() => {
    fetchStudents()
  }, [])

  const fetchStudents = async () => {
    try {
      const result = await studentsApi.list({ page_size: 100 })
      setStudents(result.items)
    } catch {
      // ignore
    }
  }

  const fetchResources = useCallback(async () => {
    setLoading(true)
    try {
      const result = await resourcesApi.list({
        page,
        page_size: 20,
        subject: filterSubject,
      })
      setResources(result.items)
      setTotal(result.total)
    } catch {
      message.error('获取资料列表失败')
    } finally {
      setLoading(false)
    }
  }, [page, filterSubject])

  useEffect(() => {
    fetchResources()
  }, [fetchResources])

  const handleBeforeUpload = (file: RcFile): boolean => {
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      message.error('不支持该文件类型，请上传 PDF、Word、Excel 或图片文件')
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      message.error('文件大小不能超过 50MB')
      return false
    }
    setUploadFile(file)
    uploadForm.setFieldValue('title', file.name.replace(/\.[^.]+$/, ''))
    return false // 阻止自动上传
  }

  const handleUpload = async (values: {
    title: string
    subject?: string
    grade?: string
    resource_type?: string
    description?: string
    share_student_ids?: number[]
  }) => {
    if (!uploadFile) {
      message.warning('请先选择文件')
      return
    }

    const formData = new FormData()
    formData.append('file', uploadFile)
    formData.append('title', values.title)
    if (values.subject) formData.append('subject', values.subject)
    if (values.grade) formData.append('grade', values.grade || '')
    if (values.description) formData.append('description', values.description)

    setUploading(true)
    setUploadProgress(0)

    try {
      const resource = await resourcesApi.upload(formData, (progressEvent) => {
        const percent = progressEvent.total
          ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
          : 0
        setUploadProgress(percent)
      })

      // 上传后分享
      if (values.share_student_ids && values.share_student_ids.length > 0) {
        await resourcesApi.share(resource.id, values.share_student_ids)
      }

      message.success('资料上传成功')
      setUploadOpen(false)
      setUploadFile(null)
      uploadForm.resetFields()
      setUploadProgress(0)
      fetchResources()
    } catch (err: unknown) {
      const axiosError = err as { response?: { status?: number } }
      if (axiosError.response?.status === 413) {
        message.error('文件大小超出限制（最大 50MB）')
      } else {
        message.error('上传失败，请重试')
      }
    } finally {
      setUploading(false)
    }
  }

  const handleShare = (resource: Resource) => {
    setSharingResource(resource)
    const sharedIds = resource.shared_students?.map((s) => s.student_id) || []
    setSelectedStudentIds(sharedIds)
    setShareOpen(true)
  }

  const handleConfirmShare = async () => {
    if (!sharingResource) return
    setSharing(true)
    try {
      await resourcesApi.share(sharingResource.id, selectedStudentIds)
      message.success('分享成功')
      setShareOpen(false)
      fetchResources()
    } catch {
      message.error('分享失败，请重试')
    } finally {
      setSharing(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await resourcesApi.delete(id)
      message.success('资料已删除')
      fetchResources()
    } catch {
      message.error('删除失败')
    }
  }

  const handleDownload = (resource: Resource) => {
    const url = resourcesApi.getDownloadUrl(resource.id)
    const token = localStorage.getItem('access_token')
    // 通过临时 a 标签下载
    const link = document.createElement('a')
    link.href = `${url}?token=${token}`
    link.download = resource.original_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const draggerProps: UploadProps = {
    beforeUpload: handleBeforeUpload,
    fileList: uploadFile ? [{ uid: uploadFile.uid, name: uploadFile.name, size: uploadFile.size, type: uploadFile.type, originFileObj: uploadFile }] : [],
    onRemove: () => setUploadFile(null),
    multiple: false,
    accept: '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif',
  }

  return (
    <div>
      <PageHeader
        title="资料管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setUploadOpen(true)}>
            上传资料
          </Button>
        }
      />

      <Row gutter={[16, 16]}>
        {/* 左侧分类筛选 */}
        <Col xs={24} sm={6} md={5}>
          <Card style={{ borderRadius: 8 }} bodyStyle={{ padding: '12px 0' }}>
            <div style={{ padding: '0 16px 8px', fontWeight: 600, color: '#374151', fontSize: 13 }}>
              按科目筛选
            </div>
            <div
              style={{
                padding: '8px 16px',
                cursor: 'pointer',
                background: !filterSubject ? '#EFF6FF' : 'transparent',
                color: !filterSubject ? '#2563EB' : '#374151',
                fontWeight: !filterSubject ? 500 : 400,
              }}
              onClick={() => setFilterSubject(undefined)}
            >
              全部文件
            </div>
            {SUBJECTS.map((s) => (
              <div
                key={s}
                style={{
                  padding: '8px 16px',
                  cursor: 'pointer',
                  background: filterSubject === s ? '#EFF6FF' : 'transparent',
                  color: filterSubject === s ? '#2563EB' : '#374151',
                  fontWeight: filterSubject === s ? 500 : 400,
                }}
                onClick={() => setFilterSubject(s)}
              >
                {s}
              </div>
            ))}
          </Card>
        </Col>

        {/* 右侧文件列表 */}
        <Col xs={24} sm={18} md={19}>
          <Card style={{ borderRadius: 8 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <Spin size="large" />
              </div>
            ) : resources.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#9CA3AF' }}>
                <CloudUploadOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                <div>还没有上传资料</div>
                <div style={{ fontSize: 13, marginTop: 4 }}>点击右上角"上传资料"开始添加教学资料</div>
              </div>
            ) : (
              <List
                dataSource={resources}
                pagination={{
                  current: page,
                  pageSize: 20,
                  total,
                  onChange: setPage,
                  size: 'small',
                }}
                renderItem={(resource) => (
                  <List.Item
                    key={resource.id}
                    style={{
                      padding: '16px',
                      border: '1px solid #E5E7EB',
                      borderRadius: 8,
                      marginBottom: 8,
                      background: '#FFFFFF',
                    }}
                    actions={[
                      <Button
                        key="download"
                        type="link"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(resource)}
                      >
                        下载
                      </Button>,
                      <Button
                        key="share"
                        type="link"
                        size="small"
                        icon={<ShareAltOutlined />}
                        onClick={() => handleShare(resource)}
                        style={{ color: '#10B981' }}
                      >
                        分享
                      </Button>,
                      <Popconfirm
                        key="delete"
                        title="确认删除此资料？"
                        description="删除后已分享给学生的资料将无法访问。"
                        onConfirm={() => handleDelete(resource.id)}
                        okText="删除"
                        cancelText="取消"
                        okButtonProps={{ danger: true }}
                      >
                        <Button type="link" size="small" danger icon={<DeleteOutlined />} />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={getFileIcon(resource.file_type)}
                      title={
                        <Space>
                          <Text style={{ fontWeight: 500, color: '#111827' }}>
                            {resource.title}
                          </Text>
                          <Tag color="blue" style={{ fontSize: 11 }}>
                            {getFileTypeLabel(resource.file_type)}
                          </Tag>
                          {resource.subject && <Tag color="cyan" style={{ fontSize: 11 }}>{resource.subject}</Tag>}
                        </Space>
                      }
                      description={
                        <Space wrap size={[8, 4]}>
                          <Text style={{ color: '#9CA3AF', fontSize: 12 }}>
                            {formatFileSize(resource.file_size)}
                          </Text>
                          <Text style={{ color: '#9CA3AF', fontSize: 12 }}>
                            上传于 {formatDate(resource.created_at)}
                          </Text>
                          {resource.shared_students && resource.shared_students.length > 0 ? (
                            <Text style={{ color: '#10B981', fontSize: 12 }}>
                              已分享给 {resource.shared_students.length} 名学生
                            </Text>
                          ) : (
                            <Text style={{ color: '#9CA3AF', fontSize: 12 }}>未分享</Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 上传 Modal */}
      <Modal
        title="上传资料"
        open={uploadOpen}
        onCancel={() => {
          setUploadOpen(false)
          setUploadFile(null)
          uploadForm.resetFields()
          setUploadProgress(0)
        }}
        onOk={() => uploadForm.submit()}
        confirmLoading={uploading}
        okText="上传并保存"
        cancelText="取消"
        width={560}
        destroyOnClose
      >
        <Form form={uploadForm} layout="vertical" onFinish={handleUpload} style={{ marginTop: 16 }}>
          {/* 上传区域 */}
          <Dragger {...draggerProps} style={{ marginBottom: 16 }}>
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined style={{ fontSize: 36, color: '#2563EB' }} />
            </p>
            <p style={{ color: '#374151', fontSize: 14, margin: '8px 0 4px' }}>
              拖拽文件到此处，或点击选择文件
            </p>
            <p style={{ color: '#9CA3AF', fontSize: 12 }}>
              支持 PDF、Word、Excel、图片，单文件 ≤ 50MB
            </p>
          </Dragger>

          {uploading && (
            <Progress percent={uploadProgress} style={{ marginBottom: 12 }} />
          )}

          <Form.Item
            name="title"
            label="资料名称"
            rules={[{ required: true, message: '请输入资料名称' }]}
          >
            <Input placeholder="请输入资料名称" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="subject" label="科目分类">
                <Select
                  placeholder="请选择科目"
                  allowClear
                  options={SUBJECTS.map((s) => ({ value: s, label: s }))}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="resource_type" label="资料类型">
                <Select
                  placeholder="请选择类型"
                  allowClear
                  options={RESOURCE_TYPES}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="备注说明">
            <Input.TextArea placeholder="备注信息（选填）" rows={2} />
          </Form.Item>

          {students.length > 0 && (
            <Form.Item name="share_student_ids" label="立即分享给">
              <Select
                mode="multiple"
                placeholder="选择要分享的学生（可选）"
                options={students.map((s) => ({
                  value: s.id,
                  label: `${s.name} (${s.grade})`,
                }))}
                allowClear
              />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 分享 Modal */}
      <Modal
        title={`分享资料给学生 — ${sharingResource?.title}`}
        open={shareOpen}
        onCancel={() => setShareOpen(false)}
        onOk={handleConfirmShare}
        confirmLoading={sharing}
        okText="确认分享"
        cancelText="取消"
        width={440}
      >
        <div style={{ marginTop: 16 }}>
          <Space style={{ marginBottom: 12 }}>
            <Button
              size="small"
              onClick={() => setSelectedStudentIds(students.map((s) => s.id))}
            >
              全选
            </Button>
            <Button size="small" onClick={() => setSelectedStudentIds([])}>
              清空
            </Button>
          </Space>
          <div style={{ maxHeight: 320, overflow: 'auto' }}>
            {students.map((student) => (
              <div
                key={student.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 0',
                  borderBottom: '1px solid #F3F4F6',
                }}
              >
                <Checkbox
                  checked={selectedStudentIds.includes(student.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedStudentIds((prev) => [...prev, student.id])
                    } else {
                      setSelectedStudentIds((prev) => prev.filter((id) => id !== student.id))
                    }
                  }}
                />
                <Text style={{ color: '#111827' }}>{student.name}</Text>
                <Text style={{ color: '#6B7280', fontSize: 12 }}>
                  {student.grade} · {student.subjects?.join('、')}
                </Text>
              </div>
            ))}
          </div>
          {selectedStudentIds.length > 0 && (
            <div style={{ marginTop: 12, color: '#2563EB', fontSize: 13 }}>
              已选择 {selectedStudentIds.length} 名学生
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

export default ResourcesPage
