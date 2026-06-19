/**
 * 小红书账号 Cookie 工具函数
 * 数据管理已迁移到后端数据库（API: /v1/xhs/accounts）
 * 本文件仅保留 Cookie 拼接等纯工具函数
 */

/**
 * 将 a1 和 web_session 拼成完整的 Cookie 字符串
 * 格式：a1=xxx; web_session=yyy
 * @param {{ a1?: string, webSession?: string, web_session?: string }} account
 * @returns {string}
 */
export function buildCookieString(account) {
  if (!account) return ''
  const parts = []
  const a1 = account.a1 || ''
  const ws = account.webSession || account.web_session || ''
  if (a1) parts.push(`a1=${a1}`)
  if (ws) parts.push(`web_session=${ws}`)
  return parts.join('; ')
}
