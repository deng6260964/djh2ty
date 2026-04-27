// pages/progress/progress.js
const { get } = require('../../api/request')
const { formatDate, getKnowledgeStatusInfo } = require('../../utils/format')

Page({
  data: {
    // 科目列表
    subjects: [],
    activeSubjectIndex: 0,
    activeSubject: '',
    // 成绩趋势数据
    gradeData: [],
    // 知识点数据
    knowledgePoints: [],
    // 统计
    masteredCount: 0,
    learningCount: 0,
    todoCount: 0,
    // Canvas 尺寸
    canvasWidth: 350,
    canvasHeight: 200,
    // 加载状态
    loading: false,
    // 是否有数据
    hasGradeData: false,
    hasKnowledgeData: false
  },

  onLoad() {
    this.loadSubjects()
  },

  onShow() {
    this.loadSubjects()
  },

  onPullDownRefresh() {
    this.loadSubjects().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载学生的科目列表（通过知识点接口或成绩接口推断可用科目）
  async loadSubjects() {
    this.setData({ loading: true })

    try {
      // 先尝试获取进度总览（含科目列表）
      // 后端 /api/progress/my 接口返回当前学生的科目和统计信息
      const res = await get('/api/progress/my')
      // 兼容：subjects 可能在 res.subjects 或直接是数组
      let subjects = res.subjects || []

      // 如果没有科目，尝试从成绩记录提取
      if (subjects.length === 0) {
        const gradesRes = await get('/api/progress/grades', {}, { showLoading: false }).catch(() => ({ items: [] }))
        const subjectSet = new Set()
        ;(gradesRes.items || []).forEach(g => g.subject && subjectSet.add(g.subject))
        subjects = Array.from(subjectSet)
      }

      if (subjects.length > 0) {
        this.setData({
          subjects,
          activeSubject: subjects[0],
          activeSubjectIndex: 0,
          loading: false
        })
        this.loadProgressData(subjects[0])
      } else {
        this.setData({ loading: false, subjects: [] })
      }
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 加载某科目的进度数据
  async loadProgressData(subject) {
    this.setData({ loading: true })

    try {
      // 同时请求成绩趋势和知识点
      const [gradeRes, knowledgeRes] = await Promise.all([
        get('/api/progress/grades/trend', { subject }),
        get('/api/progress/knowledge-points', { subject })
      ])

      // 处理成绩数据
      const gradeData = (gradeRes.data || []).map(item => ({
        ...item,
        dateLabel: formatDate(item.exam_date, 'MM-DD'),
        percentage: item.percentage || (item.full_score > 0 ? Math.round(item.score / item.full_score * 100) : 0)
      }))

      // 处理知识点数据
      const knowledgePoints = (knowledgeRes.items || knowledgeRes || []).map(item => ({
        ...item,
        statusInfo: getKnowledgeStatusInfo(item.status)
      }))

      const masteredCount = knowledgePoints.filter(k => k.status === 'mastered').length
      const learningCount = knowledgePoints.filter(k => k.status === 'learning').length
      const todoCount = knowledgePoints.filter(k => k.status === 'todo').length

      this.setData({
        gradeData,
        knowledgePoints,
        masteredCount,
        learningCount,
        todoCount,
        hasGradeData: gradeData.length > 0,
        hasKnowledgeData: knowledgePoints.length > 0,
        loading: false
      })

      // 绘制折线图
      if (gradeData.length > 0) {
        // 获取屏幕宽度适配 canvas
        const { windowWidth } = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync()
        const canvasWidth = Math.floor((windowWidth - 48 - 56) * 1) // 24rpx * 2 边距 + 28rpx * 2 padding
        this.setData({
          canvasWidth: Math.min(canvasWidth, windowWidth - 48),
          canvasHeight: 200
        })
        setTimeout(() => {
          this.drawLineChart(gradeData)
        }, 150)
      }
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 切换科目
  switchSubject(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    const subject = this.data.subjects[index]

    this.setData({
      activeSubjectIndex: index,
      activeSubject: subject,
      gradeData: [],
      knowledgePoints: [],
      hasGradeData: false,
      hasKnowledgeData: false
    })

    this.loadProgressData(subject)
  },

  // 用 Canvas 绘制折线图
  drawLineChart(data) {
    const query = wx.createSelectorQuery()
    query.select('#gradeChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0]) {
          // 降级：使用旧版 canvas API
          this.drawLineChartLegacy(data)
          return
        }

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const { width, height } = res[0]
        const dpr = wx.getWindowInfo ? wx.getWindowInfo().pixelRatio : 2

        canvas.width = width * dpr
        canvas.height = height * dpr
        ctx.scale(dpr, dpr)

        this.renderChart(ctx, data, width, height)
      })
  },

  // 旧版 canvas API（兼容）
  drawLineChartLegacy(data) {
    const ctx = wx.createCanvasContext('gradeChart', this)
    const width = this.data.canvasWidth
    const height = this.data.canvasHeight

    this.renderChartLegacy(ctx, data, width, height)
    ctx.draw()
  },

  // 渲染图表（新版）
  renderChart(ctx, data, width, height) {
    const padding = { top: 20, right: 20, bottom: 40, left: 40 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    // 清空
    ctx.clearRect(0, 0, width, height)

    // 数据处理
    const scores = data.map(d => d.score)
    const maxScore = Math.max(...scores, 100)
    const minScore = Math.max(Math.min(...scores) - 10, 0)
    const scoreRange = maxScore - minScore || 1

    const points = data.map((d, i) => ({
      x: padding.left + (i / Math.max(data.length - 1, 1)) * chartWidth,
      y: padding.top + chartHeight - ((d.score - minScore) / scoreRange) * chartHeight,
      score: d.score,
      label: d.dateLabel || d.exam_name || ''
    }))

    // 绘制网格线
    ctx.strokeStyle = '#F3F4F6'
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (i / 4) * chartHeight
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(width - padding.right, y)
      ctx.stroke()
    }

    // 绘制折线
    if (points.length > 1) {
      ctx.beginPath()
      ctx.strokeStyle = '#2563EB'
      ctx.lineWidth = 3
      ctx.lineJoin = 'round'
      ctx.moveTo(points[0].x, points[0].y)
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y))
      ctx.stroke()

      // 渐变填充
      const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight)
      gradient.addColorStop(0, 'rgba(37,99,235,0.18)')
      gradient.addColorStop(1, 'rgba(37,99,235,0)')
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y))
      ctx.lineTo(points[points.length - 1].x, padding.top + chartHeight)
      ctx.lineTo(points[0].x, padding.top + chartHeight)
      ctx.closePath()
      ctx.fillStyle = gradient
      ctx.fill()
    }

    // 绘制数据点
    points.forEach(p => {
      ctx.beginPath()
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2)
      ctx.fillStyle = '#FFFFFF'
      ctx.fill()
      ctx.strokeStyle = '#2563EB'
      ctx.lineWidth = 3
      ctx.stroke()

      // 分数标签
      ctx.fillStyle = '#374151'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(String(p.score), p.x, p.y - 10)
    })

    // 绘制 X 轴标签
    ctx.fillStyle = '#9CA3AF'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    points.forEach(p => {
      ctx.fillText(p.label, p.x, height - 8)
    })
  },

  // 渲染图表（旧版 API）
  renderChartLegacy(ctx, data, width, height) {
    const padding = { top: 20, right: 20, bottom: 40, left: 40 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    const scores = data.map(d => d.score)
    const maxScore = Math.max(...scores, 100)
    const minScore = Math.max(Math.min(...scores) - 10, 0)
    const scoreRange = maxScore - minScore || 1

    const points = data.map((d, i) => ({
      x: padding.left + (i / Math.max(data.length - 1, 1)) * chartWidth,
      y: padding.top + chartHeight - ((d.score - minScore) / scoreRange) * chartHeight,
      score: d.score,
      label: d.dateLabel || ''
    }))

    // 网格线
    ctx.setStrokeStyle('#F3F4F6')
    ctx.setLineWidth(1)
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (i / 4) * chartHeight
      ctx.beginPath()
      ctx.moveTo(padding.left, y)
      ctx.lineTo(width - padding.right, y)
      ctx.stroke()
    }

    // 折线
    if (points.length > 1) {
      ctx.setStrokeStyle('#2563EB')
      ctx.setLineWidth(3)
      ctx.setLineJoin('round')
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y))
      ctx.stroke()
    }

    // 数据点和标签
    points.forEach(p => {
      ctx.beginPath()
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2)
      ctx.setFillStyle('#FFFFFF')
      ctx.fill()
      ctx.setStrokeStyle('#2563EB')
      ctx.setLineWidth(3)
      ctx.stroke()

      ctx.setFillStyle('#374151')
      ctx.setFontSize(11)
      ctx.setTextAlign('center')
      ctx.fillText(String(p.score), p.x, p.y - 10)
    })

    // X 轴标签
    ctx.setFillStyle('#9CA3AF')
    ctx.setFontSize(10)
    ctx.setTextAlign('center')
    points.forEach(p => {
      ctx.fillText(p.label, p.x, height - 8)
    })
  }
})
