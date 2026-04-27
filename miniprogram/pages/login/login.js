// pages/login/login.js
const { login } = require('../../utils/auth')

Page({
  data: {
    loading: false,
    errorMsg: ''
  },

  onLoad() {
    // 如果已登录，直接跳转课程页
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({
        url: '/pages/courses/courses'
      })
    }
  },

  // 微信一键登录
  handleLogin() {
    if (this.data.loading) return

    this.setData({
      loading: true,
      errorMsg: ''
    })

    login()
      .then(() => {
        this.setData({ loading: false })

        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        })

        // 登录成功后跳转课程页（Tab 页，用 switchTab 或 redirectTo）
        setTimeout(() => {
          wx.switchTab({
            url: '/pages/courses/courses'
          })
        }, 1000)
      })
      .catch(err => {
        this.setData({
          loading: false,
          errorMsg: err.message || '登录失败，请重试'
        })

        wx.showToast({
          title: err.message || '登录失败',
          icon: 'none',
          duration: 3000
        })
      })
  }
})
