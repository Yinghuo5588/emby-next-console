<template>
  <div class="settings-page">
    <PageHeader title="设置" desc="系统配置" />

    <div class="section-card">
      <div class="section-title">系统状态</div>
      <div v-if="health" class="health-grid">
        <div class="health-item"><span class="dot" :class="health.db === 'ok' ? 'ok' : 'err'" /> 数据库 <span class="val">{{ health.db }}</span></div>
        <div class="health-item"><span class="dot" :class="health.redis === 'ok' ? 'ok' : 'err'" /> Redis <span class="val">{{ health.redis }}</span></div>
      </div>
      <n-button size="small" quaternary @click="loadHealth" :loading="hLoading">刷新</n-button>
    </div>

    <div class="section-card">
      <div class="section-title">配置项</div>
      <div v-for="item in settings" :key="item.setting_key" class="setting-row">
        <div class="sr-label">{{ labelMap[item.setting_key] || item.setting_key }}</div>
        <div class="sr-desc">{{ item.description }}</div>
        <div class="sr-value">{{ masked(item) }}</div>
      </div>
      <n-empty v-if="!sLoading && settings.length === 0" description="无配置" />
    </div>

    <div class="section-card">
      <div class="section-title">账户</div>
      <div class="setting-row clickable" @click="handleLogout">
        <span>🚪</span>
        <span class="sr-label">退出登录</span>
        <span class="sr-arrow">›</span>
      </div>
    </div>

    <div class="section-card">
      <div class="section-title">关于</div>
      <div class="setting-row">
        <span>ℹ️</span>
        <span class="sr-label">Emby Next Console</span>
        <span class="sr-value">v2.0</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NEmpty, useDialog } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import { systemApi } from '@/api/system'
import type { SettingItem, HealthResponse } from '@/api/system'

const dialog = useDialog()
const settings = ref<SettingItem[]>([])
const sLoading = ref(false)
const health = ref<HealthResponse | null>(null)
const hLoading = ref(false)

const labelMap: Record<string, string> = { TMDB_API_KEY: 'TMDB API Key', EMBY_HOST: 'Emby 服务器', EMBY_API_KEY: 'Emby API Key' }

async function loadSettings() { sLoading.value = true; try { settings.value = (await systemApi.settings()).data ?? [] } catch { settings.value = [] } finally { sLoading.value = false } }
async function loadHealth() { hLoading.value = true; try { health.value = (await systemApi.health()).data ?? null } catch { health.value = null } finally { hLoading.value = false } }

function masked(item: SettingItem) {
  if (item.setting_key.includes('KEY') && item.value) { const v = String(item.value); return v.length > 8 ? v.slice(0, 4) + '****' + v.slice(-4) : '****' }
  return String(item.value || '—')
}

function handleLogout() {
  dialog.warning({ title: '退出登录', content: '确定退出？', positiveText: '退出', negativeText: '取消', onPositiveClick: () => { localStorage.removeItem('token'); localStorage.removeItem('username'); localStorage.removeItem('avatarUrl'); window.location.href = '/login' } })
}

onMounted(() => { loadSettings(); loadHealth() })
</script>

<style scoped>
.settings-page { padding-bottom: 24px; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; margin-bottom: 14px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.setting-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.setting-row:last-child { border-bottom: none; }
.clickable { cursor: pointer; }
.clickable:active { opacity: 0.7; }
.sr-label { font-size: 14px; font-weight: 500; flex: 1; }
.sr-desc { font-size: 12px; color: var(--text-muted); }
.sr-value { font-size: 13px; color: var(--text-muted); flex-shrink: 0; }
.sr-arrow { font-size: 1.2rem; color: var(--text-muted); }
.health-grid { display: flex; gap: 20px; margin-bottom: 10px; }
.health-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.ok { background: var(--success); }
.dot.err { background: var(--danger); }
.val { color: var(--text-muted); font-size: 12px; }
</style>
