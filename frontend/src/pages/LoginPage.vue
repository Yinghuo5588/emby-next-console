<template>
  <div class="login-page">
    <n-card class="login-card" bordered>
      <div class="login-header">
        <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="var(--brand)"/>
          <path d="M12 10L20 16L12 22V10Z" fill="white"/>
        </svg>
        <h1>Emby Next</h1>
        <p class="subtitle">Admin Console</p>
      </div>

      <n-form ref="formRef" :model="form" :rules="rules" size="large">
        <n-form-item path="username" label="Username">
          <n-input v-model:value="form.username" placeholder="Enter username" :disabled="loading" @keydown.enter="handleLogin" />
        </n-form-item>
        <n-form-item path="password" label="Password">
          <n-input v-model:value="form.password" type="password" show-password-on="mousedown" placeholder="Enter password" :disabled="loading" @keydown.enter="handleLogin" />
        </n-form-item>
      </n-form>

      <n-alert v-if="error" type="error" :title="error" style="margin-bottom: 1rem" />

      <n-button type="primary" block size="large" :loading="loading" @click="handleLogin">
        Login
      </n-button>

      <div class="login-footer">
        <p>© 2024 Emby Next Console</p>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInst, FormRules } from 'naive-ui'
import { NCard, NForm, NFormItem, NInput, NButton, NAlert } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInst | null>(null)
const form = ref({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
}

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
  } catch { return }

  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.value.username, form.value.password)
    router.push('/')
  } catch (err: any) {
    error.value = err.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: var(--bg);
}
.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: var(--radius-lg);
}
.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}
.login-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text);
  margin: 0.5rem 0 0.25rem;
}
.subtitle {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin: 0;
}
.login-footer {
  margin-top: 1.5rem;
  text-align: center;
}
.login-footer p {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}
</style>
