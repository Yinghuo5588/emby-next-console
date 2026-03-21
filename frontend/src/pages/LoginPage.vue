<template>
 <div class="login-page">
 <div class="login-box card">
 <h1 class="login-title">Emby Console</h1>
 <p class="login-sub">管理员登录</p>
 <form @submit.prevent="handleLogin">
 <div class="field">
 <label>用户名</label>
 <input v-model="form.username" type="text" placeholder="username" autocomplete="username" />
 </div>
 <div class="field">
 <label>密码</label>
 <input v-model="form.password" type="password" placeholder="password" autocomplete="current-password" />
 </div>
 <p v-if="error" class="error-msg">{{ error }}</p>
 <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
 {{ loading ? '登录中...' : '登录' }}
 </button>
 </form>
 </div>
 </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
 if (!form.username || !form.password) return
 loading.value = true
 error.value = ''
 try {
 await auth.login(form.username, form.password)
 router.push('/dashboard')
 } catch {
 error.value = '用户名或密码错误'
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
 background: var(--color-bg);
}
.login-box {
 width: 360px;
 padding: 36px;
}
.login-title {
 font-size: 22px;
 font-weight: 700;
 color: var(--color-primary);
 margin-bottom: 4px;
 text-align: center;
}
.login-sub {
 color: var(--color-text-muted);
 margin-bottom: 28px;
 font-size: 13px;
 text-align: center;
}
.field { margin-bottom: 16px; }
.field label {
 display: block;
 margin-bottom: 6px;
 font-size: 13px;
 color: var(--color-text-muted);
}
.field input {
 width: 100%;
 padding: 9px 12px;
 background: var(--color-surface-2);
 border: 1px solid var(--color-border);
 border-radius: 6px;
 color: var(--color-text);
 font-size: 14px;
 outline: none;
}
.field input:focus { border-color: var(--color-primary); }
.submit-btn {
 width: 100%;
 justify-content: center;
 padding: 10px;
 margin-top: 8px;
}
.error-msg {
 color: var(--color-danger);
 font-size: 13px;
 margin-bottom: 10px;
 text-align: center;
}
</style>