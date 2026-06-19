import { createRouter, createWebHistory } from 'vue-router'
import { getCookie } from '@/utils/cookie'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/home/history',
    children: [
      {
        path: 'home',
        component: () => import('@/views/HomeContainer.vue'),
        redirect: 'history',
        children: [
          { path: 'history', name: 'History', component: () => import('@/views/History.vue') },
          { path: 'material', name: 'Material', component: () => import('@/views/Material.vue') },
          { path: 'xiaohongshu-settings', name: 'XiaohongshuSettings', component: () => import('@/views/XiaohongshuSettings.vue') },
        ],
      },
      {
        path: 'create',
        name: 'CreatePublish',
        component: () => import('@/views/CreatePublish.vue'),
      },
    ],
  },
  {
    path: '/home',
    redirect: '/home/history',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, _from, next) => {
  const isLoggedIn = getCookie('isLoggedIn') === 'true'
  const hasUserId = !!getCookie('userId')
  if (to.meta.requiresAuth && (!isLoggedIn || !hasUserId)) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && isLoggedIn && hasUserId) {
    next({ path: '/create' })
  } else {
    next()
  }
})

export default router
