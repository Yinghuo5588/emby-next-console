<template>
  <div class="settings-page">
    <PageHeader title="设置" />

    <!-- 用户卡片 -->
    <div class="profile-card anim-in" style="--i:0">
      <div class="profile-left">
        <div class="profile-avatar">
          <IosIcon name="users" :size="22" color="#fff" :stroke-width="2" />
        </div>
        <div class="profile-info">
          <div class="profile-name">管理员</div>
          <div class="profile-badges">
            <span class="badge" :class="health?.db === 'ok' ? 'badge-ok' : 'badge-err'">
              <span class="badge-dot" /> 数据库
            </span>
            <span class="badge" :class="health?.redis === 'ok' ? 'badge-ok' : 'badge-err'">
              <span class="badge-dot" /> Redis
            </span>
          </div>
        </div>
      </div>
      <div class="profile-version">v1.0.3</div>
    </div>

    <!-- 数据配置 -->
    <div class="settings-group anim-in" style="--i:1">
      <div class="group-label">数据配置</div>
      <div class="group-card">
        <div class="setting-item">
          <div class="si-left">
            <IosIcon name="globe" :size="18" color="var(--brand)" :stroke-width="2" />
            <div>
              <div class="si-title">TMDB API Key</div>
              <div class="si-desc">内容详情的简介与图片</div>
            </div>
          </div>
          <span class="status-tag" :class="tmdbApiKey ? 'status-on' : 'status-off'">{{ tmdbApiKey ? '已配置' : '未配置' }}</span>
        </div>
        <div class="si-form">
          <n-input v-model:value="tmdbApiKey" type="password" show-password-on="click" placeholder="请输入 TMDB API Key" size="small" />
          <n-button type="primary" size="small" :loading="tmdbSaving" @click="saveTmdbApiKey">保存</n-button>
        </div>
        <div class="setting-item" style="margin-top: 10px;">
          <div class="si-left">
            <IosIcon name="link" :size="18" color="var(--brand)" :stroke-width="2" />
            <div>
              <div class="si-title">图片代理</div>
              <div class="si-desc">替换 image.tmdb.org，加速国内访问</div>
            </div>
          </div>
          <span class="status-tag" :class="tmdbImgProxy ? 'status-on' : 'status-off'">{{ tmdbImgProxy ? '已配置' : '未配置' }}</span>
        </div>
        <div class="si-form">
          <n-input v-model:value="tmdbImgProxy" placeholder="如 https://tmdb-img.example.com" size="small" />
          <n-button type="primary" size="small" :loading="tmdbProxySaving" @click="saveTmdbProxy">保存</n-button>
        </div>
      </div>
    </div>

    <!-- 连接配置 -->
    <div class="settings-group anim-in" style="--i:2">
      <div class="group-label">连接配置</div>
      <div class="group-card">
        <div class="setting-item">
          <div class="si-left">
            <IosIcon name="link" :size="18" color="#34C759" :stroke-width="2" />
            <div>
              <div class="si-title">Webhook URL</div>
              <div class="si-desc">在 Emby 后台 → 通知中添加</div>
            </div>
          </div>
        </div>
        <div class="code-block">
          <code>{{ webhookUrl }}</code>
          <n-button size="tiny" quaternary @click="copy(webhookUrl)">复制</n-button>
        </div>
        <div class="setting-item" style="margin-top: 8px;">
          <div class="si-left">
            <IosIcon name="check" :size="18" color="#FF9500" :stroke-width="2" />
            <div>
              <div class="si-title">鉴权 Token</div>
              <div class="si-desc">?token=xxx 或 Header: X-Webhook-Token</div>
            </div>
          </div>
        </div>
        <div class="code-block" v-if="webhookToken">
          <code>{{ webhookToken }}</code>
          <n-button size="tiny" quaternary @click="copy(webhookToken)">复制</n-button>
        </div>
        <div class="code-block">
          <code class="small">{{ fullExample }}</code>
          <n-button size="tiny" quaternary @click="copy(fullExample)">复制</n-button>
        </div>
      </div>
    </div>

    <!-- 其他配置 -->
    <div class="settings-group anim-in" style="--i:3">
      <div class="group-label">其他</div>
      <div class="group-card">
        <div v-for="item in settings" :key="item.setting_key" class="setting-item">
          <div class="si-left">
            <IosIcon name="settings" :size="18" color="var(--text-muted)" :stroke-width="1.8" />
            <div>
              <div class="si-title">{{ labelMap[item.setting_key] || item.setting_key }}</div>
            </div>
          </div>
          <span class="si-value">{{ masked(item) }}</span>
        </div>
        <n-empty v-if="!sLoading && settings.length === 0" description="无配置" :theme-overrides="{ fontSizeSmall: '12px' }" />
      </div>
    </div>

    <!-- 退出登录 -->
    <div class="logout-section anim-in" style="--i:4">
      <button class="logout-btn" @click="handleLogout">
        <IosIcon name="trash" :size="18" color="#FF3B30" :stroke-width="2" />
        <span>退出登录</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NButton, NEmpty, NInput, useDialog, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import { systemApi } from '@/api/system'
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
      if (s.setting_key === 'EMBY_WEBHOOK_TOKEN') { webhookToken.value = s.value || ''; break }
    }
    if (!webhookToken.value) webhookToken.value = 'embyconsole'
  } catch {}
}
async function loadTmdbSetting() {
  try { tmdbApiKey.value = String((await systemApi.getTmdbSetting()).data?.value || '') }
  catch { tmdbApiKey.value = '' }
}
async function saveTmdbApiKey() {
  tmdbSaving.value = true
  try { await systemApi.updateTmdbSetting(tmdbApiKey.value); msg.success('已保存'); await loadSettings() }
  catch { msg.error('保存失败') } finally { tmdbSaving.value = false }
}
async function saveTmdbProxy() {
  tmdbProxySaving.value = true
  try { await systemApi.updateSetting('TMDB_IMG_PROXY', tmdbImgProxy.value); msg.success('已保存') }
  catch { msg.error('保存失败') } finally { tmdbProxySaving.value = false }
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
function copy(text: string) { navigator.clipboard.writeText(text).then(() => msg.success('已复制')) }
function handleLogout() {
  dialog.warning({ title: '退出登录', content: '确定退出？', positiveText: '退出', negativeText: '取消',
    onPositiveClick: () => { localStorage.removeItem('token'); localStorage.removeItem('username'); localStorage.removeItem('avatarUrl'); window.location.href = '/login' }
  })
}
onMounted(async () => { await loadSettings(); await loadTmdbSetting(); loadTmdbProxy(); loadHealth(); loadWebhookInfo() })
</script>

<style scoped>
.settings-page { padding: 0.5rem 0 2rem; }

/* ── 入场动画 ── */
.anim-in {
  opacity: 0; transform: translateY(14px);
  animation: cardIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}
@keyframes cardIn { to { opacity: 1; transform: translateY(0); } }

/* ── 用户卡片 ── */
.profile-card {
  display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(135deg, #0A84FF 0%, #0055D6 100%);
  border-radius: 16px; padding: 1rem 1.1rem;
  margin-bottom: 1.25rem; color: #fff;
  box-shadow: 0 4px 16px rgba(0, 122, 255, 0.25);
}
.profile-left { display: flex; align-items: center; gap: 0.75rem; }
.profile-avatar {
  width: 40px; height: 40px; border-radius: 12px;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
}
.profile-name { font-size: 1rem; font-weight: 700; }
.profile-badges { display: flex; gap: 6px; margin-top: 4px; }
.badge {
  font-size: 0.6rem; font-weight: 600;
  padding: 1px 6px; border-radius: 4px;
  background: rgba(255,255,255,0.2); color: #fff;
  display: flex; align-items: center; gap: 3px;
}
.badge-dot { width: 5px; height: 5px; border-radius: 50%; }
.badge-ok .badge-dot { background: #34C759; }
.badge-err .badge-dot { background: #FF3B30; }
.profile-version { font-size: 0.75rem; opacity: 0.6; font-weight: 600; }

/* ── 分组 ── */
.settings-group { margin-bottom: 1.25rem; }
.group-label {
  font-size: 0.7rem; font-weight: 600;
  color: var(--text-muted); text-transform: uppercase;
  letter-spacing: 0.06em; padding: 0 4px 6px;
}
.group-card {
  background: var(--surface); border-radius: 14px;
  border: 1px solid var(--border); padding: 0.75rem;
}

/* ── 设置项 ── */
.setting-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.5rem 0;
}
.setting-item + .setting-item { border-top: 0.5px solid var(--border); }
.si-left { display: flex; align-items: center; gap: 0.6rem; flex: 1; min-width: 0; }
.si-title { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.si-desc { font-size: 0.7rem; color: var(--text-muted); margin-top: 1px; }
.si-value { font-size: 0.8rem; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.si-form { display: flex; gap: 8px; margin-top: 6px; }

/* ── 状态标签 ── */
.status-tag {
  font-size: 0.65rem; font-weight: 600;
  padding: 2px 8px; border-radius: 5px; flex-shrink: 0;
}
.status-on { background: rgba(52,199,89,0.1); color: #248A3D; }
.status-off { background: rgba(142,142,147,0.1); color: #8e8e93; }

/* ── 代码块 ── */
.code-block {
  display: flex; align-items: center; gap: 6px;
  background: var(--bg); border-radius: 8px;
  padding: 6px 10px; margin-top: 6px;
}
.code-block code {
  flex: 1; font-size: 0.72rem; word-break: break-all;
  color: var(--text); font-family: 'SF Mono', Menlo, monospace;
}
.code-block code.small { font-size: 0.65rem; }

/* ── 退出 ── */
.logout-section { margin-top: 0.5rem; }
.logout-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; padding: 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; color: #FF3B30;
  font-size: 0.9rem; font-weight: 600;
  font-family: inherit; cursor: pointer;
  transition: all 0.15s;
}
.logout-btn:active { background: rgba(255,59,48,0.06); }

@media (max-width: 767px) {
  .si-form { flex-direction: column; }
}
</style>
