// pages/feedback-detail/feedback-detail.js
const { get } = require('../../api/request')
const { formatDate, formatTime } = require('../../utils/format')

Page({
  data: {
    feedback: null,
    loading: false,
    feedbackId: null
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ feedbackId: id })
      this.loadFeedback(id)
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      })
    }
  },

  onPullDownRefresh() {
    if (this.data.feedbackId) {
      this.loadFeedback(this.data.feedbackId).finally(() => {
        wx.stopPullDownRefresh()
      })
    } else {
      wx.stopPullDownRefresh()
    }
  },

  // 加载反馈详情
  async loadFeedback(id) {
    this.setData({ loading: true })

    try {
      const data = await get(`/api/feedback/my/${id}`)

      const feedback = {
        ...data,
        dateStr: formatDate(data.course_date || data.created_at),
        timeStr: data.course_start_time ? formatTime(data.course_start_time) : '',
        endTimeStr: data.course_end_time ? formatTime(data.course_end_time) : '',
        createdDateStr: formatDate(data.created_at),
        courseLabel: data.subject ? `${data.subject}课` : '课程',
        timeRange: data.course_start_time && data.course_end_time
          ? `${formatTime(data.course_start_time)} - ${formatTime(data.course_end_time)}`
          : ''
      }

      this.setData({ feedback, loading: false })

      // 设置页面标题
      wx.setNavigationBarTitle({
        title: `${feedback.courseLabel}反馈`
      })
    } catch (err) {
      this.setData({ loading: false })
    }
  }
})
