<template>
  <div class="login-wrapper">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="login-bg-circle circle-1"></div>
      <div class="login-bg-circle circle-2"></div>
      <div class="login-bg-circle circle-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo 区域 -->
      <div class="login-header">
        <div class="login-logo">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
            <line x1="7" y1="2" x2="7" y2="22" />
            <line x1="17" y1="2" x2="17" y2="22" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <line x1="2" y1="7" x2="7" y2="7" />
            <line x1="2" y1="17" x2="7" y2="17" />
            <line x1="17" y1="17" x2="22" y2="17" />
            <line x1="17" y1="7" x2="22" y2="7" />
          </svg>
        </div>
        <h1 class="login-title">Emby Console</h1>
        <p class="login-subtitle">媒体服务器管理控制台</p>
      </div>

      <!-- 表单 -->
      <n-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <n-form-item path="username">
          <n-input
            v-model:value="form.username"
            placeholder="Emby 管理员账号"
            size="large"
            :input-props="{ autocomplete: 'username' }"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <n-icon size="18" :color="colors.muted">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="密码"
            size="large"
            :input-props="{ autocomplete: 'current-password' }"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <n-icon size="18" :color="colors.muted">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          :disabled="!form.username || !form.password"
          class="login-btn"
          @click="handleLogin"
        >
          {{ loading ? '验证中...' : '登录' }}
        </n-button>
      </n-form>

      <!-- 底部提示 -->
      <div class="login-footer">
        <span class="footer-text">使用 Emby 管理员账号登录</span>
      </div>

      <!-- 错误提示 -->
      <n-alert v-if="errorMsg" type="error" :show-icon="false" class="login-error" closable @close="errorMsg = ''">
        {{ errorMsg }}
      </n-alert>
    </div>

    <!-- 底部版权 -->
    <div class="login-bottom">
      <span>Emby Next Console · v2.0</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NForm, NFormItem, NInput, NButton, NIcon, NAlert, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const formRef = ref<any>(null)
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const colors = {
  muted: '#8e8e93',
}

async function handleLogin() {
  if (loading.value) return

  // 基础校验
  if (!form.username || !form.password) {
    errorMsg.value = '请输入账号和密码'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    await authStore.login(form.username, form.password)
    message.success('登录成功')
    router.replace('/stats')
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '登录失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}

// 已登录则跳转
onMounted(async () => {
  if (authStore.isLoggedIn) {
    router.replace('/stats')
  }
})
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0A84FF 0%, #007AFF 50%, #0055D6 100%);
}

/* ── 背景装饰圆 ── */
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.login-bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}
.circle-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #fff 0%, transparent 70%);
  top: -100px;
  right: -100px;
}
.circle-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #fff 0%, transparent 70%);
  bottom: -50px;
  left: -80px;
}
.circle-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #fff 0%, transparent 70%);
  top: 50%;
  left: 60%;
}

/* ── 登录卡片 ── */
.login-card {
  width: 100%;
  max-width: 380px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2.5rem 2rem 2rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  position: relative;
  z-index: 1;
}

/* ── Logo ── */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}
.login-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  background: linear-gradient(135deg, #0A84FF 0%, #0055D6 100%);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.35);
}
.login-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  letter-spacing: -0.02em;
}
.login-subtitle {
  font-size: 0.85rem;
  color: #8e8e93;
  margin: 0.25rem 0 0;
}

/* ── 表单 ── */
.login-card :deep(.n-input) {
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
}
.login-card :deep(.n-input:hover),
.login-card :deep(.n-input.n-input--focus) {
  border-color: #007AFF;
  background: rgba(0, 122, 255, 0.04);
}
.login-card :deep(.n-input__input-el) {
  font-size: 15px;
}
.login-card :deep(.n-form-item) {
  margin-bottom: 1.25rem;
}

/* ── 登录按钮 ── */
.login-btn {
  margin-top: 0.5rem;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #0A84FF 0%, #0055D6 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.3);
  transition: all 0.2s;
}
.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(0, 122, 255, 0.4);
}
.login-btn:active:not(:disabled) {
  transform: translateY(0);
}
.login-btn:disabled {
  opacity: 0.5;
  background: linear-gradient(135deg, #9ca3d9 0%, #a084b8 100%);
  box-shadow: none;
}

/* ── 底部 ── */
.login-footer {
  text-align: center;
  margin-top: 1.5rem;
}
.footer-text {
  font-size: 0.8rem;
  color: #aeaeb2;
}

.login-error {
  margin-top: 1rem;
  border-radius: 12px;
}

.login-bottom {
  position: absolute;
  bottom: 1.5rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.02em;
}

/* ── 暗色模式 ── */
@media (prefers-color-scheme: dark) {
  .login-wrapper {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  }
  .login-card {
    background: rgba(28, 28, 30, 0.92);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  }
  .login-title {
    color: #fff;
  }
  .login-card :deep(.n-input) {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.08);
  }
  .login-card :deep(.n-input:hover),
  .login-card :deep(.n-input.n-input--focus) {
    border-color: #0A84FF;
    background: rgba(10, 132, 255, 0.08);
  }
}

/* ── 移动端 ── */
@media (max-width: 767px) {
  .login-card {
    max-width: 100%;
    padding: 2rem 1.5rem 1.5rem;
    border-radius: 20px;
  }
  .login-logo {
    width: 56px;
    height: 56px;
    border-radius: 16px;
  }
  .login-title {
    font-size: 1.3rem;
  }
  .circle-1 { width: 250px; height: 250px; }
  .circle-2 { width: 180px; height: 180px; }
}
</style>
