<template>
  <div class="history-page">
    <div class="page-header">
      <h2 class="page-title">历史记录</h2>
      <p class="page-desc">查看自己在各平台的发布记录与状态</p>
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文案关键词"
          clearable
          class="search-input"
          @input="onSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterStatus" placeholder="状态" clearable class="status-select" @change="onFilter">
          <el-option label="已发布" value="published" />
        </el-select>
      </div>
    </div>
    <div v-if="list.length > 0" class="table-wrap">
      <el-table :data="pagedList" stripe class="history-table" v-loading="loading">
        <el-table-column prop="contentBrief" label="文案摘要" min-width="260" show-overflow-tooltip />
        <el-table-column prop="platformLabel" label="平台" width="100" align="center" />
        <el-table-column prop="statusLabel" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.statusTagType" size="small">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="publishTime" label="发布时间" width="190" />
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link size="small" @click="handleUse(row)">复用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="onSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </div>
    <el-empty v-else :description="loading ? '加载中...' : '暂无已发布历史记录'" class="empty-wrap">
      <el-button v-if="!loading" type="primary" @click="goCreate">去创作</el-button>
    </el-empty>

    <!-- 查看详情弹窗：文案 + 图片 -->
    <el-dialog
      v-model="detailVisible"
      title="内容详情"
      width="640px"
      class="detail-dialog"
      destroy-on-close
      @close="detailData = null"
    >
      <div v-if="detailLoading" class="detail-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <template v-else-if="detailData">
        <div class="detail-title">{{ detailData.title || '—' }}</div>
        <div v-if="detailData.content" class="detail-content">{{ detailData.content }}</div>
        <div v-else class="detail-content empty">暂无文案</div>
        <div v-if="detailData.image_urls && detailData.image_urls.length" class="detail-images">
          <div class="detail-images-label">图片</div>
          <div class="detail-images-list">
            <a
              v-for="(url, idx) in detailData.image_urls"
              :key="idx"
              :href="url"
              target="_blank"
              rel="noopener noreferrer"
              class="detail-image-item"
            >
              <img :src="url" :alt="'图片' + (idx + 1)" />
            </a>
          </div>
        </div>
        <div v-else class="detail-images">
          <div class="detail-images-label">图片</div>
          <div class="detail-content empty">暂无图片</div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Search, Loading } from '@element-plus/icons-vue'
import { getPublishRecordList, getPublishImages } from '@/apis'

export default {
  name: 'History',
  components: { Search, Loading },
  data() {
    return {
      searchKeyword: '',
      filterStatus: 'published',
      currentPage: 1,
      pageSize: 10,
      total: 0,
      list: [],
      loading: false,
      detailVisible: false,
      detailLoading: false,
      detailData: null,
    }
  },
  computed: {
    pagedList() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.list.slice(start, end)
    },
  },
  mounted() {
    this.fetchList()
  },
  methods: {
    async fetchList() {
      this.loading = true
      try {
        const data = await getPublishRecordList({})
        const rawList = data?.list || []
        const keyword = (this.searchKeyword || '').trim()

        const platformMap = {
          1: '小红书',
          2: '抖音',
          3: '快手',
          4: '微信公众号',
        }
        const statusMap = {
          0: '待发布',
          1: '发布中',
          2: '发布成功',
          3: '发布失败',
          4: '已删除',
        }
        const statusTagTypeMap = {
          0: 'info',
          1: 'warning',
          2: 'success',
          3: 'danger',
          4: 'info',
        }

        const mapped = rawList.map((item) => {
          const content = (item.content || '').trim()
          const status = Number(item.publish_status)
          const publishTime = item.publish_time || item.created_at || '—'
          const contentBrief =
            content.length > 60 ? `${content.slice(0, 60)}...` : (content || '—')
          return {
            ...item,
            publishTime,
            content,
            contentBrief,
            platformLabel: platformMap[item.platform] || '—',
            statusLabel: statusMap[status] || '未知',
            statusTagType: statusTagTypeMap[status] || 'info',
          }
        })

        const filtered = keyword
          ? mapped.filter((item) =>
              item.content?.toLowerCase().includes(keyword.toLowerCase())
            )
          : mapped

        // 后端按 ID 倒序，这里再保证一次
        this.list = filtered.sort((a, b) => (b.id || 0) - (a.id || 0))
        this.total = this.list.length
        if (this.currentPage > 1 && this.pagedList.length === 0) {
          this.currentPage = 1
        }
      } catch (e) {
        this.list = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    onSearch() {
      this.currentPage = 1
      this.fetchList()
    },
    onFilter() {
      this.currentPage = 1
      this.fetchList()
    },
    onPageChange(page) {
      this.currentPage = page
      this.fetchList()
    },
    onSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
      this.fetchList()
    },
    async handleView(row) {
      const publishId = row.id
      if (!publishId) {
        this.$message.warning('无法获取发布记录 ID')
        return
      }
      this.detailVisible = true
      this.detailLoading = true
      this.detailData = null
      try {
          const data = await getPublishImages({ publish_id: publishId })
          const list = data?.list || []
          const imageUrls = list
            .map((item) => item?.image_url)
            .filter((url) => !!url)

        this.detailData = {
          title: row.contentBrief || `发布记录 #${publishId}`,
          content: row.content || '',
          image_urls: imageUrls,
        }
      } catch (e) {
        this.$message.error(e?.message || '加载详情失败')
        this.detailVisible = false
      } finally {
        this.detailLoading = false
      }
    },
    handleUse(row) {
      const content = (row.content || '').trim()
      if (!content) {
        this.$message.warning('该记录暂无可复用的文案')
        return
      }
      try {
        window.sessionStorage.setItem('createCopy', content)
      } catch (e) {
        // ignore
      }
      this.$router.push('/create')
    },
    goCreate() {
      this.$router.push('/create')
    },
  },
}
</script>

<style lang="scss" scoped>
$primary: #FF6B47;
$primary-light: #FF8A65;
$primary-bg: #fff8f6;
$text: #303133;
$text-secondary: #606266;
$border: #e4e7ed;
$radius: 12px;
$radius-sm: 8px;

.history-page {
  width: 100%;
}

.page-header {
  margin-bottom: 32px;
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
  margin: 0 0 24px;
  line-height: 1.5;
}

.toolbar {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.search-input {
  width: 280px;
  :deep(.el-input__wrapper) {
    border-radius: $radius-sm;
    transition: border-color 0.2s ease;
  }
}

.status-select {
  width: 140px;
  :deep(.el-input__wrapper) {
    border-radius: $radius-sm;
  }
}

.table-wrap {
  border-radius: $radius;
  overflow: hidden;
  border: 1px solid $border;
}

:deep(.history-table) {
  --el-table-border-color: #{$border};
  --el-table-header-bg-color: #f5f7fa;
}
:deep(.history-table .el-table__header th) {
  font-weight: 600;
  color: $text;
  height: 54px;
}
:deep(.history-table .el-button.is-link) {
  color: $primary;
}

.pagination-wrap {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  padding: 16px;
}
:deep(.pagination-wrap .el-pagination) {
  --el-pagination-hover-color: #{$primary};
}

.empty-wrap {
  padding: 64px 0;
}
.empty-wrap :deep(.el-empty__description) {
  color: $text-secondary;
}

/* 查看详情弹窗 */
.detail-dialog :deep(.el-dialog__header) {
  padding: 16px 20px;
  border-bottom: 1px solid $border;
}
.detail-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}
.detail-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: $text-secondary;
}
.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: $text;
  margin-bottom: 16px;
  line-height: 1.4;
}
.detail-content {
  font-size: 14px;
  color: $text;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 20px;
  padding: 12px;
  background: $primary-bg;
  border-radius: $radius-sm;
  &.empty {
    color: $text-secondary;
  }
}
.detail-images-label {
  font-size: 14px;
  font-weight: 600;
  color: $text;
  margin-bottom: 12px;
}
.detail-images-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.detail-image-item {
  display: block;
  width: 160px;
  height: 160px;
  border-radius: $radius-sm;
  overflow: hidden;
  border: 1px solid $border;
  flex-shrink: 0;
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
</style>
