<template>
  <div class="home-page">
    <header class="home-header">
      <div class="header-inner">
        <div class="logo">
          <span class="logo-mark">AI</span>
          <span class="logo-text">智能运营</span>
        </div>
        <div class="user-area">
          <span class="user-name">{{ userDisplayName }}</span>
          <el-button type="text" class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
      </div>
    </header>

    <div class="home-body">
      <aside class="home-aside">
        <nav class="aside-nav">
          <div
            v-for="item in menuList"
            :key="item.key"
            class="nav-item-wrap"
          >
            <router-link
              v-if="item.key === 'create'"
              :to="'/create'"
              class="nav-item"
              :class="{ active: $route.path === '/create' }"
            >
              <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
              <span class="nav-text">{{ item.label }}</span>
            </router-link>
            <div
              v-else
              class="nav-item"
              :class="{ active: activeMenu === item.key }"
              @click="onMenuClick(item)"
            >
              <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
              <span class="nav-text">{{ item.label }}</span>
            </div>
          </div>
        </nav>
      </aside>
      <main class="home-main">
        <History
          v-if="activeMenu === 'history'"
          @go-create="goCreate"
          @use-theme="useTheme"
        />
        <Material
          v-else-if="activeMenu === 'material'"
          @go-create="goCreate"
          @use-copy="useCopy"
        />
      </main>
    </div>
  </div>
</template>

<script>
import CookieUtils from '@/utils/cookie'
import History from './History.vue'
import Material from './Material.vue'
import { Edit, List, FolderOpened } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    History,
    Material,
    Edit,
    List,
    FolderOpened,
  },
  data() {
    return {
      activeMenu: 'history',
      menuList: [
        { key: 'create', label: '创作中心', icon: Edit },
        { key: 'history', label: '历史记录', icon: List },
        { key: 'material', label: '素材库', icon: FolderOpened },
      ],
    }
  },
  computed: {
    userDisplayName() {
      return CookieUtils.getCookie('nickName') || CookieUtils.getCookie('userName') || '运营人员'
    },
  },
  methods: {
    onMenuClick(item) {
      this.activeMenu = item.key
    },
    goCreate() {
      this.$router.push('/create')
    },
    useTheme(theme) {
      this.$router.push({ path: '/create', query: { theme: theme || '' } })
    },
    useCopy(copyContent) {
      sessionStorage.setItem('createCopy', copyContent || '')
      this.$router.push('/create')
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
$primary-soft: #ffebe6;
$primary-bg: #fff8f6;
$text: #2c2c2c;
$text-secondary: #6b6b6b;
$border: #f0e8e6;
$radius: 20px;
$radius-sm: 14px;
$shadow: 0 4px 24px rgba(232, 90, 58, 0.06);
$shadow-hover: 0 8px 32px rgba(232, 90, 58, 0.1);

.home-page {
  min-height: 100vh;
  background: linear-gradient(165deg, #fffbfa 0%, #fff6f3 35%, #ffffff 70%);
  display: flex;
  flex-direction: column;
}

.home-header {
  flex-shrink: 0;
  padding: 18px 40px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba($primary, 0.06);
  transition: background 0.25s ease;

  .header-inner {
    max-width: 920px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;

    .logo-mark {
      width: 40px;
      height: 40px;
      line-height: 40px;
      text-align: center;
      background: linear-gradient(145deg, $primary 0%, $primary-light 100%);
      color: #fff;
      font-weight: 700;
      font-size: 14px;
      border-radius: 12px;
      transition: transform 0.22s ease, box-shadow 0.22s ease;
    }

    .logo-mark:hover {
      transform: scale(1.04);
      box-shadow: 0 6px 20px rgba($primary, 0.28);
    }

    .logo-text {
      font-size: 17px;
      font-weight: 600;
      color: $text;
      letter-spacing: 0.02em;
    }
  }

  .user-area {
    display: flex;
    align-items: center;
    gap: 14px;

    .user-name {
      font-size: 14px;
      color: $text-secondary;
    }

    .logout-btn {
      color: $primary;
      padding: 6px 12px;
      font-size: 13px;
      border-radius: $radius-sm;
      transition: background 0.2s ease, color 0.2s ease;
    }

    .logout-btn:hover {
      background: $primary-bg;
      color: $primary;
    }
  }
}

.home-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.home-aside {
  flex-shrink: 0;
  width: 200px;
  padding: 28px 0 28px 24px;
  border-right: 1px solid $border;
  background: rgba(255, 255, 255, 0.5);
}

.aside-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item-wrap {
  display: contents;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: $radius-sm;
  font-size: 14px;
  color: $text-secondary;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;

  .nav-icon {
    font-size: 18px;
    color: rgba($primary, 0.6);
  }

  &:hover {
    background: $primary-bg;
    color: $primary;
    .nav-icon { color: $primary; }
  }

  &.active {
    background: $primary-bg;
    color: $primary;
    font-weight: 500;
    .nav-icon { color: $primary; }
  }
}

.home-main {
  flex: 1;
  padding: 56px 28px 72px;
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
  overflow: auto;
}

.aside-nav a.nav-item {
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
