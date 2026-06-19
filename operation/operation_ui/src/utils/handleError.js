import { ElNotification } from 'element-plus'

/**
 * 统一异常处理
 * @param {import('axios').AxiosError} error
 */
export function handleError(error) {
  if (error.response) {
    const { status, data } = error.response
    ElNotification.error({
      title: '请求错误',
      message: (data && data.message) ? data.message : `状态码: ${status}`,
    })
  } else {
    ElNotification.error({
      title: '网络异常',
      message: '请检查网络连接',
    })
  }
}
