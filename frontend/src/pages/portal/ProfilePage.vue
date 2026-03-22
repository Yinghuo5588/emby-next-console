<template>
  <div>
    <div style="font-size:18px;font-weight:700;margin-bottom:16px">个人信息</div>

    <n-card size="small">
      <div v-if="auth.user?.avatar" style="text-align:center;margin-bottom:16px">
        <n-avatar :size="64" round><img :src="auth.user.avatar" /></n-avatar>
      </div>
      <n-descriptions :column="1" label-placement="left" size="small" bordered>
        <n-descriptions-item label="用户名">{{ auth.user?.username }}</n-descriptions-item>
        <n-descriptions-item label="显示名">{{ auth.user?.display_name || '-' }}</n-descriptions-item>
        <n-descriptions-item label="角色">
          <n-tag :type="auth.user?.is_admin ? 'success' : 'default'" size="small">{{ auth.user?.is_admin ? '管理员' : '普通用户' }}</n-tag>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-card title="修改密码" size="small" style="margin-top:16px">
      <n-form label-placement="top" size="small">
        <n-form-item label="当前密码"><n-input v-model:value="oldPwd" type="password" /></n-form-item>
        <n-form-item label="新密码"><n-input v-model:value="newPwd" type="password" /></n-form-item>
        <n-form-item label="确认新密码"><n-input v-model:value="confirmPwd" type="password" /></n-form-item>
      </n-form>
      <n-alert v-if="pwdError" type="error" :title="pwdError" style="margin-bottom:12px" />
      <n-alert v-if="pwdSuccess" type="success" :title="pwdSuccess" style="margin-bottom:12px" />
      <n-button type="primary" block :loading="pwdLoading" @click="handleChangePassword">修改密码</n-button>
    </n-card>

    <div style="margin-top:24px;text-align:center">
      <n-button quaternary type="error" @click="handleLogout">退出登录</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NAvatar, NTag, NDescriptions, NDescriptionsItem, NForm, NFormItem, NInput, NButton, NAlert, useMessage } from 'naive-ui'
import { usePortalAuthStore } from '@/stores/portal-auth'
import { portalApi } from '@/api/portal'

const router = useRouter()
const auth = usePortalAuthStore()
const msg = useMessage()
const oldPwd = ref(''); const newPwd = ref(''); const confirmPwd = ref('')
const pwdLoading = ref(false); const pwdError = ref(''); const pwdSuccess = ref('')

async function handleChangePassword() {
  pwdError.value = ''; pwdSuccess.value = ''
  if (newPwd.value !== confirmPwd.value) { pwdError.value = '两次输入的新密码不一致'; return }
  pwdLoading.value = true
  try { await portalApi.changePassword(oldPwd.value, newPwd.value); pwdSuccess.value = '密码修改成功'; oldPwd.value = ''; newPwd.value = ''; confirmPwd.value = '' }
  catch (e: any) { pwdError.value = e.response?.data?.detail || '修改失败' }
  finally { pwdLoading.value = false }
}

function handleLogout() { auth.logout(); router.push('/portal/login') }
</script>
