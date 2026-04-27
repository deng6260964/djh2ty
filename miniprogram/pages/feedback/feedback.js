// pages/feedback/feedback.js
const { get } = require('../../api/request')
const { formatDate, formatTime, truncateText } = require('../../utils/format')

Page({
  data: {
    feedbackList: [],
    loading: false,
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    isLoadingMore: false
  },

  onLoad() {
    this.loadFeedback()
  },

  onShow() {
    // 重新加载第一页
    this.setData({ page: 1, feedbackList: [], hasMore: true })
    this.loadFeedback()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, feedbackList: [], hasMore: true })
    this.loadFeedback().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.isLoadingMore) {
      this.loadMoreFeedback()
    }
  },

  // 加载反馈列表
  async loadFeedback() {
    this.setData({ loading: true })

    try {
      const res = await get('/api/feedback/my', {
        page: 1,
        page_size: this.data.pageSize
      })

      const feedbackList = this.processFeedback(res.items || [])

      this.setData({
        feedbackList,
        total: res.total || 0,
        page: 1,
        hasMore: feedbackList.length < (res.total || 0),
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 加载更多
  async loadMoreFeedback() {
    if (this.data.isLoadingMore || !this.data.hasMore) return

    this.setData({ isLoadingMore: true })

    const nextPage = this.data.page + 1

    try {
      const res = await get('/api/feedback/my', {
        page: nextPage,
        page_size: this.data.pageSize
      }, { showLoading: false })

      const newItems = this.processFeedback(res.items || [])
      const feedbackList = [...this.data.feedbackList, ...newItems]

      this.setData({
        feedbackList,
        page: nextPage,
        hasMore: feedbackList.length < (res.total || 0),
        isLoadingMore: false
      })
    } catch (err) {
      this.setData({ isLoadingMore: false })
    }
  },

  // 处理反馈数据
  processFeedback(items) {
    return items.map(item => ({
      ...item,
      dateStr: formatDate(item.course_date || item.created_at),
      timeStr: item.course_start_time ? formatTime(item.course_start_time) : '',
      performancePreview: truncateText(item.performance || '', 50),
      courseLabel: item.subject ? `${item.subject}课` : '课程'
    }))
  },

  // 点击进入详情
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/feedback-detail/feedback-detail?id=${id}`
    })
  }
})
