<template>
  <div class="settings-page">
    <PageHeader title="设置" desc="系统配置" />

    <div class="section-card">
      <div class="section-title"><IosIcon name="globe" :size="18" color="var(--brand)" :stroke-width="2" style="margin-right: 6px; vertical-align: -2px;" /> TMDB 配置</div>
      <p class="section-desc">用于补全内容详情里的 TMDB 简介与图片信息。</p>
      <div class="tmdb-form">
        <n-input
          v-model:value="tmdbApiKey"
          type="password"
          show-password-on="click"
          placeholder="请输入 TMDB API Key"
        />
        <n-button type="primary" :loading="tmdbSaving" @click="saveTmdbApiKey">保存</n-button>
      </div>
      <div class="tmdb-form" style="margin-top: 8px;">
        <n-input
          v-model:value="tmdbImgProxy"
          placeholder="图片代理域名（可选，如 https://tmdb-img.example.com，不填用原站）"
        />
        <n-button type="primary" :loading="tmdbProxySaving" @click="saveTmdbProxy">保存代理</n-button>
      </div>
      <p class="section-desc" style="margin-top: 4px; font-size: 0.75rem; opacity: 0.6;">替换 https://image.tmdb.org 为代理地址，解决国内访问慢的问题</p>
    </div>

    <div class="section-card">
      <div class="section-title"><IosIcon name="link" :size="18" color="var(--brand)" :stroke-width="2" style="margin-right: 6px; vertical-align: -2px;" /> Webhook 配置</div>
      <p class="section-desc">在 Emby 后台 → 通知 → Webhook 中添加以下 URL</p>

      <div class="webhook-block">
        <label class="wl-label">Webhook URL</label>
        <div class="wl-row">
          <code class="wl-code">{{ webhookUrl }}</code>
          <n-button size="tiny" quaternary @click="copy(webhookUrl)">复制</n-button>
        </div>
      </div>

      <div class="webhook-block">
        <label class="wl-label">鉴权方式</label>
        <div class="wl-row">
          <code class="wl-code">?token=xxx</code>
          <span class="wl-or">或</span>
          <code class="wl-code">Header: X-Webhook-Token</code>
        </div>
      </div>

      <div class="webhook-block" v-if="webhookToken">
        <label class="wl-label">当前 Token</label>
        <div class="wl-row">
          <code class="wl-code">{{ webhookToken }}</code>
          <n-button size="tiny" quaternary @click="copy(webhookToken)">复制</n-button>
        </div>
      </div>

      <div class="webhook-block">
        <label class="wl-label">完整示例</label>
        <div class="wl-row">
          <code class="wl-code full-example">{{ fullExample }}</code>
          <n-button size="tiny" quaternary @click="copy(fullExample)">复制</n-button>
        </div>
      </div>
    </div>

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
        <div class="sr-value">{{ masked(item) }}</div>
      </div>
      <n-empty v-if="!sLoading && settings.length === 0" description="无配置" />
    </div>

    <div class="section-card">
      <div class="section-title">账户</div>
      <div class="setting-row clickable" @click="handleLogout">
        <IosIcon name="trash" :size="18" color="#FF3B30" :stroke-width="2" />
        <span class="sr-label">退出登录</span>
        <span class="sr-arrow">›</span>
      </div>
    </div>

    <div class="section-card">
      <div class="section-title">关于</div>
      <div class="setting-row">
        <IosIcon name="check" :size="18" color="var(--success)" :stroke-width="2" />
        <span class="sr-label">Emby Next Console</span>
        <span class="sr-value">v1.0.3</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NButton, NEmpty, NInput, useDialog, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import { systemApi } from '@/api/system'
import IosIcon from '@/components/common/IosIcon.vue'
import type { SettingItem, HealthResponse } from '@/api/system'

const dialog = useDialog()
const msg = useMessage()
const settings = ref<SettingItem[]>([])
const sLoading = ref(false)
const health = ref<HealthResponse | null>(null)
const hLoading = ref(false)
const tmdbApiKey = ref('')
const tmdbSaving = ref(false)
const tmdbImgProxy = ref('')
const tmdbProxySaving = ref(false)

const labelMap: Record<string, string> = { TMDB_API_KEY: 'TMDB API Key', EMBY_HOST: 'Emby 服务器', EMBY_API_KEY: 'Emby API Key' }
const webhookToken = ref('')

const webhookUrl = computed(() => {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://your-server'
  return `${origin}/api/v1/webhook/emby`
})

const fullExample = computed(() => `${webhookUrl.value}?token=${webhookToken.value || 'your-token'}`)

async function loadSettings() {
  sLoading.value = true
  try { settings.value = (await systemApi.settings()).data ?? [] } catch { settings.value = [] }
  finally { sLoading.value = false }
}
async function loadHealth() {
  hLoading.value = true
  try { health.value = (await systemApi.health()).data ?? null } catch { health.value = null }
  finally { hLoading.value = false }
}
async function loadWebhookInfo() {
  try {
    for (const s of settings.value) {
      if (s.setting_key === 'EMBY_WEBHOOK_TOKEN') {
        webhookToken.value = s.value || ''
        break
      }
    }
    if (!webhookToken.value) webhookToken.value = 'embyconsole'
  } catch {}
}
async function loadTmdbSetting() {
  try {
    const res = await systemApi.getTmdbSetting()
    tmdbApiKey.value = String(res.data?.value || '')
  } catch {
    tmdbApiKey.value = ''
  }
}
async function saveTmdbApiKey() {
  tmdbSaving.value = true
  try {
    await systemApi.updateTmdbSetting(tmdbApiKey.value)
    msg.success('TMDB API Key 已保存')
    await loadSettings()
  } catch {
    msg.error('保存失败')
  } finally {
    tmdbSaving.value = false
  }
}

async function saveTmdbProxy() {
  tmdbProxySaving.value = true
  try {
    await systemApi.updateSetting('TMDB_IMG_PROXY', tmdbImgProxy.value)
    msg.success('TMDB 图片代理已保存')
  } catch {
    msg.error('保存失败')
  } finally {
    tmdbProxySaving.value = false
  }
}

function loadTmdbProxy() {
  for (const s of settings.value) {
    if (s.setting_key === 'TMDB_IMG_PROXY') tmdbImgProxy.value = s.value_json || s.value || ''
  }
}

function masked(item: SettingItem) {
  if (item.setting_key.includes('KEY') && item.value) {
    const v = String(item.value)
    return v.length > 8 ? v.slice(0, 4) + '****' + v.slice(-4) : '****'
  }
  return String(item.value || '—')
}

function copy(text: string) {
  navigator.clipboard.writeText(text).then(() => msg.success('已复制'))
}

function handleLogout() {
  dialog.warning({
    title: '退出登录', content: '确定退出？', positiveText: '退出', negativeText: '取消',
    onPositiveClick: () => { localStorage.removeItem('token'); localStorage.removeItem('username'); localStorage.removeItem('avatarUrl'); window.location.href = '/login' }
  })
}

onMounted(async () => {
  await loadSettings()
  await loadTmdbSetting()
  loadTmdbProxy()
  loadHealth()
  loadWebhookInfo()
})
</script>

<style scoped>
.settings-page { padding-bottom: 24px; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; margin-bottom: 14px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.section-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.setting-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.setting-row:last-child { border-bottom: none; }
.clickable { cursor: pointer; }
.clickable:active { opacity: 0.7; }
.sr-label { font-size: 14px; font-weight: 500; flex: 1; }
.sr-value { font-size: 13px; color: var(--text-muted); flex-shrink: 0; }
.sr-arrow { font-size: 1.2rem; color: var(--text-muted); }
.health-grid { display: flex; gap: 20px; margin-bottom: 10px; }
.health-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.ok { background: var(--success); }
.dot.err { background: var(--danger); }
.val { color: var(--text-muted); font-size: 12px; }
.webhook-block { margin-bottom: 10px; }
.wl-label { font-size: 12px; color: var(--text-muted); display: block; margin-bottom: 4px; }
.wl-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.wl-code { background: var(--bg); padding: 6px 10px; border-radius: 8px; font-size: 12px; word-break: break-all; flex: 1; min-width: 0; }
.wl-code.full-example { font-size: 11px; }
.wl-or { font-size: 12px; color: var(--text-muted); }
.tmdb-form { display: flex; gap: 10px; align-items: center; }
@media (max-width: 767px) {
  .tmdb-form { flex-direction: column; align-items: stretch; }
}
</style>
