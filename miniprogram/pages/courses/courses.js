// pages/courses/courses.js
const { get } = require('../../api/request')
const { formatDate, formatTime, formatDuration, getCourseStatusInfo, isToday, formatMonth } = require('../../utils/format')

Page({
  data: {
    // 当前年月
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,
    // 选中的日期
    selectedDate: formatDate(new Date()),
    // 日历数据（当月每一天）
    calendarDays: [],
    // 有课的日期集合（用于显示蓝点）
    courseDates: {},
    // 当天课程列表
    dayCourses: [],
    // 所有课程（当月）
    allCourses: [],
    // 加载状态
    loading: false,
    // 月份标题
    monthTitle: ''
  },

  onLoad() {
    this.initCalendar()
    this.loadMonthCourses()
  },

  onShow() {
    // 从后台切回时刷新
    this.loadMonthCourses()
  },

  onPullDownRefresh() {
    this.loadMonthCourses().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 初始化日历
  initCalendar() {
    const { currentYear, currentMonth } = this.data
    const days = this.generateCalendarDays(currentYear, currentMonth)
    const monthTitle = formatMonth(currentYear, currentMonth)

    this.setData({
      calendarDays: days,
      monthTitle
    })
  },

  // 生成日历天数数组
  generateCalendarDays(year, month) {
    const firstDay = new Date(year, month - 1, 1)
    const lastDay = new Date(year, month, 0)
    const firstDayOfWeek = firstDay.getDay() // 0=周日

    const days = []

    // 前置空白格
    for (let i = 0; i < firstDayOfWeek; i++) {
      days.push({ day: 0, dateStr: '', isEmpty: true })
    }

    // 当月天数
    const today = formatDate(new Date())
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
      days.push({
        day: d,
        dateStr,
        isEmpty: false,
        isToday: dateStr === today
      })
    }

    return days
  },

  // 加载当月课程
  async loadMonthCourses() {
    const { currentYear, currentMonth } = this.data

    const startDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-01`
    const lastDay = new Date(currentYear, currentMonth, 0).getDate()
    const endDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

    this.setData({ loading: true })

    try {
      const res = await get('/api/courses/my', {
        start_date: startDate,
        end_date: endDate,
        page_size: 200
      })

      const courses = (res.items || []).map(course => ({
        ...course,
        startTimeStr: formatTime(course.start_time),
        endTimeStr: formatTime(course.end_time),
        durationStr: formatDuration(course.duration),
        dateStr: formatDate(course.start_time),
        statusInfo: getCourseStatusInfo(course.status)
      }))

      // 构建有课日期集合
      const courseDates = {}
      courses.forEach(c => {
        if (c.dateStr) courseDates[c.dateStr] = true
      })

      // 更新日历天数的蓝点标记
      const calendarDays = this.data.calendarDays.map(d => ({
        ...d,
        hasCourse: d.dateStr ? !!courseDates[d.dateStr] : false
      }))

      this.setData({
        allCourses: courses,
        courseDates,
        calendarDays,
        loading: false
      })

      // 刷新选中日期的课程
      this.filterDayCourses(this.data.selectedDate, courses)
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 筛选某天的课程
  filterDayCourses(dateStr, courses) {
    const allCourses = courses || this.data.allCourses
    const dayCourses = allCourses.filter(c => c.dateStr === dateStr)
    // 按开始时间排序
    dayCourses.sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    this.setData({ dayCourses })
  },

  // 点击日期
  onDateTap(e) {
    const { dateStr, isEmpty } = e.currentTarget.dataset
    if (isEmpty || !dateStr) return

    this.setData({ selectedDate: dateStr })
    this.filterDayCourses(dateStr)
  },

  // 切换到上个月
  prevMonth() {
    let { currentYear, currentMonth } = this.data
    currentMonth--
    if (currentMonth < 1) {
      currentMonth = 12
      currentYear--
    }

    const days = this.generateCalendarDays(currentYear, currentMonth)
    const monthTitle = formatMonth(currentYear, currentMonth)

    // 选中新月份的1号
    const newSelectedDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-01`

    this.setData({
      currentYear,
      currentMonth,
      calendarDays: days,
      monthTitle,
      selectedDate: newSelectedDate,
      dayCourses: []
    })

    this.loadMonthCourses()
  },

  // 切换到下个月
  nextMonth() {
    let { currentYear, currentMonth } = this.data
    currentMonth++
    if (currentMonth > 12) {
      currentMonth = 1
      currentYear++
    }

    const days = this.generateCalendarDays(currentYear, currentMonth)
    const monthTitle = formatMonth(currentYear, currentMonth)

    const newSelectedDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-01`

    this.setData({
      currentYear,
      currentMonth,
      calendarDays: days,
      monthTitle,
      selectedDate: newSelectedDate,
      dayCourses: []
    })

    this.loadMonthCourses()
  }
})
