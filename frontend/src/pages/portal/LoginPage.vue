<template>
  <div class="login-wrapper">
    <n-card style="width: 360px; max-width: 100%; text-align: center" size="large">
      <div class="login-header">
        <div class="logo-ring">
          <IosIcon name="film" :size="28" color="var(--brand)" :stroke-width="1.5" />
        </div>
        <div class="login-title">Emby 门户</div>
        <div class="login-desc">使用你的 Emby 账号登录</div>
      </div>

      <n-form label-placement="top" size="medium">
        <n-form-item label="用户名">
          <n-input v-model:value="username" placeholder="Emby 用户名" @keyup.enter="handleLogin" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="password" type="password" placeholder="Emby 密码" @keyup.enter="handleLogin" />
        </n-form-item>
      </n-form>
      <n-alert v-if="error" type="error" :title="error" style="margin-bottom: 12px" />
      <n-button type="primary" block size="large" :loading="loading" @click="handleLogin">登录</n-button>

      <div class="login-footer">
        <router-link to="/admin">管理员入口</router-link>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, NAlert } from 'naive-ui'
import IosIcon from '@/components/common/IosIcon.vue'
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

<style scoped>
.login-wrapper {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg); padding: 20px;
}
.login-header { margin-bottom: 24px; }
.logo-ring {
  width: 56px; height: 56px; border-radius: 16px;
  background: var(--brand-light);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}
.login-title { font-size: 22px; font-weight: 700; }
.login-desc { color: var(--text-muted); font-size: 13px; margin-top: 4px; }
.login-footer { margin-top: 20px; }
.login-footer a { color: var(--text-muted); font-size: 13px; text-decoration: none; }
.login-footer a:hover { color: var(--text); }
</style>
