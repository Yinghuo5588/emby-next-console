<template>
  <div class="portal-login">
    <div class="login-card card">
      <div class="login-logo">
        <div class="logo-icon">🎬</div>
        <h2>Emby 门户</h2>
        <p class="muted">使用你的 Emby 账号登录</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" placeholder="Emby 用户名" required autofocus />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="Emby 密码" required />
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <div class="login-footer">
        <RouterLink to="/admin" class="muted">管理员入口 →</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePortalAuthStore } from '@/stores/portal-auth'

const router = useRouter()
const auth = usePortalAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/portal')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.portal-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  padding: 20px;
}
.login-card {
  width: 360px;
  max-width: 100%;
  padding: 32px;
  text-align: center;
}
.login-logo { margin-bottom: 24px; }
.logo-icon { font-size: 48px; margin-bottom: 8px; }
.login-logo h2 { margin: 0; font-size: 22px; }
.muted { color: var(--text-muted); font-size: 13px; }
.form-group { text-align: left; margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.form-group input { width: 100%; }
.error-msg { color: var(--danger); font-size: 13px; margin-bottom: 12px; text-align: left; }
.btn-block { width: 100%; margin-top: 8px; }
.login-footer { margin-top: 20px; }
.login-footer a { text-decoration: none; }
.login-footer a:hover { color: var(--text); }
</style>