<template>
  <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--bg-secondary);padding:20px">
    <n-card style="width:360px;max-width:100%;text-align:center" size="large">
      <div style="margin-bottom:24px">
        <div style="font-size:48px">🎬</div>
        <div style="font-size:22px;font-weight:700;margin-top:8px">Emby 门户</div>
        <div style="color:var(--text-muted);font-size:13px">使用你的 Emby 账号登录</div>
      </div>

      <n-form label-placement="top" size="medium">
        <n-form-item label="用户名"><n-input v-model:value="username" placeholder="Emby 用户名" @keyup.enter="handleLogin" /></n-form-item>
        <n-form-item label="密码"><n-input v-model:value="password" type="password" placeholder="Emby 密码" @keyup.enter="handleLogin" /></n-form-item>
      </n-form>
      <n-alert v-if="error" type="error" :title="error" style="margin-bottom:12px" />
      <n-button type="primary" block size="large" :loading="loading" @click="handleLogin">登录</n-button>

      <div style="margin-top:20px">
        <router-link to="/admin" style="color:var(--text-muted);font-size:13px;text-decoration:none">管理员入口 →</router-link>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NAlert } from 'naive-ui'
import { usePortalAuthStore } from '@/stores/portal-auth'

const router = useRouter()
const auth = usePortalAuthStore()
const username = ref(''); const password = ref(''); const loading = ref(false); const error = ref('')

async function handleLogin() {
  loading.value = true; error.value = ''
  try { await auth.login(username.value, password.value); router.push('/portal') }
  catch (e: any) { error.value = e.response?.data?.detail || '登录失败，请检查用户名和密码' }
  finally { loading.value = false }
}
</script>
