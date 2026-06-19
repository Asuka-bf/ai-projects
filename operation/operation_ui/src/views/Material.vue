<template>
  <div class="material-page">
    <div class="page-header">
      <h2 class="page-title">素材库</h2>
      <p class="page-desc">管理图片、文案等素材，便于创作时复用</p>
      <div class="toolbar">
        <el-radio-group v-model="activeTab" class="tab-group">
          <el-radio-button label="image">图片</el-radio-button>
          <el-radio-button label="copy">文案</el-radio-button>
        </el-radio-group>
        <template v-if="activeTab === 'image'">
          <el-upload
            class="upload-inline"
            :show-file-list="false"
            accept="image/jpeg,image/png,image/gif,image/webp"
            :before-upload="beforeUpload"
            :http-request="handleUploadRequest"
          >
            <el-button type="primary" class="upload-btn" :loading="uploading">
              <el-icon><Upload /></el-icon>
              上传素材
            </el-button>
          </el-upload>
        </template>
      </div>
    </div>

    <div v-if="activeTab === 'image'" class="content-wrap">
      <div v-if="imageList.length > 0" class="image-grid">
        <div
          v-for="item in imageList"
          :key="item.id"
          class="image-item"
          @click="handlePreview(item)"
        >
          <div class="image-thumb">
            <img :src="item.url" :alt="item.name" />
          </div>
          <!-- <div class="image-info">
            <span class="image-name">{{ item.name }}</span>
            <span class="image-time">{{ item.createTime }}</span>
            <el-button
              type="danger"
              link
              size="small"
              class="delete-btn"
              @click.stop="handleDelete(item.id)"
            >
              删除
            </el-button>
          </div> -->
        </div>
      </div>
      <el-empty v-else description="暂无图片素材" class="empty-wrap">
        <el-upload
          :show-file-list="false"
          accept="image/jpeg,image/png,image/gif,image/webp"
          :before-upload="beforeUpload"
          :http-request="handleUploadRequest"
        >
          <el-button type="primary" :loading="uploading">上传图片</el-button>
        </el-upload>
      </el-empty>
    </div>

    <el-dialog
      v-model="previewVisible"
      title="预览"
      width="80%"
      max-width="800px"
      align-center
      append-to-body
      @close="previewUrl = ''"
    >
      <img v-if="previewUrl" :src="previewUrl" class="preview-img" alt="预览" />
    </el-dialog>

    <div v-if="activeTab === 'copy'" class="content-wrap">
      <div v-if="copyList.length > 0" class="copy-list">
        <div
          v-for="item in copyList"
          :key="item.id"
          class="copy-item"
        >
          <div v-if="item.title" class="copy-title">{{ item.title }}</div>
          <div class="copy-content">{{ item.content }}</div>
          <div class="copy-meta">
            <span class="copy-time">{{ item.createTime }}</span>
            <el-button type="primary" link size="small" @click="handleUseCopy(item)">使用</el-button>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无文案素材" class="empty-wrap">
        <el-button type="primary" @click="goCreate">去创作</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script>
import { Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCookie } from '@/utils/cookie'
import { getMaterialImages, uploadMaterialImage, deleteMaterialImage, getMaterialCopies } from '@/apis'

export default {
  name: 'Material',
  components: { Upload },
  data() {
    return {
      activeTab: 'image',
      imageList: [],
      copyList: [],
      uploading: false,
      previewVisible: false,
      previewUrl: '',
    }
  },
  watch: {
    activeTab() {
      if (this.activeTab === 'image') this.loadImages()
      else this.loadCopy()
    },
  },
  mounted() {
    this.loadImages()
    this.loadCopy()
  },
  methods: {
    async loadImages() {
      try {
        const userId = getCookie('userId')
        const res = await getMaterialImages(userId ? { user_id: userId } : {})
        // 拦截器成功时返回 res.data，即 { list }
        const list = res?.list ?? res?.data?.list ?? []
        this.imageList = (list || []).map((row) => ({
          id: row.id,
          name: this._imageNameFromUrl(row.image_url),
          url: row.image_url,
          createTime: row.created_at || '',
        }))
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || e?.message || '加载图片列表失败')
        this.imageList = []
      }
    },
    _imageNameFromUrl(url) {
      if (!url) return '素材图片'
      try {
        const name = url.split('/').pop() || url
        return name.length > 20 ? name.slice(0, 20) + '…' : name
      } catch {
        return '素材图片'
      }
    },
    beforeUpload(file) {
      const isImage = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isImage) {
        ElMessage.error('仅支持 jpg/png/gif/webp')
        return false
      }
      if (!isLt10M) {
        ElMessage.error('图片大小不超过 10MB')
        return false
      }
      return true
    },
    async handleUploadRequest({ file }) {
      this.uploading = true
      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await uploadMaterialImage(formData)
        if (res?.image_url) {
          ElMessage.success('上传成功')
          await this.loadImages()
        } else {
          ElMessage.error('上传失败')
        }
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || e?.message || '上传失败')
      } finally {
        this.uploading = false
      }
    },
    handlePreview(item) {
      this.previewUrl = item.url
      this.previewVisible = true
    },
    handleDelete(imageId) {
      ElMessageBox.confirm('确定删除该图片吗？', '删除确认', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await deleteMaterialImage(imageId)
            ElMessage.success('已删除')
            await this.loadImages()
          } catch (e) {
            ElMessage.error(e?.response?.data?.message || e?.message || '删除失败')
          }
        })
        .catch(() => {})
    },
    async loadCopy() {
      try {
        const res = await getMaterialCopies()
        const list = res?.list ?? res?.data?.list ?? []
        this.copyList = (list || []).map((row) => ({
          id: row.id,
          title: row.title || '',
          content: row.content || '',
          createTime: row.created_at || '',
        }))
      } catch (e) {
        ElMessage.error(e?.response?.data?.message || e?.message || '加载文案列表失败')
        this.copyList = []
      }
    },
    handleUseCopy(item) {
      sessionStorage.setItem('createCopy', item.content || '')
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

.material-page {
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
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.tab-group {
  :deep(.el-radio-button__inner) {
    border-radius: $radius-sm;
  }
  :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background: $primary;
    border-color: $primary;
    box-shadow: -1px 0 0 0 $primary;
  }
}

.upload-inline {
  display: inline-block;
}
.upload-btn {
  border-radius: $radius-sm;
}

.content-wrap {
  min-height: 400px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 24px;
}

.image-item {
  border-radius: $radius;
  overflow: hidden;
  border: 1px solid $border;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: $primary-light;
    box-shadow: 0 8px 24px rgba(255, 107, 71, 0.12);
    transform: translateY(-2px);
  }
}

.image-thumb {
  aspect-ratio: 4/3;
  overflow: hidden;
  background: #f5f7fa;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
}

.image-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.delete-btn {
  align-self: flex-start;
  padding: 0;
  color: #f56c6c;
}

.image-name {
  font-size: 14px;
  color: $text;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-time {
  font-size: 12px;
  color: $text-secondary;
}

.copy-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.copy-item {
  padding: 20px 24px;
  border-radius: $radius;
  border: 1px solid $border;
  background: #fdfdfd;
  transition: all 0.3s ease;

  &:hover {
    border-color: $primary-light;
    box-shadow: 0 4px 16px rgba(255, 107, 71, 0.08);
  }
}

.copy-title {
  font-size: 13px;
  color: $primary;
  font-weight: 600;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-content {
  font-size: 15px;
  color: $text;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.copy-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-time {
  font-size: 13px;
  color: $text-secondary;
}
:deep(.copy-meta .el-button.is-link) {
  color: $primary;
  font-weight: 600;
}

.preview-img {
  width: 100%;
  display: block;
  border-radius: $radius-sm;
}

.empty-wrap {
  padding: 64px 0;
}
.empty-wrap :deep(.el-empty__description) {
  color: $text-secondary;
}
</style>
