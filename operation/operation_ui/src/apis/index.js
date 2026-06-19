import { http } from './request'

/**
 * 登录
 * @param {{ userName: string, password: string, terminal: string }} data
 */
export function login(data) {
  return http({
    url: '/login',
    method: 'post',
    data,
  })
}

/**
 * 按主题创建：调用 agent 生成板块与标题，落库后返回（接口较慢，使用更长超时）
 * @param {{ theme: string }} data
 * @returns {Promise<{ sections: Array<{ id: number, name: string, titles: Array<{ id: number, section_id?: number, title: string, sort_order: number, content?: string, status?: string, view_count?: string, like_count?: string, created_at?: string, updated_at?: string }> }> }>}
 */
export function createStart(data) {
  return http({
    url: '/v1/create/start',
    method: 'post',
    data,
    timeout: 90000, // 90 秒，等待 agent 生成
  })
}

/**
 * 检索已有主题列表（按名称模糊），用于直接进入流程不调慢接口
 * @param {{ keyword?: string }} params
 * @returns {Promise<{ themes: string[] }>}
 */
export function createThemes(params = {}) {
  return http({
    url: '/v1/create/themes',
    method: 'get',
    params,
  })
}

/**
 * 按主题名从数据库加载板块与标题，不调 agent
 * @param {{ theme: string }} params
 * @returns {Promise<{ sections: Array<{ id: number, name: string, titles: Array<{ id: number, section_id?: number, title: string, sort_order: number, content?: string, status?: string, view_count?: string, like_count?: string, created_at?: string, updated_at?: string }> }> }>}
 */
export function createLoad(params) {
  return http({
    url: '/v1/create/load',
    method: 'get',
    params,
  })
}

/**
 * 获取风格列表（t_style），用于图片生成步骤选择风格
 * @returns {Promise<{ list: Array<{ id: number, name: string, fengge: string, create_time: string|null }> }>}
 */
export function getStyles() {
  return http({
    url: '/v1/create/styles',
    method: 'get',
  })
}

/**
 * 获取模型列表（t_models），仅可用模型，可按类型过滤
 * @param {{ type?: 'text'|'image' }} params
 * @returns {Promise<{ list: Array<{ id: number, name: string, type: string, version: string, description: string }> }>}
 */
export function getModels(params = {}) {
  return http({
    url: '/v1/create/models',
    method: 'get',
    params,
  })
}

/**
 * 根据标题 ID 查询标题详情（含是否已有文案），用于生成文案前先查库并回显
 * @param {number} titleId
 * @returns {Promise<{ id: number, title: string, content?: string, status?: string, ... }>}
 */
export function getTitleDetail(titleId) {
  return http({
    url: `/v1/create/title/${titleId}`,
    method: 'get',
  })
}

/**
 * 文案编导：根据选中标题调用内容创作 agent 生成文案；若传 title_id 则同时落库并置状态为已生成
 * @param {{ title_text: string, theme?: string, title_id?: number }} data
 * @returns {Promise<{ content: string }>}
 */
export function createCopy(data) {
  return http({
    url: '/v1/create/copy',
    method: 'post',
    data,
    timeout: 60000,
  })
}

/**
 * 保存文案：仅更新标题的 content 字段和 status
 * @param {number} titleId 标题 ID
 * @param {{ content: string }} data 文案内容
 * @returns {Promise<{ id: number }>}
 */
export function saveCopy(titleId, data) {
  return http({
    url: '/v1/create/save-copy',
    method: 'post',
    params: { title_id: titleId },
    data,
  })
}

/**
 * 生成封面：调用图像生成并保存到 t_title_images，更新标题状态
 * @param {{ title_id: number, prompt: string }} data
 * @returns {Promise<{ image_url: string }>}
 */
export function generateCover(data) {
  return http({
    url: '/v1/create/cover',
    method: 'post',
    data,
    timeout: 90000,
  })
}

/**
 * 上传封面/正文图片：上传到 OSS 并写入 t_title_images
 * @param {FormData} formData 需包含 file（图片文件）
 * @param {number} titleId 所属标题 ID（作为 Query 参数 title_id）
 * @returns {Promise<{ image_url: string, image_id: number }>}
 */
export function uploadTitleImage(formData, titleId) {
  const params = titleId != null ? { title_id: titleId } : {}
  return http({
    url: '/v1/create/cover/upload',
    method: 'post',
    data: formData,
    params,
    headers: {
      'Content-Type': false, // FormData 由浏览器设置 multipart boundary
    },
    timeout: 60000,
  })
}

/**
 * 素材库：根据用户 id 获取该用户的素材图片列表（t_title_images, title_id=0）
 * @param {{ user_id?: number|string }} params 可选，传入 user_id 时按该用户查询（需与当前登录用户一致）
 * @returns {Promise<{ list: Array<{ id: number, image_url: string, created_at: string, ... }> }>}
 */
export function getMaterialImages(params = {}) {
  return http({
    url: '/v1/material/images',
    method: 'get',
    params,
  })
}

/**
 * 素材库：上传图片到 OSS 并写入 t_title_images（素材库）
 * @param {FormData} formData 需包含 file（图片文件）
 * @returns {Promise<{ image_url: string }>}
 */
export function uploadMaterialImage(formData) {
  return http({
    url: '/v1/material/image/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': false,
    },
    timeout: 60000,
  })
}

/**
 * 素材库：删除图片
 * @param {number} imageId 图片 ID
 */
export function deleteMaterialImage(imageId) {
  return http({
    url: `/v1/material/image/${imageId}`,
    method: 'delete',
  })
}

/**
 * 素材库：获取当前用户生成过的文案列表（t_titles 中 content 不为空，按 section 归属 user_id）
 * @returns {Promise<{ list: Array<{ id: number, title: string, content: string, created_at: string }> }>}
 */
export function getMaterialCopies() {
  return http({
    url: '/v1/material/copies',
    method: 'get',
  })
}

/**
 * 历史记录：获取当前用户下状态为已发布（status=4）的标题列表
 * @param {{ keyword?: string, page?: number, page_size?: number }} params
 * @returns {Promise<{ list: Array<{ id: number, section_id: number, section_name: string, title: string, content: string, status: string, view_count?: string, like_count?: string, created_at: string, updated_at: string }>, total: number }>}
 */
export function getHistoryList(params = {}) {
  return http({
    url: '/v1/history/list',
    method: 'get',
    params,
  })
}

/**
 * 更新标题的标题、文案与正文图（发布前若用户修改了则先调用此接口）
 * @param {number} titleId
 * @param {{ title: string, content: string, image_urls: string[] }} data
 * @returns {Promise<{ id: number }>}
 */
export function updateTitle(titleId, data) {
  return http({
    url: `/v1/create/title/${titleId}`,
    method: 'put',
    data,
  })
}

/**
 * 发布到小红书：后端根据 title_id 查询标题、文案、图片，用 account_ids 对应的账号发布
 * @param {{ title_id: number, account_ids: number[] }} data
 * @returns {Promise<{ code: number, message: string, data: { results: Array } }>}
 */
export function publishXiaohongshu(data) {
  return http({
    url: '/v1/create/publish',
    method: 'post',
    data,
    timeout: 130000,
  })
}

/**
 * 创建发布记录（t_publish_records），在进入「图片生成」步骤前调用
 * @param {{ titles_id: number, content?: string }} params
 * @returns {Promise<{ id: number, title_id: number, platform: number, publish_status: number }>}
 */
export function createPublishRecord(params) {
  return http({
    url: '/v1/records/create_publish_records',
    method: 'post',
    params,
  })
}

/**
 * 根据发布记录 ID 查询关联的图片列表（t_publish_images + t_title_images）
 * @param {{ publish_id: number }} params
 * @returns {Promise<{ list: Array<{ id: number, publish_id: number, image_id: number, image_url: string, image_type: number, sort_order: number }> }>}
 */
export function getPublishImages(params) {
  return http({
    url: '/v1/publish_images/get_publish_images',
    method: 'get',
    params,
  })
}

/**
 * 历史记录：获取当前用户的发布记录列表（t_publish_records）
 * 根据用户 ID（通过 token 解析）返回其在各平台上的发布记录，按 ID 倒序
 * @param {{}} params 预留扩展参数（如平台、状态过滤），当前后端未使用
 * @returns {Promise<{ list: Array<{ id: number, title_id: number, platform: number, publish_status: number, publish_time: string|null, content: string|null, view_count: number, like_count: number, comment_count: number, share_count: number, created_at: string, updated_at: string }> }>}
 */
export function getPublishRecordList(params = {}) {
  return http({
    url: '/v1/records/list',
    method: 'get',
    params,
  })
}

/**
 * 根据发布记录 ID 保存当前关联的图片列表（先清空再按顺序重建）
 * @param {{ publish_id: number, image_ids: number[] }} params
 * @returns {Promise<{ list: Array<{ id: number, publish_id: number, image_id: number, image_type: number, sort_order: number }> }>}
 */
export function createPublishImages(params) {
  return http({
    url: '/v1/publish_images/create_publish_images',
    method: 'post',
    params,
  })
}

// ========== 小红书账号管理 API ==========

/**
 * 获取当前用户的所有小红书账号
 * @returns {Promise<Array<{ id: number, name: string, a1: string, web_session: string, created_at: string }>>}
 */
export function getXhsAccounts() {
  return http({
    url: '/v1/xhs/accounts',
    method: 'get',
  })
}

/**
 * 添加小红书账号
 * @param {{ name: string, a1: string, web_session: string }} data
 * @returns {Promise<{ id: number }>}
 */
export function addXhsAccount(data) {
  return http({
    url: '/v1/xhs/accounts',
    method: 'post',
    data,
  })
}

/**
 * 修改小红书账号
 * @param {{ account_id: number, name?: string, a1?: string, web_session?: string }} data
 * @returns {Promise<{ id: number }>}
 */
export function updateXhsAccount(data) {
  return http({
    url: '/v1/xhs/accounts',
    method: 'put',
    data,
  })
}

/**
 * 删除小红书账号
 * @param {number} accountId
 */
export function deleteXhsAccount(accountId) {
  return http({
    url: `/v1/xhs/accounts/${accountId}`,
    method: 'delete',
  })
}
