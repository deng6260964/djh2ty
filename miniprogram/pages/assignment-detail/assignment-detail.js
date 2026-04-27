// pages/assignment-detail/assignment-detail.js
const { get } = require('../../api/request')
const { formatDate, getDueDateStatus } = require('../../utils/format')

Page({
  data: {
    assignment: null,
    loading: false,
    assignmentId: null
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ assignmentId: id })
      this.loadAssignment(id)
    } else {
      wx.showToast({
        title: '参数错误',
        icon: 'none'
      })
    }
  },

  onPullDownRefresh() {
    if (this.data.assignmentId) {
      this.loadAssignment(this.data.assignmentId).finally(() => {
        wx.stopPullDownRefresh()
      })
    } else {
      wx.stopPullDownRefresh()
    }
  },

  // 加载作业详情
  async loadAssignment(id) {
    this.setData({ loading: true })

    try {
      // 先从列表接口获取（/api/assignments/my 不一定有单个详情接口）
      // 后端可能提供 /api/assignments/{id} 或通过 my 列表参数过滤
      const data = await get(`/api/assignments/${id}`)
      const dueStatus = getDueDateStatus(data.due_date)

      const assignment = {
        ...data,
        dueDateStr: formatDate(data.due_date),
        createdDateStr: formatDate(data.created_at),
        gradedDateStr: data.graded_at ? formatDate(data.graded_at) : '',
        submittedDateStr: data.submitted_at ? formatDate(data.submitted_at) : '',
        dueStatus,
        isGraded: data.status === 'graded',
        isSubmitted: data.status === 'submitted' || data.status === 'graded',
        scoreGrade: data.score ? this.getScoreGrade(data.score) : ''
      }

      this.setData({ assignment, loading: false })

      // 设置页面标题
      wx.setNavigationBarTitle({ title: data.title || '作业详情' })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 根据分数获取等级
  getScoreGrade(score) {
    if (score >= 90) return 'A'
    if (score >= 80) return 'B'
    if (score >= 70) return 'C'
    if (score >= 60) return 'D'
    return 'F'
  }
})
