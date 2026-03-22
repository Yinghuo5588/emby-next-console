<template>
  <div>
    <h3 class="page-title">个人信息</h3>

    <div class="card profile-card">
      <div class="pf-avatar" v-if="auth.user?.avatar">
        <img :src="auth.user.avatar" alt="avatar" />
      </div>
      <div class="pf-item">
        <div class="pf-label">用户名</div>
        <div class="pf-value">{{ auth.user?.username }}</div>
      </div>
      <div class="pf-item">
        <div class="pf-label">显示名</div>
        <div class="pf-value">{{ auth.user?.display_name || '-' }}</div>
      </div>
      <div class="pf-item">
        <div class="pf-label">角色</div>
        <div class="pf-value">
          <span class="tag" :class="auth.user?.is_admin ? 'tag-green' : 'tag-gray'">
            {{ auth.user?.is_admin ? '管理员' : '普通用户' }}
          </span>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <h4 style="margin-bottom: 16px;">修改密码</h4>
      <form @submit.prevent="handleChangePassword">
        <div class="form-group">
          <label>当前密码</label>
          <input v-model="oldPwd" type="password" required />
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="newPwd" type="password" required minlength="6" />
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input v-model="confirmPwd" type="password" required />
        </div>
        <div v-if="pwdError" class="error-msg">{{ pwdError }}</div>
        <div v-if="pwdSuccess" class="success-msg">{{ pwdSuccess }}</div>
        <button type="submit" class="btn btn-primary" :disabled="pwdLoading">
          {{ pwdLoading ? '修改中...' : '修改密码' }}
        </button>
      </form>
    </div>

    <div style="margin-top: 24px; text-align: center;">
      <button class="btn btn-ghost" @click="handleLogout">退出登录</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePortalAuthStore } from '@/stores/portal-auth'
import { portalApi } from '@/api/portal'

const router = useRouter()
const auth = usePortalAuthStore()

const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdLoading = ref(false)
const pwdError = ref('')
const pwdSuccess = ref('')

async function handleChangePassword() {
  pwdError.value = ''
  pwdSuccess.value = ''

  if (newPwd.value !== confirmPwd.value) {
    pwdError.value = '两次输入的新密码不一致'
    return
  }

  pwdLoading.value = true
  try {
    await portalApi.changePassword(oldPwd.value, newPwd.value)
    pwdSuccess.value = '密码修改成功'
    oldPwd.value = ''; newPwd.value = ''; confirmPwd.value = ''
  } catch (e: any) {
    pwdError.value = e.response?.data?.detail || '修改失败'
  } finally {
    pwdLoading.value = false
  }
}

function handleLogout() {
  auth.logout()
  router.push('/portal/login')
}
</script>

<style scoped>
.page-title { font-size: 18px; margin-bottom: 16px; }
.profile-card { padding: 20px; }
.pf-avatar { text-align: center; margin-bottom: 16px; }
.pf-avatar img { width: 64px; height: 64px; border-radius: 50%; }
.pf-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); }
.pf-item:last-child { border-bottom: none; }
.pf-label { font-size: 13px; color: var(--text-muted); }
.pf-value { font-size: 14px; font-weight: 500; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.form-group input { width: 100%; }
.error-msg { color: var(--danger); font-size: 13px; margin-bottom: 12px; }
.success-msg { color: var(--success, #22c55e); font-size: 13px; margin-bottom: 12px; }
</style>