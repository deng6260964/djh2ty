// api/request.js - 请求封装
const app = getApp()

/**
 * 封装 wx.request，功能：
 * 1. 统一 baseURL
 * 2. 自动加 Authorization header（从 storage 读 token）
 * 3. 统一错误处理（401 跳登录，显示 toast）
 * 4. Promise 化
 */

function request(options) {
  const { url, method = 'GET', data = {}, showLoading = true, loadingText = '加载中...' } = options

  // 获取 token
  const token = wx.getStorageSync('token')
  const baseUrl = app.globalData.apiBaseUrl || 'http://localhost:8000'

  // 显示加载
  if (showLoading) {
    wx.showLoading({
      title: loadingText,
      mask: true
    })
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${url}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success(res) {
        if (showLoading) {
          wx.hideLoading()
        }

        const { statusCode, data: responseData } = res

        // 成功响应
        if (statusCode >= 200 && statusCode < 300) {
          resolve(responseData)
          return
        }

        // 401 未授权 - 跳转登录
        if (statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.removeStorageSync('studentId')

          wx.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
          })

          setTimeout(() => {
            wx.redirectTo({
              url: '/pages/login/login'
            })
          }, 1500)

          reject({ code: 'TOKEN_EXPIRED', message: '登录已过期' })
          return
        }

        // 403 权限不足
        if (statusCode === 403) {
          wx.showToast({
            title: '无权访问此内容',
            icon: 'none',
            duration: 2000
          })
          reject({ code: 'PERMISSION_DENIED', message: '无权访问', data: responseData })
          return
        }

        // 404 资源不存在
        if (statusCode === 404) {
          reject({ code: 'NOT_FOUND', message: '请求的内容不存在', data: responseData })
          return
        }

        // 其他错误
        const errorMsg = responseData?.message || '请求失败，请稍后重试'
        wx.showToast({
          title: errorMsg.length > 7 ? '请求失败' : errorMsg,
          icon: 'none',
          duration: 2000
        })

        reject({ code: responseData?.code || 'ERROR', message: errorMsg, data: responseData })
      },
      fail(err) {
        if (showLoading) {
          wx.hideLoading()
        }

        // 网络错误
        wx.showToast({
          title: '网络异常，请检查网络',
          icon: 'none',
          duration: 2000
        })

        reject({ code: 'NETWORK_ERROR', message: '网络异常', error: err })
      }
    })
  })
}

// GET 请求
function get(url, params = {}, options = {}) {
  // 处理查询参数
  const queryString = Object.keys(params)
    .filter(key => params[key] !== undefined && params[key] !== null && params[key] !== '')
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  const fullUrl = queryString ? `${url}?${queryString}` : url

  return request({
    url: fullUrl,
    method: 'GET',
    ...options
  })
}

// POST 请求
function post(url, data = {}, options = {}) {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

// PUT 请求
function put(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

// PATCH 请求
function patch(url, data = {}, options = {}) {
  return request({
    url,
    method: 'PATCH',
    data,
    ...options
  })
}

// DELETE 请求
function del(url, options = {}) {
  return request({
    url,
    method: 'DELETE',
    ...options
  })
}

module.exports = { request, get, post, put, patch, del }
