// utils/auth.js - 认证工具
const { post } = require('../api/request')

/**
 * 微信登录
 * 1. wx.login() 获取 code
 * 2. 调用 /api/auth/wechat 接口换取 token
 * 3. 保存 token 和用户信息
 */
function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          reject({ message: '微信登录失败，请重试' })
          return
        }

        const code = loginRes.code

        // 调用后端微信登录接口
        post('/api/auth/wechat', {
          code: code
        }, { showLoading: false })
          .then(data => {
            // 保存 token
            const token = data.access_token
            wx.setStorageSync('token', token)

            // 保存用户信息
            const userInfo = data.user
            wx.setStorageSync('userInfo', userInfo)

            // 保存 studentId（如果有）
            if (userInfo && userInfo.student_id) {
              wx.setStorageSync('studentId', userInfo.student_id)
            }

            // 更新全局数据
            const app = getApp()
            if (app) {
              app.globalData.token = token
              app.globalData.userInfo = userInfo
              app.globalData.studentId = userInfo?.student_id
            }

            resolve(data)
          })
          .catch(err => {
            // 该微信未绑定学生账号
            if (err.code === 'WECHAT_LOGIN_FAILED' || err.code === 'ERROR') {
              reject({ message: '你的微信尚未绑定学生账号，请联系老师', code: 'NOT_BOUND' })
            } else {
              reject(err)
            }
          })
      },
      fail(err) {
        reject({ message: '微信登录失败，请重试', error: err })
      }
    })
  })
}

/**
 * 获取 token
 */
function getToken() {
  return wx.getStorageSync('token') || null
}

/**
 * 退出登录
 */
function logout() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('userInfo')
  wx.removeStorageSync('studentId')

  const app = getApp()
  if (app) {
    app.globalData.token = null
    app.globalData.userInfo = null
    app.globalData.studentId = null
  }

  wx.redirectTo({
    url: '/pages/login/login'
  })
}

/**
 * 检查是否已登录
 */
function isLoggedIn() {
  const token = getToken()
  return !!token
}

/**
 * 获取用户信息
 */
function getUserInfo() {
  return wx.getStorageSync('userInfo') || null
}

/**
 * 获取学生 ID
 */
function getStudentId() {
  return wx.getStorageSync('studentId') || null
}

module.exports = {
  login,
  getToken,
  logout,
  isLoggedIn,
  getUserInfo,
  getStudentId
}
