<template>
  <div class="settings-page">
    <div class="settings-header">
      <h2>设置</h2>
    </div>

    <div class="settings-section">
      <div class="section-title">账户</div>
      <div class="setting-item" @click="handleLogout">
        <span class="setting-icon">🚪</span>
        <span class="setting-label">退出登录</span>
        <span class="setting-arrow">›</span>
      </div>
    </div>

    <div class="settings-section">
      <div class="section-title">关于</div>
      <div class="setting-item">
        <span class="setting-icon">ℹ️</span>
        <span class="setting-label">Emby Next Console</span>
        <span class="setting-value">v1.0</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useDialog } from 'naive-ui'

const router = useRouter()
const dialog = useDialog()

function handleLogout() {
  dialog.warning({
    title: '退出登录',
    content: '确定退出当前账户？',
    positiveText: '退出',
    negativeText: '取消',
    onPositiveClick: () => {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('avatarUrl')
      router.replace('/login')
    },
  })
}
</script>

<style scoped>
.settings-page { padding: 0.5rem 0; }
.settings-header { margin-bottom: 1rem; }
.settings-header h2 { font-size: 1.3rem; font-weight: 700; margin: 0; }
.settings-section { margin-bottom: 1.5rem; }
.section-title { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; padding: 0 0.25rem; margin-bottom: 0.5rem; }
.setting-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; cursor: pointer; transition: all 0.15s; -webkit-tap-highlight-color: transparent; }
.setting-item:active { transform: scale(0.98); opacity: 0.7; }
.setting-item + .setting-item { margin-top: 1px; }
.setting-icon { font-size: 1.1rem; }
.setting-label { flex: 1; font-size: 0.9rem; font-weight: 500; }
.setting-value { font-size: 0.8rem; color: var(--text-muted); }
.setting-arrow { font-size: 1.2rem; color: var(--text-muted); font-weight: 300; }
</style>
