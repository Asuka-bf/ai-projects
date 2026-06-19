import axios from 'axios'
import { handleError } from '@/utils/handleError'
import { getCookie } from '@/utils/cookie'
import config from '@/config'

const instance = axios.create({
  baseURL: config.baseURL,
  timeout: config.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截：为后端验证携带 token
instance.interceptors.request.use(
  (config) => {
    const token = getCookie('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (err) => Promise.reject(err)
)

instance.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== undefined && res.code !== 200) {
      handleError({ response: { status: res.code, data: { message: res.message } } })
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    // 仅当 data 有值时才解包，否则返回完整 res（避免 data 为 null 时拿到空）
    return (res.data !== undefined && res.data !== null) ? res.data : res
  },
  (error) => {
    handleError(error)
    return Promise.reject(error)
  }
)

export const http = instance
