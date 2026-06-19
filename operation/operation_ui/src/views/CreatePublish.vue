<template>
  <div class="create-page">
    <div class="create-main">
      <section v-if="!workflowStarted" class="hero-section">
        <div class="hero-card">
          <h1 class="hero-title">从主题开始，完成创作与发布</h1>
          <p class="hero-desc">输入本次运营主题，按步骤完成信息收集、文案生成、配图与发布</p>
          <div class="theme-input-wrap">
            <el-input
              v-model="theme"
              placeholder="输入运营主题，例如：春季新品上市、周末促销活动..."
              size="large"
              clearable
              maxlength="80"
              show-word-limit
              class="theme-input"
              @keyup.enter="startWorkflow"
            >
              <template #prefix>
                <el-icon><Edit /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              size="large"
              class="start-btn"
              :disabled="!themeTrimmed || startLoading"
              :loading="startLoading"
              @click="startWorkflow"
            >
              开始创作
            </el-button>
            <p v-if="startLoading" class="start-loading-hint">正在生成板块与标题，请稍候…</p>

            <div class="theme-divider">
              <span>或</span>
            </div>
            <div class="existing-theme-wrap">
              <p class="existing-theme-desc">检索已有主题，直接进入下一步（无需等待生成）</p>
              <el-select
                v-model="selectedExistingTheme"
                filterable
                remote
                placeholder="输入主题名称检索..."
                :remote-method="remoteThemeSearch"
                :loading="themeSearchLoading"
                clearable
                class="existing-theme-select"
                size="large"
              >
                <el-option
                  v-for="t in themeOptions"
                  :key="t"
                  :label="t"
                  :value="t"
                />
              </el-select>
              <el-button
                type="primary"
                plain
                size="large"
                class="enter-btn"
                :disabled="!selectedExistingTheme || loadThemeLoading"
                :loading="loadThemeLoading"
                @click="enterWorkflowWithExisting"
              >
                进入创作
              </el-button>
            </div>
          </div>
        </div>
      </section>

      <section v-else class="workflow-section">
        <div class="workflow-card">
          <a class="back-to-theme" @click.prevent="goToThemePage">
            <el-icon><House /></el-icon>
            <span>从主题开始，完成创作与发布</span>
          </a>
          <div class="steps-wrap">
            <el-steps :active="currentStep" align-center finish-status="success" class="workflow-steps">
              <el-step title="热词搜索" description="搜索并选定热词" />
              <el-step title="文案编导" description="AI 撰写与编排文案" />
              <el-step title="图片生成" description="选择风格并生成" />
              <el-step title="图文排版" description="编排图文布局" />
              <el-step title="发布" description="一键发布" />
            </el-steps>
          </div>
          <div class="step-content">
            <!-- 1、热词搜索 -->
            <div v-show="currentStep === 0" class="step-panel step-hotwords">
              <div v-if="sectionsFromApi.length" class="sections-block">
                <h4 class="sections-block-title">已生成板块与标题</h4>
                <el-collapse class="sections-collapse">
                  <el-collapse-item
                    v-for="sec in sectionsFromApi"
                    :key="sec.id"
                    :title="sec.name"
                    :name="sec.id"
                  >
                    <ul class="titles-list">
                      <li
                        v-for="t in sec.titles"
                        :key="t.id"
                        class="titles-item"
                        :class="{ selected: isTitleSelected(sec, t) }"
                        @click="selectTitle(sec, t)"
                      >
                        <span class="titles-order">{{ t.sort_order }}</span>
                        <span class="titles-text">{{ t.title }}</span>
                        <span v-if="t.status !== undefined && t.status !== null && t.status !== '' && t.status !== '0'" class="titles-status" :class="'status-' + t.status">
                          {{ titleStatusMap[t.status] || t.status }}
                        </span>
                        <span v-if="t.view_count != null || t.like_count != null" class="titles-stats">
                          <span v-if="t.view_count != null">阅读 {{ t.view_count }}</span>
                          <span v-if="t.view_count != null && t.like_count != null"> · </span>
                          <span v-if="t.like_count != null">点赞 {{ t.like_count }}</span>
                        </span>
                      </li>
                    </ul>
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div class="step-actions">
                <el-button
                  type="primary"
                  class="step-btn-next"
                  :disabled="!stepData.selectedTitle"
                  @click="goStep(1)"
                >
                  下一步：文案编导
                </el-button>
              </div>
            </div>

            <!-- 2、文案编导 -->
            <div v-show="currentStep === 1" class="step-panel step-copy">

              <div class="step-copy-header">
                <div v-if="stepData.selectedTitle" class="selected-title-display">
                  <span class="selected-label">当前选题： </span>
                  <span class="selected-label theme-value">{{ theme }} </span>
                  <span class="selected-section">{{ stepData.selectedTitle.sectionName }}</span>
                  <span class="selected-sep"> — </span>
                  <span class="selected-title-text">{{ stepData.selectedTitle.title }}</span>
                </div>
                <div class="copy-header-actions">
                  <el-button
                    type="primary"
                    plain
                    class="gen-btn"
                    :loading="copyGenerating"
                    :disabled="copyGenerating"
                    @click="generateCopy"
                  >
                    <el-icon><Document /></el-icon>
                    生成文案
                  </el-button>
                  <el-button
                    type="primary"
                    plain
                    class="gen-btn"
                    :loading="copyGenerating"
                    :disabled="copyGenerating"
                    @click="refreshCopy"
                  >
                    <el-icon><Refresh /></el-icon>
                    重置文案
                  </el-button>
                </div>
              </div>
             
              <p v-if="copyGenerating" class="copy-loading-hint">正在生成文案，预计需 10–30 秒，请耐心等待…</p>
              <el-input
                v-model="stepData.copyContent"
                type="textarea"
                :rows="18"
                placeholder="生成后将在此展示文案，可自行编辑"
                class="step-textarea"
              />
              <div class="step-actions">
                <el-button class="step-btn-prev" @click="goStep(0)">上一步</el-button>
                <el-button type="primary" class="step-btn-next" @click="goToImageStep">下一步：图片生成</el-button>
              </div>
            </div>

            <!-- 3、图片生成 -->
            <div v-show="currentStep === 2" class="step-panel step-image">
              <div class="style-options">
                <div class="style-options-row">
                  <span class="style-label">选择风格</span>
                  <div class="style-chips">
                    <div
                      v-for="s in styleList"
                      :key="s.id"
                      class="style-chip"
                      :class="{ active: stepData.styleId === s.id }"
                      @click="stepData.styleId = s.id"
                    >
                      <el-icon><Brush /></el-icon>
                      <span>{{ s.name || '未命名风格' }}</span>
                    </div>
                  </div>
                  <div class="gen-btn-wrap gen-btn-wrap-right">
                    <el-button
                      type="primary"
                      plain
                      class="gen-btn"
                      :loading="imageGenerating"
                      @click="generateImage"
                    >
                      <el-icon><Picture /></el-icon>
                      生成封面
                    </el-button>
                    <input
                      ref="coverFileInput"
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      style="display:none"
                      @change="onCoverFileChange"
                    />
                    <el-button
                      plain
                      class="gen-btn"
                      :loading="coverUploading"
                      @click="triggerCoverUpload"
                    >
                      <el-icon><Upload /></el-icon>
                      上传图片
                    </el-button>
                    <el-button
                      plain
                      class="gen-btn material-btn"
                      @click="openMaterialModal"
                    >
                      <el-icon><FolderOpened /></el-icon>
                    素材库
                    </el-button>
                  </div>
                </div>
                <p v-if="styleList.length === 0 && !styleLoading" class="style-empty-hint">暂无风格数据，请先在后台维护 t_style 表</p>
                <p v-if="styleLoading" class="style-loading-hint">加载风格中…</p>
              </div>
              <!-- 模型选择已隐藏，默认使用第一个可用模型 -->
              <!-- <div v-show="true" class="style-options">
                <span class="style-label">选择模型</span>
                <el-select
                  v-model="stepData.modelId"
                  placeholder="请选择图像生成模型"
                  clearable
                  class="model-select"
                  :loading="modelLoading"
                >
                  <el-option
                    v-for="m in modelList"
                    :key="m.id"
                    :label="m.name + (m.version ? ' ' + m.version : '')"
                    :value="m.id"
                  >
                    <span>{{ m.name }}</span>
                    <span v-if="m.version" class="model-version"> {{ m.version }}</span>
                  </el-option>
                </el-select>
                <p v-if="modelList.length === 0 && !modelLoading" class="style-empty-hint">暂无可用图像模型，请先在后台维护 t_models 表（type=image, status=1）</p>
              </div> -->
              <div v-if="(stepData.generatedCoverImages || []).length" class="image-preview-list">
                <div
                  v-for="(url, idx) in stepData.generatedCoverImages"
                  :key="idx"
                  class="image-preview-item"
                  :class="{ selected: (stepData.selectedCoverImages || []).includes(url) }"
                  :style="coverPreviewSizes[idx] ? { width: coverPreviewSizes[idx].w + 'px', height: coverPreviewSizes[idx].h + 'px' } : {}"
                  @click="toggleCoverSelection(url)"
                >
                  <img
                    :src="url"
                    alt="封面预览"
                    :style="coverPreviewSizes[idx] ? { width: coverPreviewSizes[idx].naturalW + 'px', height: coverPreviewSizes[idx].naturalH + 'px', transform: 'scale(0.32)', transformOrigin: 'top left' } : {}"
                    @load="onCoverPreviewLoad(idx, $event)"
                  />
                  <span v-if="(stepData.selectedCoverImages || []).includes(url)" class="image-preview-tag">已选择</span>
                </div>
              </div>
              <div v-else class="image-placeholder">
                <el-icon><Picture /></el-icon>
                <span>生成后将在此展示</span>
              </div>
              <!-- 素材库选择弹窗 -->
              <el-dialog
                v-model="materialModalVisible"
                title="素材库"
                width="95%"
                class="material-modal-dialog"
                :close-on-click-modal="true"
                @open="loadMaterialImages"
                @close="materialImagesList = []"
              >
                <div v-if="materialImagesLoading" class="material-modal-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>加载素材中…</span>
                </div>
                <el-empty v-else-if="!materialImagesList.length" description="暂无素材图片，请先在素材库页面上传" />
                <div v-else class="material-modal-grid">
                  <div
                    v-for="item in materialImagesList"
                    :key="item.id"
                    class="material-modal-item"
                    :class="{ selected: (stepData.selectedCoverImages || []).includes(item.image_url) }"
                    @click="selectMaterialImage(item)"
                  >
                    <img :src="item.image_url" :alt="'素材' + item.id" />
                  </div>
                </div>
                <template #footer>
                  <el-button @click="materialModalVisible = false">关闭</el-button>
                </template>
              </el-dialog>
              <div class="step-actions">
                <el-button class="step-btn-prev" @click="goStep(1)">上一步</el-button>
                <el-button type="primary" class="step-btn-next" @click="goToLayoutStep">下一步：图文排版</el-button>
              </div>
            </div>

            <!-- 4、图文排版 -->
            <div v-show="currentStep === 3" class="step-panel step-layout">
              <div class="layout-two-column">
                <!-- 左侧：编辑区 -->
                <div class="layout-editor">
                  <div class="editor-header">
                    <span class="editor-page-title">图片编辑（最多4张） 已添加 {{ layoutImages.length }}/4 张</span>
                  </div>
                  <div class="editor-images">
                    <input
                      ref="layoutFileInput"
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      class="editor-file-input"
                      @change="onLayoutFileChange"
                    />
                    <div
                      v-for="(img, idx) in layoutImages"
                      :key="idx"
                      class="editor-img-thumb"
                    >
                      <img :src="img.url" :alt="'图' + (idx + 1)" />
                      <span class="editor-img-remove" @click.stop="removeLayoutImage(idx)" title="删除">
                        <el-icon><Close /></el-icon>
                      </span>
                    </div>
                    <div
                      v-if="layoutImages.length < 4"
                      class="editor-add-img"
                      @click="addLayoutImage"
                    >
                      <el-icon v-if="!layoutUploading" class="add-icon"><Plus /></el-icon>
                      <el-icon v-else class="add-icon is-loading"><Loading /></el-icon>
                    </div>
                  </div>
                  <div class="editor-field">
                    标题：
                    <el-input
                      v-model="stepData.layoutTitle"
                      placeholder="填写标题会有更多赞哦"
                      maxlength="20"
                      show-word-limit
                      class="editor-title-input"
                    />
                 
                  </div>
                  <div class="editor-field">
                    <el-input
                      v-model="stepData.layoutBody"
                      type="textarea"
                      :rows="15"
                      placeholder="输入正文描述，真诚有价值的分享予人温暖"
                      maxlength="1000"
                      show-word-limit
                      class="editor-body-input"
                    />
                  </div>
                  <div class="editor-actions">
                    <el-button class="btn-draft" @click="saveDraftAndLeave">暂存离开</el-button>
                    <div class="editor-actions-right">
                      <el-button class="step-btn-prev" @click="goStep(2)">上一步</el-button>
                      <el-button type="primary" class="step-btn-next" @click="goStep(4)">下一步：发布</el-button>
                    </div>
                  </div>
                </div>
                <!-- 右侧：手机预览 -->
                <div class="layout-preview-wrap">
                 
                  
                  <div class="phone-mockup">
                 
                    <div class="phone-nav">
                      <el-icon><ArrowLeft /></el-icon>
                      <div class="phone-avatar" />
                      <span class="phone-username">小红薯66681BE2</span>
                      <el-button type="danger" size="small" class="phone-follow">关注</el-button>
                      <el-icon><Share /></el-icon>
                    </div>
                    <div class="phone-content">
                      <div v-if="layoutImages.length" class="phone-note-images">
                        <div class="phone-note-image-item" @click="nextLayoutPreviewImage">
                          <img :src="layoutCurrentImageUrl" :alt="'图' + layoutImageCurrent" />
                          <div v-if="layoutImages.length > 1" class="phone-note-image-indicator">
                            {{ layoutImageCurrent }} / {{ layoutImageTotal }}
                          </div>
                        </div>
                      </div>
                      <div class="phone-note-meta">{{ stepData.layoutTitle }}</div>
                      <div class="phone-note-placeholder" v-if="!stepData.layoutBody">这是一片发单地，分享笔记</div>
                      <div class="phone-note-body" v-else>{{ stepData.layoutBody }}</div>
                    
                    </div>
                
                  </div>
                </div>
              </div>
              
            </div>

            <!-- 5、发布 -->
            <div v-show="currentStep === 4" class="step-panel step-publish">
              <div class="publish-summary">
                <div class="summary-row">
                  <span class="summary-label">主题</span>
                  <span class="summary-value">{{ theme }}</span>
                </div>
                <div class="summary-row">
                  <span class="summary-label">文案</span>
                  <span class="summary-value summary-copy">{{ stepData.copyContent || '—' }}</span>
                </div>
                <div class="summary-row" v-if="layoutImages.length">
                  <span class="summary-label">配图</span>
                  <div class="summary-images">
                    <img
                      v-for="(img, idx) in layoutImages"
                      :key="idx"
                      :src="img.url"
                      :alt="'配图' + (idx + 1)"
                      class="summary-image"
                    />
                  </div>
                </div>
                <div class="summary-row" v-else-if="stepData.imagePreview">
                  <span class="summary-label">配图</span>
                  <img :src="stepData.imagePreview" alt="配图" class="summary-image" />
                </div>
               
              </div>
              <div class="publish-account-section">
                <div class="account-section-header">
                  <span class="account-section-title">选择发布账号</span>
                  <el-button type="primary" link size="small" @click="goXiaohongshuSettings">
                    管理账号
                  </el-button>
                </div>
                <div v-if="xhsAccountList.length === 0" class="account-empty">
                  <el-empty description="暂无小红书账号" :image-size="60">
                    <el-button type="primary" size="small" @click="goXiaohongshuSettings">
                      去添加账号
                    </el-button>
                  </el-empty>
                </div>
                <div v-else class="account-radio-group">
                  <el-radio-group v-model="selectedAccountId" class="account-radio-list">
                    <div
                      v-for="account in xhsAccountList"
                      :key="account.id"
                      class="account-radio-item"
                      :class="{ 'is-checked': selectedAccountId === account.id }"
                    >
                      <el-radio :label="account.id" class="account-radio">
                        <span class="account-name">{{ account.name }}</span>
                        <span class="account-remark" v-if="account.remark">
                          — {{ account.remark }}
                        </span>
                      </el-radio>
                    </div>
                  </el-radio-group>
                </div>
              </div>
              <div class="publish-actions">
                <el-button class="step-btn-prev" @click="goStep(3)">上一步</el-button>
                <el-button
                  type="primary"
                  class="publish-btn"
                  :loading="publishLoading"
                  @click="doPublish"
                >
                  <el-icon><Upload /></el-icon>
                  发布
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import {
  Edit,
  Collection,
  Document,
  Picture,
  Upload,
  Camera,
  Brush,
  House,
  Search,
  MagicStick,
  Plus,
  Loading,
  ArrowDown,
  ChatDotRound,
  User,
  Sunny,
  ArrowLeft,
  Share,
  Star,
  FolderOpened,
  Close,
  Refresh,
} from '@element-plus/icons-vue'
import { createStart, createThemes, createLoad, getTitleDetail, createCopy, saveCopy, getStyles, generateCover, uploadTitleImage, updateTitle, publishXiaohongshu, getMaterialImages } from '@/apis'
import { getXhsAccounts } from '@/apis'
import axios from 'axios'

export default {
  name: 'CreatePublish',
  components: {
    Edit,
    Collection,
    Document,
    Picture,
    Upload,
    Camera,
    Brush,
    House,
    Search,
    MagicStick,
    Plus,
    Loading,
    ArrowDown,
    ChatDotRound,
    User,
    Sunny,
    ArrowLeft,
    Share,
    Star,
    FolderOpened,
    Close,
    Refresh,
  },
  data() {
    return {
      theme: '',
      workflowStarted: false,
      currentStep: 0,
      startLoading: false,
      sectionsFromApi: [],
      themeOptions: [],
      themeSearchLoading: false,
      selectedExistingTheme: '',
      loadThemeLoading: false,
      hotwordKeyword: '',
      hotwordSearching: false,
      hotwordCandidates: [],
      stepData: {
        selectedTitle: null,
        selectedHotwords: [],
        infoContent: '',
        copyContent: '',
        styleId: null,
        modelId: null,
        imagePreview: '',
        generatedCoverImages: [], // 本步生成的多张封面，不删除之前的，便于多次生成后挑选
        selectedCoverImages: [], // 用户在图片生成步骤中勾选的图片
        layoutType: 'image-top',
        layoutTitle: '',
        layoutBody: '',
        layoutTags: [
          '#英语学习原来可以这么有趣',
          '#让学习变得更简单',
          '#多元化学习',
          '#让孩子爱上学习',
          '#小学生英语',
        ],
        // 图文排版使用的图片列表：[{ id, url }]
        layoutImages: [],
        initialLayoutTitle: '',
        initialLayoutBody: '',
        initialLayoutImages: [],
        previewTab: 'note',
      },
      styleList: [],
      modelList: [],
      styleLoading: false,
      modelLoading: false,
      copyGenerating: false,
      imageGenerating: false,
      coverUploading: false,
      layoutUploading: false,
      publishLoading: false,
      xhsAccountList: [],
      selectedAccountId: null,
      screenshotPreviewUrl: '',
      coverPreviewSizes: {}, // 封面缩略图 20% 尺寸 { [idx]: { w, h, naturalW, naturalH } }
      coverImageMetaMap: {}, // 封面/素材图的元信息（目前只需记录 image_id），按 URL 维度存储
      layoutPreviewIndex: 0, // 手机预览当前图片下标
      materialModalVisible: false,
      materialImagesList: [],
      materialImagesLoading: false,
      layoutOptions: [
        { value: 'image-top', label: '图在上', icon: Picture },
        { value: 'image-bottom', label: '图在下', icon: Picture },
        { value: 'image-left', label: '图左文右', icon: Document },
      ],
      // t_titles.status: 0=未生成（不显示） 1=已生成 2=已发布 3=已废弃
      titleStatusMap: {
        '1': '已生成',
        '2': '已发布',
        '3': '已废弃',
      },
    }
  },
  computed: {
    themeTrimmed() {
      return (this.theme || '').trim().length > 0
    },
    layoutImages() {
      return this.stepData.layoutImages || []
    },
    layoutImageTotal() {
      const list = this.layoutImages
      return list.length || 1
    },
    layoutImageCurrent() {
      const total = this.layoutImageTotal
      if (!total) return 0
      return Math.min(this.layoutPreviewIndex + 1, total)
    },
    layoutCurrentImageUrl() {
      const list = this.layoutImages
      if (!list.length) return this.stepData.imagePreview || ''
      const idx = Math.min(this.layoutPreviewIndex, list.length - 1)
      return (list[idx] || {}).url || this.stepData.imagePreview || ''
    },
  },
  watch: {
  },
  mounted() {
    // 优先恢复离开时保存的工作流状态（从设置页返回）
    const restored = this.restoreWorkflowState()
    if (restored) {
      window.addEventListener('reset-create-workflow', this.handleResetWorkflow)
      return
    }
    const { theme } = this.$route.query
    if (theme) this.theme = theme
    // 检查是否有从其他页面带入的文案内容
    const copyContent = sessionStorage.getItem('createCopy')
    if (copyContent && copyContent.trim()) {
      sessionStorage.removeItem('createCopy')
      this.workflowStarted = true
      this.currentStep = 1
      this.stepData.copyContent = copyContent
    }
    // 监听重置创作流程事件
    window.addEventListener('reset-create-workflow', this.handleResetWorkflow)
  },
  beforeUnmount() {
    window.removeEventListener('reset-create-workflow', this.handleResetWorkflow)
  },
  methods: {
    handleResetWorkflow() {
      // 重置创作流程到初始状态
      this.workflowStarted = false
      this.currentStep = 0
      this.theme = ''
      this.selectedExistingTheme = ''
      this.themeOptions = []
      this.sectionsFromApi = []
      this.stepData.selectedTitle = null
      this.stepData.selectedHotwords = []
      this.stepData.copyContent = ''
      this.stepData.imagePreview = ''
      this.stepData.generatedCoverImages = []
      this.stepData.selectedCoverImages = []
      this.stepData.layoutImages = []
      this.coverPreviewSizes = {}
      this.coverImageMetaMap = {}
      this.styleOptions = []
      this.modelOptions = []
    },
    goToThemePage() {
      this.workflowStarted = false
      this.sectionsFromApi = []
      this.stepData.selectedTitle = null
      this.selectedExistingTheme = ''
      this.themeOptions = []
    },
    remoteThemeSearch(query) {
      this.themeSearchLoading = true
      const keyword = (query || '').trim()
      createThemes(keyword ? { keyword } : {})
        .then((data) => {
          this.themeOptions = data?.themes || []
        })
        .catch(() => {
          this.themeOptions = []
        })
        .finally(() => {
          this.themeSearchLoading = false
        })
    },
    enterWorkflowWithExisting() {
      if (!this.selectedExistingTheme) return
      this.loadThemeLoading = true
      createLoad({ theme: this.selectedExistingTheme })
        .then((data) => {
          this.theme = this.selectedExistingTheme
          this.sectionsFromApi = data?.sections || []
          this.stepData.selectedTitle = null
          this.workflowStarted = true
          this.currentStep = 0
          this.$message.success('已加载该主题，可直接进行热词搜索等后续步骤')
        })
        .catch(() => {
          this.$message.error('加载失败，请稍后重试')
        })
        .finally(() => {
          this.loadThemeLoading = false
        })
    },
    startWorkflow() {
      if (!this.themeTrimmed) return
      this.startLoading = true
      this.sectionsFromApi = []
      this.stepData.selectedTitle = null
      createStart({ theme: this.theme.trim() })
        .then((data) => {
          this.sectionsFromApi = data?.sections || []
          this.workflowStarted = true
          this.currentStep = 0
          if (this.sectionsFromApi.length) {
            this.$message.success('已生成板块与标题')
          }
        })
        .catch(() => {
          this.$message.error('创建失败，请稍后重试')
        })
        .finally(() => {
          this.startLoading = false
        })
    },
    isTitleSelected(sec, t) {
      const sel = this.stepData.selectedTitle
      return sel && sel.id === t.id && sel.sectionId === sec.id
    },
    selectTitle(sec, t) {
      this.stepData.selectedTitle = {
        id: t.id,
        title: t.title,
        sort_order: t.sort_order,
        sectionId: sec.id,
        sectionName: sec.name,
        content: t.content,
        status: t.status,
        view_count: t.view_count,
        like_count: t.like_count,
      }
      // 若该标题已有文章内容，预填到文案编导
      if (t.content && (t.content + '').trim()) {
        this.stepData.copyContent = (t.content + '').trim()
      }
      // 选中标题后自动进入下一环节（文案编导），并显示当前选题
      this.$nextTick(() => {
        this.goStep(1)
      })
    },
    goStep(step) {
      const fromStep = this.currentStep
      if (step === 1 && fromStep === 0 && !this.stepData.selectedTitle) {
        this.$message.warning('请先选择一个标题')
        return
      }
      // 从文案编导退回上一步时，清空当前页保存的文案与图片，下次进入可能选不同标题无旧数据
      if (fromStep === 1 && step === 0) {
        this.stepData.copyContent = ''
        this.stepData.imagePreview = ''
        this.stepData.generatedCoverImages = []
        this.stepData.selectedCoverImages = []
        this.coverPreviewSizes = {}
      }
      this.currentStep = step
      if (step === 3) {
        this.layoutPreviewIndex = 0
        this.stepData.layoutTitle = this.stepData.selectedTitle?.title || ''
        this.stepData.layoutBody = this.stepData.copyContent || ''
        const selectedList = (this.stepData.selectedCoverImages || []).filter(Boolean)
        if (selectedList.length) {
          this.stepData.layoutImages = selectedList.slice(0, 4).map((url) => {
            const meta = this.coverImageMetaMap[url] || {}
            return {
              url,
              id: meta.id,
            }
          })
        } else if (this.stepData.imagePreview) {
          const previewMeta = this.coverImageMetaMap[this.stepData.imagePreview] || {}
          this.stepData.layoutImages = [{
            url: this.stepData.imagePreview,
            id: previewMeta.id,
          }]
        } else {
          this.stepData.layoutImages = []
        }
        this.stepData.initialLayoutTitle = this.stepData.layoutTitle
        this.stepData.initialLayoutBody = this.stepData.layoutBody
        this.stepData.initialLayoutImages = (this.stepData.layoutImages || []).map((img) => img?.url).filter(Boolean)
        this.stepData.previewTab = 'note'
      }
      // 进入发布步骤时，从后端加载账号列表
      if (step === 4) {
        this.loadXhsAccounts()
      }
      // 只在从步骤 1 进入步骤 2 时，加载风格数据，并根据标题详情自动预填封面
      // 从步骤 3 返回步骤 2 时，不再重置已生成/已选择的图片
      if (step === 2 && fromStep === 1 && this.stepData.selectedTitle?.id) {
        // 加载风格
        this.fetchStyles()
        getTitleDetail(this.stepData.selectedTitle.id)
          .then((detail) => {
            const hasImages = (this.stepData.generatedCoverImages || []).length > 0
            if (detail?.cover_url && !hasImages) {
              this.stepData.imagePreview = detail.cover_url
              this.stepData.generatedCoverImages = [detail.cover_url]
              this.stepData.selectedCoverImages = [detail.cover_url]
            } else if (!hasImages) {
              this.stepData.imagePreview = ''
              this.stepData.generatedCoverImages = []
              this.stepData.selectedCoverImages = []
            }
            this.coverPreviewSizes = {}
          })
          .catch(() => {
            if (!(this.stepData.generatedCoverImages || []).length) {
              this.stepData.imagePreview = ''
              this.stepData.generatedCoverImages = []
              this.stepData.selectedCoverImages = []
              this.coverPreviewSizes = {}
            }
          })
      }
    },
    async goToLayoutStep() {
      // 直接进入图文排版步骤，不操作发布记录
      this.goStep(3)
    },
    searchHotwords() {
      const kw = (this.hotwordKeyword || '').trim()
      if (!kw) {
        this.$message.info('请输入关键词')
        return
      }
      this.hotwordSearching = true
      // 示例：模拟热词推荐，后续可接真实搜索 API
      setTimeout(() => {
        this.hotwordCandidates = [
          kw + '促销',
          kw + '活动',
          '热门' + kw,
          kw + '推荐',
          '精选' + kw,
        ].filter((w) => !this.stepData.selectedHotwords.includes(w))
        this.hotwordSearching = false
        this.$message.success('已更新推荐热词')
      }, 600)
    },
    addHotword(w) {
      if (!this.stepData.selectedHotwords.includes(w)) {
        this.stepData.selectedHotwords.push(w)
      }
    },
    removeHotword(w) {
      this.stepData.selectedHotwords = this.stepData.selectedHotwords.filter((x) => x !== w)
    },
    async generateCopy() {
      const sel = this.stepData.selectedTitle
      const titleText = sel?.title || ''
      if (!titleText) {
        this.$message.warning('请先在「热词搜索」步骤选择一个标题')
        return
      }
      const titleId = sel?.id
      this.copyGenerating = true

      try {
        const data = await createCopy({
          title_text: titleText,
          theme: this.theme || undefined,
          title_id: titleId ?? undefined,
        })

        // 兼容多种返回格式：{ content: '...' } 或 '...'
        let content = ''
        if (typeof data === 'string') {
          content = data.trim()
        } else if (data && typeof data === 'object') {
          content = (data.content ?? data.data ?? '').trim()
        }
        content = content || '（未生成内容）'

        this.stepData.copyContent = content
        if (sel) {
          sel.content = content
          sel.status = '3'
          this.updateSectionTitleContent(sel.id, content, '3')
        }
        this.$message.success('文案已生成并保存')
      } catch (e) {
        this.$message.error(e?.message || '文案生成失败，请稍后重试')
      } finally {
        this.copyGenerating = false
      }
    },
    async refreshCopy() {
      const sel = this.stepData.selectedTitle
      const titleId = sel?.id
      if (!titleId) {
        this.$message.warning('请先在「热词搜索」步骤选择一个标题')
        return
      }
      this.copyGenerating = true
      try {
        const detail = await getTitleDetail(titleId)
        const existingContent = (detail?.content ?? '').trim()
        if (existingContent) {
          this.stepData.copyContent = existingContent
          if (sel) {
            sel.content = existingContent
            sel.status = detail?.status ?? sel.status
            this.updateSectionTitleContent(sel.id, existingContent, sel.status)
          }
          this.$message.success('已刷新最新文案')
        } else {
          this.stepData.copyContent = ''
          if (sel) {
            sel.content = ''
            this.updateSectionTitleContent(sel.id, '', detail?.status ?? sel.status)
          }
          this.$message.info('当前暂无文案内容')
        }
      } catch (e) {
        this.$message.error(e?.message || '重置文案失败，请稍后重试')
      } finally {
        this.copyGenerating = false
      }
    },
    // 将 sectionsFromApi 中对应标题的 content、status 更新，便于返回步骤一时展示正确状态
    updateSectionTitleContent(titleId, content, status) {
      for (const sec of this.sectionsFromApi) {
        const t = (sec.titles || []).find((x) => x.id === titleId)
        if (t) {
          t.content = content
          t.status = status
          break
        }
      }
    },
    fetchStyles() {
      this.styleLoading = true
      getStyles()
        .then((data) => {
          this.styleList = data?.styles || []
          if (this.styleList.length && this.stepData.styleId == null) {
            this.stepData.styleId = this.styleList[0].id
          }
        })
        .catch(() => {
          this.styleList = []
        })
        .finally(() => {
          this.styleLoading = false
        })
    },
    fetchModels() {
      this.modelLoading = true
      getModels({ type: 'image' })
        .then((data) => {
          this.modelList = data?.list || []
          if (this.modelList.length && this.stepData.modelId == null) {
            this.stepData.modelId = this.modelList[0].id
          }
        })
        .catch(() => {
          this.modelList = []
        })
        .finally(() => {
          this.modelLoading = false
        })
    },
    generateImage() {
      const sel = this.stepData.selectedTitle
      if (!sel || !sel.id) {
        this.$message.warning('请先选择一个标题')
        return
      }
      const style = this.styleList.find((s) => s.id === this.stepData.styleId)
      const styleFengge = (style && style.fengge) ? style.fengge.trim() : ''
      const copyContent = (this.stepData.copyContent || '').trim()
      const titleText = (sel.title || '').trim()
      const prompt = styleFengge
        ? (copyContent ? `${styleFengge}\n文案内容：${copyContent}` : `${styleFengge}\n标题：${titleText}`)
        : (copyContent || titleText || '配图')
      this.imageGenerating = true
      generateCover({ title_id: sel.id, prompt })
        .then((data) => {
          if (data && data.image_url) {
            const url = data.image_url
            const imageId = data.image_id != null ? data.image_id : null
            const list = this.stepData.generatedCoverImages || []
            if (!list.includes(url)) list.unshift(url)
            this.stepData.generatedCoverImages = list
            if (imageId != null) {
              this.coverImageMetaMap = {
                ...this.coverImageMetaMap,
                [url]: { id: imageId },
              }
            }
            // 新生成的图片默认加入选中列表
            const selected = this.stepData.selectedCoverImages || []
            if (!selected.includes(url)) selected.push(url)
            this.stepData.selectedCoverImages = selected
            this.stepData.imagePreview = selected[0] || url
            this.$message.success('封面已生成并保存，可继续生成多张后选择')
          } else {
            this.$message.error('未返回图片地址')
          }
        })
        .catch((err) => {
          this.$message.error(err?.message || '封面生成失败')
        })
        .finally(() => {
          this.imageGenerating = false
        })
    },
    onCoverPreviewLoad(idx, e) {
      const el = e.target
      if (!el?.naturalWidth) return
      this.coverPreviewSizes = {
        ...this.coverPreviewSizes,
        [idx]: {
          w: el.naturalWidth * 0.29,
          h: el.naturalHeight * 0.29,
          naturalW: el.naturalWidth,
          naturalH: el.naturalHeight,
        },
      }
    },
    toggleCoverSelection(url) {
      const list = this.stepData.selectedCoverImages || []
      const idx = list.indexOf(url)
      if (idx > -1) {
        list.splice(idx, 1)
      } else {
        list.push(url)
      }
      this.stepData.selectedCoverImages = [...list]
      this.stepData.imagePreview = this.stepData.selectedCoverImages[0] || ''
    },
    openMaterialModal() {
      this.materialModalVisible = true
    },
    loadMaterialImages() {
      this.materialImagesLoading = true
      getMaterialImages()
        .then((data) => {
          this.materialImagesList = data?.list || []
        })
        .catch(() => {
          this.materialImagesList = []
          this.$message.error('加载素材库失败')
        })
        .finally(() => {
          this.materialImagesLoading = false
        })
    },
    selectMaterialImage(item) {
      const url = item?.image_url
      if (!url) return
      if (item?.id != null) {
        this.coverImageMetaMap = {
          ...this.coverImageMetaMap,
          [url]: { id: item.id },
        }
      }
      const list = this.stepData.generatedCoverImages || []
      if (!list.includes(url)) {
        list.unshift(url)
        this.stepData.generatedCoverImages = list
      }
      // 素材库中点击同样作为多选/反选
      const selected = this.stepData.selectedCoverImages || []
      const idx = selected.indexOf(url)
      if (idx > -1) {
        selected.splice(idx, 1)
      } else {
        selected.push(url)
      }
      this.stepData.selectedCoverImages = [...selected]
      this.stepData.imagePreview = this.stepData.selectedCoverImages[0] || ''
      this.materialModalVisible = false
      this.$message.success('已选择该素材作为封面')
    },
    removeLayoutImage(index) {
      const list = [...(this.stepData.layoutImages || [])]
      list.splice(index, 1)
      this.stepData.layoutImages = list
      this.stepData.imagePreview = (list[0] || {}).url || this.stepData.imagePreview
    },
    // ========== 封面图片上传（Step 2） ==========
    triggerCoverUpload() {
      const titleId = this.stepData.selectedTitle?.id
      if (!titleId) {
        this.$message.warning('请先选择标题')
        return
      }
      const input = this.$refs.coverFileInput
      if (input) input.click()
    },
    onCoverFileChange(e) {
      const file = e.target?.files?.[0]
      if (!file) return
      const titleId = this.stepData.selectedTitle?.id
      if (!titleId) {
        this.$message.warning('请先选择标题')
        e.target.value = ''
        return
      }
      this.coverUploading = true
      const formData = new FormData()
      formData.append('file', file)
      uploadTitleImage(formData, titleId)
        .then((data) => {
          const url = data?.image_url
          if (!url) {
            this.$message.error('上传失败，未返回图片地址')
            return
          }
          const imageId = data?.image_id != null ? data.image_id : null
          const list = [...(this.stepData.generatedCoverImages || [])]
          const exists = list.some((i) => i.url === url)
          if (!exists) {
            list.unshift({ url, id: imageId, isUploaded: true })
          }
          this.stepData.generatedCoverImages = list
          // 自动勾选上传的图片
          const selected = [...(this.stepData.selectedCoverImages || [])]
          if (!selected.includes(url)) {
            selected.push(url)
          }
          this.stepData.selectedCoverImages = selected
          this.stepData.imagePreview = url
          this.$message.success('上传成功')
        })
        .catch((err) => {
          console.error('封面上传失败:', err)
          this.$message.error('上传失败：' + (err?.message || '未知错误'))
        })
        .finally(() => {
          this.coverUploading = false
          e.target.value = ''
        })
    },
    addLayoutImage() {
      if ((this.stepData.layoutImages || []).length >= 4) {
        this.$message.warning('最多添加4张图片')
        return
      }
      const titleId = this.stepData.selectedTitle?.id
      if (!titleId) {
        this.$message.warning('请先选择标题')
        return
      }
      const input = this.$refs.layoutFileInput
      if (input) input.click()
    },
    onLayoutFileChange(e) {
      const file = e.target?.files?.[0]
      if (!file) return
      const titleId = this.stepData.selectedTitle?.id
      if (!titleId) {
        this.$message.warning('请先选择标题')
        e.target.value = ''
        return
      }
      this.layoutUploading = true
      const formData = new FormData()
      formData.append('file', file)
      uploadTitleImage(formData, titleId)
        .then((data) => {
          const url = data?.image_url
          if (!url) {
            this.$message.error('上传失败，未返回图片地址')
            return
          }
          const imageId = data?.image_id != null ? data.image_id : null
          const list = [...(this.stepData.layoutImages || [])]
          const exists = list.some((i) => i.url === url)
          if (!exists) {
            list.unshift({
              url,
              id: imageId,
            })
          }
          this.stepData.layoutImages = list.slice(0, 4)
          this.stepData.imagePreview = (this.stepData.layoutImages[0] || {}).url || this.stepData.imagePreview
          this.$message.success('图片上传成功')
        })
        .catch((err) => {
          this.$message.error(err?.message || '图片上传失败')
        })
        .finally(() => {
          this.layoutUploading = false
          e.target.value = ''
        })
    },
    saveDraftAndLeave() {
      this.$message.success('已暂存，可稍后继续编辑')
      this.goStep(2)
    },
    nextLayoutPreviewImage() {
      const total = this.layoutImageTotal
      if (!total) return
      this.layoutPreviewIndex = (this.layoutPreviewIndex + 1) % total
    },
    /** 判断当前 layout 是否相对进入步骤3时的初始值有修改 */
    hasLayoutChanged() {
      const title = (this.stepData.layoutTitle || '').trim()
      const body = (this.stepData.layoutBody || '').trim()
      const urls = (this.stepData.layoutImages || []).map((img) => img?.url).filter(Boolean)
      const initTitle = (this.stepData.initialLayoutTitle || '').trim()
      const initBody = (this.stepData.initialLayoutBody || '').trim()
      const initUrls = this.stepData.initialLayoutImages || []
      if (title !== initTitle || body !== initBody) return true
      if (urls.length !== initUrls.length) return true
      return urls.some((u, i) => (initUrls[i] || '') !== (u || ''))
    },
    async doPublish() {
      const titleId = this.stepData.selectedTitle?.id
      if (!titleId) {
        this.$message.warning('请先选择要发布的标题')
        return
      }

      // ========== 账号选择逻辑 ==========
      // 从后端 API 刷新账号列表
      await this.loadXhsAccounts()

      // 没有账号 → 提示去添加
      if (this.xhsAccountList.length === 0) {
        this.$message.warning('请先添加小红书账号 Cookie')
        return
      }

      // 默认选中第一个账号
      if (!this.selectedAccountId) {
        this.selectedAccountId = this.xhsAccountList[0].id
      }
      // =================================

      this.publishLoading = true
      try {
        // 拦截器已解包为 data 内层：{ results: [...] }
        const data = await publishXiaohongshu({
          title_id: titleId,
          account_ids: [this.selectedAccountId],
        })

        const results = data?.results || []
        if (results.length === 0) {
          this.$message.warning('未返回发布结果')
          return
        }

        const successList = results.filter(r => r.success)
        const failList = results.filter(r => !r.success)

        if (failList.length === 0) {
          // 全部成功
          const urls = successList.map(r => r.note_url).filter(Boolean)
          this.$message.success(
            urls.length
              ? `发布成功！笔记链接：${urls.join('，')}`
              : '发布成功'
          )
        } else if (successList.length === 0) {
          // 全部失败
          this.$message.error(failList.map(r => r.msg).join('；'))
        } else {
          // 部分成功
          this.$message.warning(
            `成功 ${successList.length} 个，失败 ${failList.length} 个：${failList.map(r => r.msg).join('；')}`
          )
        }
      } catch (err) {
        this.$message.error(err?.message || '发布请求失败')
      } finally {
        this.publishLoading = false
      }
    },
    goXiaohongshuSettings() {
      // 跳转前保存当前工作流状态，回来时恢复
      this.saveWorkflowState()
      this.$router.push('/home/xiaohongshu-settings')
    },
    saveWorkflowState() {
      const state = {
        theme: this.theme,
        workflowStarted: this.workflowStarted,
        currentStep: this.currentStep,
        sectionsFromApi: this.sectionsFromApi,
        stepData: {
          selectedTitle: this.stepData.selectedTitle,
          selectedHotwords: this.stepData.selectedHotwords,
          infoContent: this.stepData.infoContent,
          copyContent: this.stepData.copyContent,
          styleId: this.stepData.styleId,
          modelId: this.stepData.modelId,
          imagePreview: this.stepData.imagePreview,
          generatedCoverImages: this.stepData.generatedCoverImages,
          selectedCoverImages: this.stepData.selectedCoverImages,
          layoutType: this.stepData.layoutType,
          layoutTitle: this.stepData.layoutTitle,
          layoutBody: this.stepData.layoutBody,
          layoutTags: this.stepData.layoutTags,
          layoutImages: this.stepData.layoutImages,
        },
        styleList: this.styleList,
        xhsAccountList: this.xhsAccountList,
        selectedAccountId: this.selectedAccountId,
        coverImageMetaMap: this.coverImageMetaMap,
        coverPreviewSizes: this.coverPreviewSizes,
      }
      sessionStorage.setItem('createPublishState', JSON.stringify(state))
    },
    restoreWorkflowState() {
      const saved = sessionStorage.getItem('createPublishState')
      if (!saved) return false
      try {
        const state = JSON.parse(saved)
        this.theme = state.theme || ''
        this.workflowStarted = state.workflowStarted || false
        this.currentStep = state.currentStep || 0
        this.sectionsFromApi = state.sectionsFromApi || []
        this.stepData = { ...this.stepData, ...state.stepData }
        this.styleList = state.styleList || []
        this.xhsAccountList = state.xhsAccountList || []
        this.selectedAccountId = state.selectedAccountId || null
        this.coverImageMetaMap = state.coverImageMetaMap || {}
        this.coverPreviewSizes = state.coverPreviewSizes || {}
        sessionStorage.removeItem('createPublishState')
        return true
      } catch (e) {
        console.error('恢复工作流状态失败:', e)
        sessionStorage.removeItem('createPublishState')
        return false
      }
    },
    async loadXhsAccounts() {
      try {
        const data = await getXhsAccounts()
        // 后端返回 web_session（下划线），映射为前端使用的 webSession（驼峰）
        this.xhsAccountList = (Array.isArray(data) ? data : []).map(item => ({
          ...item,
          webSession: item.web_session || item.webSession || '',
        }))
      } catch {
        this.xhsAccountList = []
      }
    },
    async goToImageStep() {
      const sel = this.stepData.selectedTitle
      // 如果没有选择标题，但有文案内容，仍然允许进入图片生成步骤
      if (!sel || !sel.id) {
        // 检查是否有文案内容
        const copyContent = (this.stepData.copyContent || '').trim()
        if (!copyContent) {
          this.$message.warning('请先在「热词搜索」步骤选择一个标题')
          return
        }
        // 有文案但没选标题，直接进入图片生成步骤
        this.fetchStyles()
        this.goStep(2)
        return
      }
      const titleId = sel.id
      const copyContent = (this.stepData.copyContent || '').trim()
      // 保存文案到数据库
      try {
        await saveCopy(titleId, { content: copyContent })
        // 更新本地状态
        sel.content = copyContent
        sel.status = '3'
        this.updateSectionTitleContent(sel.id, copyContent, '3')
      } catch (e) {
        console.error('保存文案失败:', e)
      }
      // 直接进入图片生成步骤，不创建发布记录
      // 发布记录将在发布时由后端创建
      this.goStep(2)
    },
  },
}
</script>

<style lang="scss" scoped>
$primary: #FF6B47;
$primary-light: #FF8A65;
$primary-soft: #ffebe6;
$primary-bg: #fff8f6;
$text: #303133;
$text-secondary: #606266;
$border: #e4e7ed;
$radius: 12px;
$radius-sm: 8px;

.create-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.create-main {
  width: 100%;
  flex: 1;
}

.hero-section {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 240px);
  padding: 32px 0;
}

.hero-card {
  width: 100%;
  max-width: 600px;
  padding: 0;
}

.hero-title {
  font-size: 32px;
  font-weight: 700;
  color: $text;
  margin: 0 0 16px;
  line-height: 1.4;
  text-align: center;
}

.hero-desc {
  font-size: 16px;
  color: $text-secondary;
  text-align: center;
  margin: 0 0 48px;
  line-height: 1.65;
}

.theme-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.theme-input {
  :deep(.el-input__wrapper) {
    height: 64px;
    padding: 0 24px 0 54px;
    border-radius: $radius;
    border: 1px solid $border;
    font-size: 16px;
    background: #fdfdfd;
    box-shadow: 0 4px 12px rgba(0,0,0,0.02);
  }
  :deep(.el-input__wrapper.is-focus) {
    border-color: rgba($primary, 0.5);
    box-shadow: 0 0 0 3px rgba($primary, 0.08);
    background: #fff;
  }
  :deep(.el-input__prefix) { left: 20px; color: rgba($primary, 0.6); font-size: 20px; }
}

.start-btn {
  height: 60px;
  border-radius: $radius;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(145deg, $primary 0%, $primary-light 100%);
  border: none;
  &:not(.is-disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(255, 107, 71, 0.25);
  }
}

.start-loading-hint,
.copy-loading-hint {
  margin: 12px 0 0;
  font-size: 14px;
  color: $text-secondary;
  text-align: center;
}

.theme-divider {
  margin: 40px 0 24px;
  text-align: center;
  color: $text-secondary;
  font-size: 14px;
  &::before, &::after {
    content: '';
    display: inline-block;
    width: 80px;
    height: 1px;
    background: $border;
    vertical-align: middle;
    margin: 0 16px;
  }
}

.existing-theme-wrap {
  padding: 24px;
  background: $primary-bg;
  border-radius: $radius;
  border: 1px solid rgba($primary, 0.12);
}
.existing-theme-desc {
  margin: 0 0 16px;
  font-size: 14px;
  color: $text-secondary;
}
.existing-theme-select {
  width: 100%;
  max-width: 400px;
  margin-right: 16px;
  margin-bottom: 12px;
  :deep(.el-input__wrapper) {
    border-radius: $radius-sm;
    border: 1px solid $border;
  }
}
.enter-btn {
  border-radius: $radius-sm;
  font-weight: 500;
}

.workflow-section { width: 100%; max-width: 1000px; margin: 0 auto; }

.workflow-card {
  padding: 0;
}

.back-to-theme {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 32px;
  padding: 8px 0;
  font-size: 15px;
  color: $primary;
  text-decoration: none;
  cursor: pointer;
  font-weight: 500;
  &:hover { color: $primary-light; opacity: 0.9; }
}

.steps-wrap { margin-bottom: 48px; padding: 0; }

:deep(.workflow-steps) {
  .el-step__head.is-process { color: $primary; }
  .el-step__title.is-process { color: $primary; font-weight: 600; }
  .el-step__icon.is-text {
    border-color: $primary;
    background: linear-gradient(145deg, $primary 0%, $primary-light 100%);
  }
  .el-step__icon-inner { color: #fff; }
  .el-step__line { background: $border; }
  .el-step__line-inner { background: linear-gradient(90deg, $primary, $primary-light); }
}

.theme-tag {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: $primary-bg;
  color: $primary;
  border-radius: $radius-sm;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 40px;
}

.step-content { min-height: 400px; }

.step-panel-title {
  font-size: 24px;
  font-weight: 600;
  color: $text;
  margin: 0 0 12px;
}

.step-panel-desc {
  font-size: 15px;
  color: $text-secondary;
  margin: 0 0 32px;
  line-height: 1.55;
}

.step-copy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
  .selected-title-display {
    margin-bottom: 0;
  }
  .copy-header-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
    flex-shrink: 0;
  }
  .gen-btn {
    margin-bottom: 0;
    flex-shrink: 0;
  }
}

.selected-title-display {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 24px;
  background: #f5f7fa;
  border-radius: $radius-sm;
  border-left: 4px solid var(--el-color-primary);
  font-size: 14px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  .selected-label {
    color: $text-secondary;
    font-weight: 500;
    flex-shrink: 0;
  }
  .selected-label.theme-value {
    color: red;
  }
  .selected-section {
    color: var(--el-color-primary);
    font-weight: 600;
    flex-shrink: 0;
  }
  .selected-sep {
    color: $text-secondary;
    flex-shrink: 0;
  }
  .selected-title-text {
    color: $text;
    font-weight: 500;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.sections-block {
  margin-bottom: 32px;
}
.sections-block-title {
  font-size: 15px;
  font-weight: 600;
  color: $text;
  margin: 0 0 16px;
}
.sections-collapse {
  border: 1px solid $border;
  border-radius: $radius-sm;
  overflow: hidden;
  :deep(.el-collapse-item__header) {
    padding: 12px 16px;
    font-size: 15px;
    color: $text;
    background: #fdfdfd;
  }
  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
    background: #fff;
  }
  :deep(.el-collapse-item__content) {
    padding: 12px 16px 16px 40px;
  }
}
.titles-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.titles-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 12px;
  margin: 0 -12px;
  font-size: 14px;
  color: $text-secondary;
  line-height: 1.5;
  border-bottom: 1px solid rgba($border, 0.6);
  cursor: pointer;
  border-radius: $radius-sm;
  transition: background 0.2s;
  &:last-child { border-bottom: none; }
  &:hover { background: $primary-bg; }
  &.selected {
    background: $primary-soft;
    color: $primary;
    font-weight: 500;
  }
}
.titles-order {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 4px;
  background: $primary-soft;
  color: $primary;
  font-weight: 500;
  font-size: 12px;
}
.titles-text {
  flex: 1;
  word-break: break-word;
}
.titles-status {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #f0f0f0;
  color: $text-secondary;
  &.status-1 { background: #e3f2fd; color: #1565c0; }  // 已生成 - 蓝色
  &.status-2 { background: #f3e5f5; color: #6a1b9a; }  // 已发布 - 紫色
  &.status-3 { background: #ffebee; color: #c62828; }  // 已废弃 - 红色
}
.titles-stats {
  flex-shrink: 0;
  font-size: 12px;
  color: #909399;
}

.step-textarea {
  margin-bottom: 32px;
  :deep(.el-textarea__inner) {
    border-radius: $radius-sm;
    border: 1px solid $border;
    padding: 16px 20px;
    font-size: 15px;
    line-height: 1.65;
    background: #fdfdfd;
  }
  :deep(.el-textarea__inner:focus) {
    border-color: rgba($primary, 0.45);
    box-shadow: 0 0 0 2px rgba($primary, 0.06);
    background: #fff;
  }
}

.gen-btn {
  border-radius: $radius-sm;
  margin-bottom: 24px;
  height: 40px;
  font-size: 15px;
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba($primary, 0.12);
  }
}
.gen-btn-wrap { margin-bottom: 24px; }
.gen-btn-wrap-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-left: auto;
  flex-shrink: 0;
  align-self: center;
  .gen-btn { margin-bottom: -22px; }
  // 生成封面按钮与页面主色一致
  .gen-btn:deep(.el-button--primary.is-plain) {
    --el-button-border-color: #{$primary};
    --el-button-text-color: #{$primary};
    --el-button-bg-color: #{$primary-bg};
    --el-button-hover-border-color: #{$primary-light};
    --el-button-hover-text-color: #fff;
    --el-button-hover-bg-color: #{$primary};
  }
  .gen-btn:deep(.el-button--primary) {
    --el-button-border-color: #{$primary};
    --el-button-text-color: #fff;
    --el-button-bg-color: #{$primary};
    --el-button-hover-border-color: #{$primary-light};
    --el-button-hover-text-color: #fff;
    --el-button-hover-bg-color: #{$primary-light};
  }
}

.step-hint {
  margin: 16px 0 0;
  font-size: 14px;
  color: $text-secondary;
}
.step-actions {
  display: flex;
  gap: 16px;
  margin-top: -38px;
  padding-top: 32px;
  .el-button { border-radius: $radius-sm; height: 44px; padding: 0 24px; font-size: 15px; }
  .step-btn-prev:hover,
  .step-btn-next:hover { transform: translateY(-1px); }
}

.style-options { margin-bottom: 24px; }
.style-options-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 40px;
}
.style-label {
  font-size: 14px;
  font-weight: 600;
  color: $text;
  flex-shrink: 0;
  letter-spacing: 0.02em;
  line-height: 40px;
  margin: 0;
}
.style-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  min-height: 40px;
  align-content: center;
}

.style-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: $radius;
  border: 1px solid $border;
  background: #fdfdfd;
  font-size: 14px;
  line-height: 1.3;
  color: $text-secondary;
  cursor: pointer;
  transition: all 0.2s ease;
  i { font-size: 16px; color: rgba($primary, 0.5); }
  &:hover {
    border-color: $primary-soft;
    color: $primary;
    background: $primary-bg;
    transform: translateY(-1px);
    i { color: $primary; }
  }
  &.active {
    border-color: rgba($primary, 0.4);
    background: $primary-bg;
    color: $primary;
    font-weight: 500;
    i { color: $primary; }
  }
}

.model-select { width: 100%; max-width: 360px; }
.style-empty-hint, .style-loading-hint { font-size: 13px; color: $text-secondary; margin-top: 8px; }
.model-version { color: $text-secondary; font-size: 12px; }

.image-preview-wrap {
  margin: 24px 0;
  border-radius: $radius;
  overflow: hidden;
  border: 1px solid $border;
  max-width: 100%;
}
.image-preview {
  display: block;
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  background: #f5f7fa;
}

.image-placeholder {
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: $primary-bg;
  border: 1px dashed $primary-soft;
  border-radius: $radius;
  color: $text-secondary;
  font-size: 15px;
  i { font-size: 48px; color: $primary-soft; }
}

.image-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin: 24px 0;
}
.image-preview-item {
  position: relative;
  min-width: 80px;
  min-height: 60px;
  border-radius: $radius;
  overflow: hidden;
  border: 2px solid $border;
  cursor: pointer;
  flex-shrink: 0;
  &:hover { border-color: $primary-soft; }
  &.selected { border-color: var(--el-color-primary); box-shadow: 0 0 0 1px var(--el-color-primary); }
  img { display: block; }
}
.image-preview-tag {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px 8px;
  font-size: 12px;
  text-align: center;
  background: var(--el-color-primary);
  color: #fff;
}

.cover-enlarge-dialog :deep(.el-dialog__body) { padding: 12px; text-align: center; }
.cover-enlarge-img {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

/* 素材库弹窗：等比例缩放图片 */
.material-btn { margin-left: 8px; }
.material-modal-dialog :deep(.el-dialog__body) {
  padding: 16px 10px;
  max-height: 70vh;
  overflow-y: auto;
}
.material-modal-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  .is-loading { font-size: 24px; }
}
.material-modal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}
.material-modal-item {
  aspect-ratio: 3 / 4;
  max-height: 360px;
  border-radius: $radius;
  overflow: hidden;
  border: 2px solid $border;
  background: #f5f7fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s, box-shadow 0.2s;
  &:hover {
    border-color: $primary-soft;
    box-shadow: 0 2px 12px rgba($primary, 0.15);
  }
  &.selected {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 1px var(--el-color-primary);
  }
  img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }
}

/* 热词搜索 */
.hotword-search-wrap { margin-bottom: 28px; }
.hotword-input { max-width: 480px; margin-bottom: 20px; }
.hotword-input :deep(.el-input-group__append) { padding: 0; }
.hotword-input :deep(.el-input-group__append .el-button) { margin: 0; border-radius: 0 $radius-sm $radius-sm 0; }
.hotword-tags, .hotword-candidates { margin-top: 16px; }
.hotword-tags-label, .hotword-candidates-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: $text-secondary;
  margin-bottom: 10px;
}
.hotword-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.hotword-tag { margin-right: 0; }
.hotword-candidate-chips { display: flex; flex-wrap: wrap; gap: 10px; }
.hotword-candidate-chip {
  padding: 8px 16px;
  border-radius: $radius-sm;
  border: 1px solid $border;
  background: #fdfdfd;
  font-size: 14px;
  color: $text-secondary;
  cursor: pointer;
  transition: all 0.2s ease;
  &:hover {
    border-color: $primary-soft;
    color: $primary;
    background: $primary-bg;
  }
}

/* 图文排版 */
.step-layout .step-panel-title,
.step-layout .step-panel-desc { display: none; }
.layout-two-column {
  display: flex;
  gap: 32px;
  align-items: flex-start;
  margin-bottom: 24px;
}
.layout-editor {
  flex: 1;
  min-width: 0;
  max-width: 520px;
  padding: 20px;
  background: #fff;
  border: 1px solid $border;
  border-radius: $radius;
}
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.editor-page-title {
  font-size: 15px;
  font-weight: 500;
  color: $text;
}
.btn-cover-suggest {
  :deep(.el-icon) { margin-right: 4px; }
}
.editor-images {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  position: relative;
}
.editor-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}
.editor-add-img {
  width: 80px;
  height: 80px;
  border: 1px dashed $border;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: $text-secondary;
  transition: all 0.2s;
  .add-icon { font-size: 28px; }
  .add-icon.is-loading {
    animation: spin 0.8s linear infinite;
  }
  &:hover {
    border-color: $primary;
    color: $primary;
    background: $primary-bg;
  }
}
.editor-img-thumb {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: $radius-sm;
  overflow: hidden;
  border: 1px solid $border;
  img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .editor-img-remove {
    position: absolute;
    top: 2px;
    right: 2px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(0,0,0,0.5);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    &:hover { background: rgba(0,0,0,0.75); }
  }
}
.editor-field {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  .editor-title-input { flex: 1; min-width: 0; }
}
.editor-title-input {
  :deep(.el-input__wrapper) { border-radius: $radius-sm; border: 1px solid $border; }
}
.btn-smart-title {
  flex-shrink: 0;
  :deep(.el-icon) { margin-left: 4px; }
}
.editor-body-input {
  width: 100%;
  :deep(.el-textarea__inner) {
    border-radius: $radius-sm;
    border: 1px solid $border;
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.6;
    resize: none;
  }
}
.editor-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.editor-tag {
  padding: 4px 12px;
  background: #f5f7fa;
  border-radius: 999px;
  font-size: 13px;
  color: $text-secondary;
}
.editor-tag-more {
  font-size: 13px;
  color: $text-secondary;
  cursor: pointer;
  &:hover { color: $primary; }
}
.editor-toolbar {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  font-size: 14px;
  color: $text-secondary;
  .toolbar-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    &:hover { color: $primary; }
  }
}
.editor-section {
  margin-bottom: 20px;
  padding-top: 16px;
  border-top: 1px solid $border;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: $text;
  a { font-size: 13px; color: $text-secondary; text-decoration: none; &:hover { color: $primary; } }
}
.activity-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.activity-card {
  flex: 1;
  min-width: 180px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: $radius-sm;
  border: 1px solid $border;
}
.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  &.activity-icon-red { background: #ff4757; color: #fff; }
  &.activity-icon-img { background: #e8e8e8; color: $text-secondary; }
}
.activity-info {
  flex: 1;
  min-width: 0;
  .activity-title { font-size: 14px; font-weight: 500; color: $text; margin-bottom: 6px; }
  .activity-detail { font-size: 12px; color: $text-secondary; margin-left: 8px; text-decoration: none; &:hover { color: $primary; } }
}
.content-setting {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: $text-secondary;
  .create-link { margin-left: auto; color: $primary; text-decoration: none; &:hover { text-decoration: underline; }
  }
}
.editor-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 9px;
  padding-top: 20px;
  .editor-actions-right {
    display: flex;
    gap: 12px;
  }
  .btn-publish { flex: 1; background: #ff4757; border-color: #ff4757; &:hover { background: #ff6b7a; border-color: #ff6b7a; } }
}

.layout-preview-wrap {
  flex-shrink: 0;
  width: 320px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: $radius;
  border: 1px solid $border;
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-bottom: 12px;
  font-size: 14px;
  color: $text-secondary;
  .preview-pepper { color: $primary; font-size: 18px; }
}
.preview-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 1px solid $border;
}
.preview-tab {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: $text-secondary;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  &.active { color: $primary; font-weight: 500; border-bottom-color: $primary; }
}
.phone-mockup {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid $border;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.phone-status-bar {
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  color: $text;
  text-align: center;
  background: #fafafa;
}
.phone-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid $border;
  font-size: 13px;
  color: $text;
  .phone-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, $primary 0%, $primary-light 100%);
  }
  .phone-username { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .phone-follow { padding: 4px 12px; font-size: 12px; }
}
.phone-content {
  padding: 12px;
  min-height: 200px;
}
.phone-note-image {
  position: relative;
  width: 100%;
  border-radius: $radius-sm;
  overflow: hidden;
  margin-bottom: 8px;
  background: #f0f0f0;
  aspect-ratio: 3/4;
  img { width: 100%; height: 100%; object-fit: cover; display: block; }
}
.phone-note-images {
  position: relative;
  width: 100%;
  border-radius: $radius-sm;
  overflow: hidden;
  margin-bottom: 8px;
  background: #f0f0f0;
  aspect-ratio: 3/4;
  .phone-note-image-item {
    width: 100%;
    height: 100%;
    overflow: hidden;
    cursor: pointer;
    img { width: 100%; height: 100%; object-fit: cover; display: block; }
  }
}
.phone-note-image-indicator {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 2px 6px;
  border-radius: 10px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 10px;
}
.phone-note-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
  color: #fff;
  font-size: 14px;
  .overlay-sub { display: block; font-size: 12px; opacity: 0.9; margin-top: 4px; }
}
.phone-note-meta {
  font-size: 15px;
  font-weight: bold;
  color: $text-secondary;
  margin-bottom: 8px;
}
.phone-note-placeholder,
.phone-note-body {
  font-size: 13px;
  color: $text-secondary;
  text-align: center;
  margin-bottom: 12px;
  line-height: 1.5;
}
.phone-note-body { text-align: left; }
.phone-comment-input {
  margin-top: 8px;
  :deep(.el-input__wrapper) { border-radius: 999px; background: #f5f5f5; }
}
.phone-bottom-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid $border;
  background: #fafafa;
  .phone-bottom-input { flex: 1; :deep(.el-input__wrapper) { border-radius: 999px; background: #fff; } }
  .el-icon { font-size: 20px; color: $text-secondary; cursor: pointer; }
}
.step-actions-layout {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid $border;
}

.publish-summary {
  background: #fdfdfd;
  border-radius: $radius;
  padding: 32px;
  margin-bottom: 32px;
  border: 1px solid $border;
}
.summary-row { margin-bottom: 24px; &:last-child { margin-bottom: 0; } }
.summary-label {
  display: block;
  font-size: 13px;
  color: $text-secondary;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 500;
}
.summary-value { font-size: 15px; color: $text; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.summary-copy { max-height: 120px; overflow-y: auto; }
.summary-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.summary-image {
  max-width: 240px;
  max-height: 160px;
  border-radius: $radius-sm;
  object-fit: cover;
  display: block;
  margin-top: 8px;
}

.publish-btn {
  border-radius: $radius-sm;
  padding: 0 24px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(145deg, $primary 0%, $primary-light 100%);
  border: none;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(255, 107, 71, 0.25);
  }
  &:active { transform: translateY(0); }
}
.publish-account-section {
  background: #fdfdfd;
  border-radius: $radius;
  padding: 24px 32px;
  margin-bottom: 24px;
  border: 1px solid $border;
}
.account-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.account-section-title {
  font-size: 14px;
  font-weight: 600;
  color: $text;
}
.account-empty {
  padding: 24px 0;
}
.account-radio-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.account-radio-item {
  padding: 12px 16px;
  border-radius: $radius-sm;
  border: 1px solid $border;
  transition: all 0.2s ease;
  cursor: pointer;
  &.is-checked {
    border-color: $primary;
    background: $primary-bg;
  }
  &:hover {
    border-color: $primary-light;
  }
}
.account-radio {
  width: 100%;
  :deep(.el-radio__label) {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}
.account-name {
  font-size: 14px;
  font-weight: 500;
  color: $text;
}
.account-remark {
  font-size: 12px;
  color: $text-secondary;
}

.publish-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 16px;
  .step-btn-prev {
    height: 44px;
    padding: 0 24px;
    font-size: 15px;
    border-radius: $radius-sm;
  }
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
