<template>
  <div class="xiaohongshu-settings-page">
    <div class="page-header">
      <div class="page-header-top">
        <el-button class="back-btn" @click="goBack" :icon="ArrowLeft">返回发布页</el-button>
      </div>
      <h2 class="page-title">小红书 Cookie 与信息</h2>
      <p class="page-desc">管理多个小红书账号的 Cookie，用于后续发布时可选择对应账号</p>
    </div>

    <div class="form-section">
      <h3 class="form-section-title">{{ editingId ? '编辑账号' : '添加账号' }}</h3>
      <el-form ref="formRef" :model="form" label-position="top" class="config-form">
        <el-form-item label="账号备注名" prop="name" required>
          <el-input
            v-model="form.name"
            placeholder="如：个人号、品牌号等，便于区分"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Cookie a1" prop="a1" required>
          <el-input
            v-model="form.a1"
            placeholder="从浏览器 Cookie 中复制 a1 的值"
            maxlength="500"
            show-word-limit
            clearable
          />
          <div class="field-hint">
            打开小红书网页版 → F12 开发者工具 → Application → Cookies → 找到 <code>a1</code> 字段，复制其值
          </div>
        </el-form-item>
        <el-form-item label="Cookie web_session" prop="webSession" required>
          <el-input
            v-model="form.webSession"
            placeholder="从浏览器 Cookie 中复制 web_session 的值"
            maxlength="500"
            show-word-limit
            clearable
          />
          <div class="field-hint">
            同上，找到 <code>web_session</code> 字段，复制其值
          </div>
        </el-form-item>
        <el-form-item label="备注信息" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="2"
            placeholder="可选：账号说明或备注"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave">{{ editingId ? '保存' : '添加' }}</el-button>
          <el-button v-if="editingId" @click="handleCancelEdit">取消</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="list-section">
      <h3 class="list-section-title">已添加账号（{{ list.length }}）</h3>
      <div v-if="list.length > 0" class="table-wrap">
        <el-table :data="list" stripe class="config-table">
          <el-table-column prop="name" label="备注名" min-width="120" show-overflow-tooltip />
          <el-table-column label="a1" min-width="140">
            <template #default="{ row }">
              <span class="cookie-preview">{{ previewValue(row.a1) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="web_session" min-width="160">
            <template #default="{ row }">
              <span class="cookie-preview">{{ previewValue(row.webSession) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
          <el-table-column label="操作" width="140" align="right" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无账号，请在上方添加" class="empty-wrap" />
    </div>
  </div>
</template>

<script>
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getXhsAccounts, addXhsAccount, updateXhsAccount, deleteXhsAccount } from '@/apis'

export default {
  name: 'XiaohongshuSettings',
  components: { ArrowLeft },
  data() {
    return {
      list: [],
      editingId: null,
      form: {
        name: '',
        a1: '',
        webSession: '',
        remark: '',
      },
    }
  },
  mounted() {
    this.loadList()
  },
  methods: {
    goBack() {
      // 使用 window.location.href 做完整页面跳转
      // 避免 Vue Router 导航时 vnode 为 null 的渲染异常
      window.location.href = '/create'
    },
    async loadList() {
      try {
        const data = await getXhsAccounts()
        // 后端返回 web_session（下划线），映射为前端使用的 webSession（驼峰）
        this.list = (Array.isArray(data) ? data : []).map(item => ({
          ...item,
          webSession: item.web_session || item.webSession || '',
        }))
      } catch {
        this.list = []
      }
    },
    cookiePreview(value) {
      if (!value) return '—'
      const str = value.trim()
      return str.length > 30 ? str.slice(0, 30) + '…' : str
    },
    async handleSave() {
      const name = this.form.name?.trim()
      const a1 = this.form.a1?.trim()
      const webSession = this.form.webSession?.trim()
      if (!name) {
        ElMessage.warning('请填写账号备注名')
        return
      }
      if (!a1) {
        ElMessage.warning('请填写 Cookie a1')
        return
      }
      if (!webSession) {
        ElMessage.warning('请填写 Cookie web_session')
        return
      }
      try {
        if (this.editingId) {
          await updateXhsAccount({
            account_id: this.editingId,
            name: this.form.name,
            a1: this.form.a1,
            web_session: this.form.webSession,
          })
          ElMessage.success('已更新')
        } else {
          await addXhsAccount({
            name: this.form.name,
            a1: this.form.a1,
            web_session: this.form.webSession,
          })
          ElMessage.success('已添加')
        }
        this.resetForm()
        await this.loadList()
      } catch (_err) {
        // 错误已由 request.js 响应拦截器统一处理
      }
    },
    handleCancelEdit() {
      this.editingId = null
      this.resetForm()
    },
    handleEdit(row) {
      this.editingId = row.id
      this.form.name = row.name || ''
      this.form.a1 = row.a1 || ''
      this.form.webSession = row.webSession || ''
      this.form.remark = row.remark || ''
    },
    async handleDelete(row) {
      try {
        await ElMessageBox.confirm(`确定删除「${row.name || '未命名'}」吗？`, '删除确认', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning',
        })
        await deleteXhsAccount(row.id)
        if (this.editingId === row.id) {
          this.handleCancelEdit()
        }
        await this.loadList()
        ElMessage.success('已删除')
      } catch (_err) {
        // 用户取消删除 或 API 报错（已由拦截器处理）
      }
    },
    resetForm() {
      this.editingId = null
      this.form.name = ''
      this.form.a1 = ''
      this.form.webSession = ''
      this.form.remark = ''
    },
  },
}
</script>

<style lang="scss" scoped>
$primary: #FF6B47;
$primary-bg: #fff8f6;
$text: #303133;
$text-secondary: #606266;
$border: #e4e7ed;
$radius: 12px;
$radius-sm: 8px;

.xiaohongshu-settings-page {
  width: 100%;
}

.page-header {
  margin-bottom: 32px;
}

.page-header-top {
  margin-bottom: 16px;
}

.back-btn {
  border-radius: $radius-sm;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: $text;
  margin: 0 0 12px;
}

.page-desc {
  font-size: 14px;
  color: $text-secondary;
  margin: 0;
  line-height: 1.5;
}

.form-section {
  margin-bottom: 40px;
  padding: 24px;
  background: $primary-bg;
  border-radius: $radius;
  border: 1px solid $border;
}

.form-section-title {
  font-size: 16px;
  font-weight: 600;
  color: $text;
  margin: 0 0 20px;
}

.config-form {
  max-width: 640px;
}

.list-section-title {
  font-size: 16px;
  font-weight: 600;
  color: $text;
  margin: 0 0 16px;
}

.table-wrap {
  border-radius: $radius;
  overflow: hidden;
  border: 1px solid $border;
}

.cookie-preview {
  font-size: 13px;
  color: $text-secondary;
  word-break: break-all;
}

.field-hint {
  font-size: 12px;
  color: $text-secondary;
  margin-top: 4px;
  line-height: 1.5;
  code {
    background: #f5f7fa;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 12px;
    color: $primary;
  }
}

:deep(.config-table) {
  --el-table-border-color: #{$border};
  --el-table-header-bg-color: #f5f7fa;
}
:deep(.config-table .el-table__header th) {
  font-weight: 600;
  color: $text;
}
:deep(.config-table .el-button.is-link) {
  font-weight: 500;
}

.empty-wrap {
  padding: 48px 0;
}
.empty-wrap :deep(.el-empty__description) {
  color: $text-secondary;
}
</style>
