// pages/assignments/assignments.js
const { get } = require('../../api/request')
const { formatDate, getDueDateStatus, getAssignmentStatusInfo, truncateText } = require('../../utils/format')

Page({
  data: {
    // 当前 Tab：0=待完成，1=已完成
    activeTab: 0,
    // 作业列表
    pendingList: [],
    completedList: [],
    // 加载状态
    loading: false,
    // 待完成数量（用于 Tab 角标）
    pendingCount: 0
  },

  onLoad() {
    this.loadAssignments()
  },

  onShow() {
    this.loadAssignments()
  },

  onPullDownRefresh() {
    this.loadAssignments().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载作业列表
  async loadAssignments() {
    this.setData({ loading: true })

    try {
      // 同时请求待完成和已完成的作业
      const [pendingRes, completedRes] = await Promise.all([
        get('/api/assignments/my', { status: 'pending' }),
        get('/api/assignments/my', { status: 'completed' })
      ])

      const pendingList = this.processAssignments(pendingRes.items || [])
      const completedList = this.processAssignments(completedRes.items || [])

      // 按截止日期升序排列待完成（最紧急在前）
      pendingList.sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
      // 已完成按完成时间倒序
      completedList.sort((a, b) => new Date(b.submitted_at || b.graded_at || b.created_at) - new Date(a.submitted_at || a.graded_at || a.created_at))

      this.setData({
        pendingList,
        completedList,
        pendingCount: pendingList.length,
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 处理作业数据
  processAssignments(items) {
    return items.map(item => {
      const dueStatus = getDueDateStatus(item.due_date)
      const statusInfo = getAssignmentStatusInfo(item.status)

      return {
        ...item,
        dueDateStr: formatDate(item.due_date),
        dueStatus,
        statusInfo,
        isUrgent: dueStatus.urgent,
        commentPreview: item.comment ? truncateText(item.comment, 40) : ''
      }
    })
  },

  // 切换 Tab
  switchTab(e) {
    const tabIndex = parseInt(e.currentTarget.dataset.tab)
    this.setData({ activeTab: tabIndex })
  },

  // 点击作业卡片，进入详情
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/assignment-detail/assignment-detail?id=${id}`
    })
  }
})
