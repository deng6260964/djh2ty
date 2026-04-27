// app.js - 全局入口
const { getToken, isLoggedIn } = require('./utils/auth')

App({
  globalData: {
    userInfo: null,
    token: null,
    apiBaseUrl: 'http://localhost:8000',  // 开发环境
    // apiBaseUrl: 'https://your-server.com',  // 生产环境（预留）
    studentId: null
  },

  onLaunch() {
    // 检查本地 token，有则跳过登录页
    const token = getToken()
    if (token) {
      this.globalData.token = token
      const userInfo = wx.getStorageSync('userInfo')
      if (userInfo) {
        this.globalData.userInfo = userInfo
        this.globalData.studentId = wx.getStorageSync('studentId')
      }
      // token 有效，跳转到课程 Tab
      wx.switchTab({
        url: '/pages/courses/courses'
      })
    } else {
      // 无 token，跳转到登录页
      wx.redirectTo({
        url: '/pages/login/login'
      })
    }
  },

  onShow() {
    // 从后台切回前台时，检查 token 有效性
    const token = getToken()
    if (!token) {
      wx.redirectTo({
        url: '/pages/login/login'
      })
    }
  }
})
