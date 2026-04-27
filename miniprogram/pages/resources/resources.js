// pages/resources/resources.js
const { get } = require('../../api/request')
const { formatDate, formatFileSize, getFileTypeIcon, getFileTypeColor } = require('../../utils/format')

Page({
  data: {
    // 资料列表
    resourceList: [],
    // 筛选后的资料
    filteredList: [],
    // 科目标签
    subjects: ['全部'],
    activeSubject: '全部',
    // 加载状态
    loading: false,
    // 下载状态（资料ID为key）
    downloadingMap: {},
    // 分页
    page: 1,
    pageSize: 30,
    hasMore: true,
    isLoadingMore: false
  },

  onLoad() {
    this.loadResources()
  },

  onShow() {
    this.loadResources()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, resourceList: [], hasMore: true })
    this.loadResources().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.isLoadingMore) {
      this.loadMoreResources()
    }
  },

  // 加载资料列表
  async loadResources() {
    this.setData({ loading: true })

    try {
      const res = await get('/api/resources/shared', {
        page: 1,
        page_size: this.data.pageSize
      })

      const resourceList = this.processResources(res.items || [])

      // 提取科目分类
      const subjectSet = new Set(['全部'])
      resourceList.forEach(r => {
        if (r.subject) subjectSet.add(r.subject)
      })
      const subjects = Array.from(subjectSet)

      this.setData({
        resourceList,
        subjects,
        page: 1,
        hasMore: resourceList.length < (res.total || 0),
        loading: false
      })

      this.filterBySubject(this.data.activeSubject)
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 加载更多
  async loadMoreResources() {
    this.setData({ isLoadingMore: true })
    const nextPage = this.data.page + 1

    try {
      const res = await get('/api/resources/shared', {
        page: nextPage,
        page_size: this.data.pageSize
      }, { showLoading: false })

      const newItems = this.processResources(res.items || [])
      const resourceList = [...this.data.resourceList, ...newItems]

      this.setData({
        resourceList,
        page: nextPage,
        hasMore: resourceList.length < (res.total || 0),
        isLoadingMore: false
      })

      this.filterBySubject(this.data.activeSubject)
    } catch (err) {
      this.setData({ isLoadingMore: false })
    }
  },

  // 处理资料数据
  processResources(items) {
    return items.map(item => ({
      ...item,
      sharedDateStr: formatDate(item.shared_at || item.created_at),
      fileSizeStr: formatFileSize(item.file_size),
      fileTypeIcon: getFileTypeIcon(item.file_type, item.original_name || item.title),
      fileTypeColor: getFileTypeColor(item.file_type, item.original_name || item.title),
      displayName: item.original_name || item.title,
      isImage: (item.file_type || '').includes('image') ||
        ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(
          (item.original_name || '').split('.').pop()?.toLowerCase() || ''
        )
    }))
  },

  // 按科目筛选
  filterBySubject(subject) {
    let filteredList
    if (subject === '全部') {
      filteredList = this.data.resourceList
    } else {
      filteredList = this.data.resourceList.filter(r => r.subject === subject)
    }
    this.setData({ filteredList })
  },

  // 切换科目
  switchSubject(e) {
    const subject = e.currentTarget.dataset.subject
    this.setData({ activeSubject: subject })
    this.filterBySubject(subject)
  },

  // 预览/下载资料
  handleFile(e) {
    const { id, isImage, downloadUrl, filename, fileType } = e.currentTarget.dataset

    if (isImage === true || isImage === 'true') {
      // 图片直接预览
      this.previewImage(id, downloadUrl)
    } else {
      // 文档下载后打开
      this.downloadAndOpen(id, downloadUrl, filename, fileType)
    }
  },

  // 预览图片
  previewImage(id, url) {
    const app = getApp()
    const token = wx.getStorageSync('token')
    const baseUrl = app.globalData.apiBaseUrl || 'http://localhost:8000'

    const imageUrl = url || `${baseUrl}/api/resources/${id}/download`

    wx.previewImage({
      urls: [imageUrl],
      current: imageUrl,
      fail() {
        wx.showToast({ title: '预览失败', icon: 'none' })
      }
    })
  },

  // 下载并打开文件
  downloadAndOpen(id, url, filename, fileType) {
    const app = getApp()
    const token = wx.getStorageSync('token')
    const baseUrl = app.globalData.apiBaseUrl || 'http://localhost:8000'

    const downloadUrl = url || `${baseUrl}/api/resources/${id}/download`

    // 标记下载中
    const downloadingMap = { ...this.data.downloadingMap, [id]: true }
    this.setData({ downloadingMap })

    wx.showLoading({ title: '下载中...', mask: true })

    wx.downloadFile({
      url: downloadUrl,
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success(res) {
        wx.hideLoading()
        if (res.statusCode === 200) {
          wx.openDocument({
            filePath: res.tempFilePath,
            fileType: fileType || '',
            showMenu: true,
            success() {
              wx.showToast({ title: '打开成功', icon: 'success', duration: 1500 })
            },
            fail(err) {
              wx.showToast({ title: '无法打开此文件', icon: 'none' })
            }
          })
        } else {
          wx.showToast({ title: '下载失败', icon: 'none' })
        }
      },
      fail() {
        wx.hideLoading()
        wx.showToast({ title: '下载失败，请检查网络', icon: 'none' })
      },
      complete: () => {
        const downloadingMap = { ...this.data.downloadingMap }
        delete downloadingMap[id]
        this.setData({ downloadingMap })
      }
    })
  }
})
