<template>
  <div class="layout-page">
    <header class="layout-header">
      <div class="header-inner">
        <div class="logo" @click="goHome">
          <span class="logo-mark">AI</span>
          <span class="logo-text">智能运营平台</span>
        </div>
        <div class="user-area">
          <el-dropdown trigger="click" placement="bottom-end" @command="handleUserCommand">
            <span class="user-trigger">
              <span class="user-name">{{ userDisplayName }}</span>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="xiaohongshu">
                  <el-icon><Link /></el-icon>
                  小红书 Cookie 与信息
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <div class="layout-body">
      <aside class="layout-aside">
        <nav class="aside-nav">
          <div
            v-for="item in menuList"
            :key="item.key"
            class="nav-item"
            :class="{ active: isActive(item) }"
            @click="goToPage(item)"
          >
            <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
            <span class="nav-text">{{ item.label }}</span>
          </div>
        </nav>
      </aside>
      <main class="layout-main">
        <div class="page-container">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import CookieUtils from '@/utils/cookie'
import { Edit, List, FolderOpened, ArrowDown, Link, SwitchButton } from '@element-plus/icons-vue'

export default {
  name: 'Layout',
  components: { Edit, List, FolderOpened, ArrowDown, Link, SwitchButton },
  data() {
    return {
      menuList: [
        { key: 'create', label: '创作中心', icon: Edit, path: '/create' },
        { key: 'history', label: '历史记录', icon: List, path: '/home/history' },
        { key: 'material', label: '素材库', icon: FolderOpened, path: '/home/material' },
      ],
    }
  },
  computed: {
    userDisplayName() {
      return CookieUtils.getCookie('nickName') || CookieUtils.getCookie('userName') || '运营人员'
    },
  },
  methods: {
    isActive(item) {
      const path = this.$route.path
      if (item.key === 'create') return path === '/create'
      if (item.key === 'history') return path === '/home/history'
      if (item.key === 'material') return path === '/home/material'
      return false
    },
    goToPage(item) {
      if (item.key === 'create') {
        // 创作中心：先通知 CreatePublish 组件重置状态，再跳转
        window.dispatchEvent(new CustomEvent('reset-create-workflow'))
        this.$router.push('/create')
      } else {
        this.$router.push(item.path)
      }
    },
    goHome() {
      this.$router.push('/home/history')
    },
    handleUserCommand(command) {
      if (command === 'xiaohongshu') {
        this.$router.push('/home/xiaohongshu-settings')
      } else if (command === 'logout') {
        this.handleLogout()
      }
    },
    handleLogout() {
      CookieUtils.setCookie('isLoggedIn', '', -1)
      CookieUtils.setCookie('userId', '', -1)
      CookieUtils.setCookie('userName', '', -1)
      CookieUtils.setCookie('nickName', '', -1)
      CookieUtils.setCookie('accessToken', '', -1)
      CookieUtils.setCookie('refreshToken', '', -1)
      localStorage.clear()
      this.$router.push('/login')
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
$bg-color: #f5f7fa;

.layout-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-color;
  font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.layout-header {
  flex-shrink: 0;
  height: 56px;
  padding: 0 20px;
  background: #ffffff;
  border-bottom: 1px solid $border;
  display: flex;
  align-items: center;
  z-index: 10;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
}

.header-inner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  .logo-mark {
    width: 36px;
    height: 36px;
    line-height: 36px;
    text-align: center;
    background: linear-gradient(135deg, $primary 0%, $primary-light 100%);
    color: #fff;
    font-weight: 700;
    font-size: 16px;
    border-radius: 8px;
  }
  .logo-text { font-size: 20px; font-weight: 600; color: $text; letter-spacing: 1px; }
}

.user-area {
  display: flex;
  align-items: center;
  .user-trigger {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    &:hover { background: #f5f7fa; }
    .user-name { font-size: 14px; color: $text-secondary; font-weight: 500; }
    .dropdown-arrow { font-size: 12px; color: $text-secondary; }
  }
}

.layout-body {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.layout-aside {
  flex-shrink: 0;
  width: 200px;
  background: #ffffff;
  border-right: 1px solid $border;
  padding: 16px 12px;
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(0, 21, 41, 0.02);
  z-index: 5;
}

.aside-nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  color: $text-secondary;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s ease;
  
  .nav-icon { font-size: 22px; transition: color 0.3s ease; }
  
  &:hover {
    background: #f7f8fa;
    color: $text;
  }
  
  &.active {
    background: $primary-bg;
    color: $primary;
    .nav-icon { color: $primary; }
  }
}

.layout-main {
  flex: 1;
  min-height: 0;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.page-container {
  width: 100%;
  max-width: 100%;
  min-height: 0;
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
}
</style>
