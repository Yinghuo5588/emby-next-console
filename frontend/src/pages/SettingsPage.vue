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

    <!-- 推送通知 -->
    <div class="settings-group anim-in" style="--i:2.5">
      <div class="group-label">推送通知</div>
      <div class="group-card">
        <div v-for="dest in notifyDests" :key="dest.id" class="notify-item" @click="editNotify(dest)">
          <div class="ni-left">
            <IosIcon name="bell" :size="18" :color="dest.is_active ? 'var(--brand)' : 'var(--text-muted)'" :stroke-width="2" />
            <div class="ni-body">
              <div class="ni-name">{{ dest.name }}</div>
              <div class="ni-url">{{ dest.url }}</div>
              <div class="ni-events">
                <span v-for="ev in dest.events.slice(0, 3)" :key="ev" class="ni-event-tag">{{ eventLabel(ev) }}</span>
                <span v-if="dest.events.length > 3" class="ni-more">+{{ dest.events.length - 3 }}</span>
              </div>
            </div>
          </div>
          <span class="status-tag" :class="dest.is_active ? 'status-on' : 'status-off'">{{ dest.is_active ? '活跃' : '停用' }}</span>
        </div>
        <div v-if="notifyDests.length === 0" class="ni-empty">暂无推送目标</div>
        <n-button size="small" block secondary @click="showNotifyModal = true" style="margin-top:8px">
          <IosIcon name="link" :size="14" style="margin-right:4px" /> 添加推送目标
        </n-button>
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
    <!-- 推送通知弹窗 -->
    <n-modal v-model:show="showNotifyModal" preset="card" :title="editingNotify ? '编辑推送目标' : '添加推送目标'" class="modal-card" :style="{ maxWidth: '440px' }">
      <n-form :model="notifyForm" label-placement="top">
        <n-form-item label="名称"><n-input v-model:value="notifyForm.name" placeholder="如：企业微信机器人" /></n-form-item>
        <n-form-item label="URL"><n-input v-model:value="notifyForm.url" placeholder="https://..." /></n-form-item>
        <n-form-item label="签名密钥（可选）"><n-input v-model:value="notifyForm.secret" placeholder="HMAC-SHA256 签名" /></n-form-item>
        <n-form-item label="订阅事件">
          <n-checkbox-group v-model:value="notifyForm.events">
            <div style="display:flex;flex-direction:column;gap:6px">
              <n-checkbox v-for="ev in availableEvents" :key="ev.key" :value="ev.key" :label="ev.label" />
            </div>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="notifyForm.is_active" />
          <span style="margin-left:8px;font-size:13px;color:var(--text-muted)">{{ notifyForm.is_active ? '活跃' : '停用' }}</span>
        </n-form-item>
      </n-form>
      <template #action>
        <div style="display:flex;gap:8px">
          <n-button v-if="editingNotify" size="small" @click="testNotify" :loading="testing">发送测试</n-button>
          <n-button v-if="editingNotify" size="small" type="error" quaternary @click="deleteNotify">删除</n-button>
          <div style="flex:1" />
          <n-button size="small" @click="showNotifyModal = false">取消</n-button>
          <n-button size="small" type="primary" @click="saveNotify" :loading="saving">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NButton, NEmpty, NInput, useDialog, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import { systemApi } from '@/api/system'
import { notifyApi } from '@/api/notify'
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

// ── 推送通知 ──
const notifyDests = ref<any[]>([])
const availableEvents = ref<{ key: string; label: string }[]>([])
const showNotifyModal = ref(false)
const editingNotify = ref<any>(null)
const saving = ref(false)
const testing = ref(false)
const notifyForm = ref<{ name: string; url: string; secret: string; events: string[]; is_active: boolean }>({
  name: '', url: '', secret: '', events: [], is_active: true,
})

function eventLabel(key: string) {
  return availableEvents.value.find(e => e.key === key)?.label || key
}
function editNotify(dest: any) {
  editingNotify.value = dest
  notifyForm.value = { name: dest.name, url: dest.url, secret: '', events: [...dest.events], is_active: dest.is_active }
  showNotifyModal.value = true
}
async function saveNotify() {
  if (!notifyForm.value.name || !notifyForm.value.url) { msg.warning('请填写名称和URL'); return }
  saving.value = true
  try {
    if (editingNotify.value) {
      await notifyApi.update(editingNotify.value.id, notifyForm.value)
    } else {
      await notifyApi.create(notifyForm.value)
    }
    msg.success('已保存')
    showNotifyModal.value = false
    editingNotify.value = null
    await loadNotifyDests()
  } catch { msg.error('保存失败') }
  finally { saving.value = false }
}
async function deleteNotify() {
  if (!editingNotify.value) return
  dialog.warning({ title: '删除', content: `确定删除「${editingNotify.value.name}」？`, positiveText: '删除', negativeText: '取消',
    onPositiveClick: async () => {
      await notifyApi.delete(editingNotify.value.id)
      msg.success('已删除')
      showNotifyModal.value = false
      editingNotify.value = null
      await loadNotifyDests()
    }
  })
}
async function testNotify() {
  if (!editingNotify.value) return
  testing.value = true
  try {
    const res = await notifyApi.test(editingNotify.value.id)
    if (res.data?.message === '发送成功') msg.success('测试通知已发送')
    else msg.error(res.data?.error || '发送失败')
  } catch { msg.error('测试失败') }
  finally { testing.value = false }
}
async function loadNotifyDests() {
  try { notifyDests.value = (await notifyApi.list()).data ?? [] } catch { notifyDests.value = [] }
}
async function loadEvents() {
  try { availableEvents.value = (await notifyApi.events()).data ?? [] } catch { availableEvents.value = [] }
}

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
onMounted(async () => { await loadSettings(); await loadTmdbSetting(); loadTmdbProxy(); loadHealth(); loadWebhookInfo(); loadNotifyDests(); loadEvents() })
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

/* ── 推送通知 ── */
.notify-item {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 0.6rem 0; cursor: pointer;
  border-bottom: 0.5px solid var(--border);
  transition: background 0.15s; border-radius: 8px;
}
.notify-item:last-of-type { border-bottom: none; }
.notify-item:active { background: var(--bg-secondary); }
.ni-left { display: flex; align-items: flex-start; gap: 0.5rem; flex: 1; min-width: 0; }
.ni-body { flex: 1; min-width: 0; }
.ni-name { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.ni-url { font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px; }
.ni-events { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.ni-event-tag { font-size: 0.6rem; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(0,122,255,0.08); color: var(--brand); }
.ni-more { font-size: 0.6rem; color: var(--text-muted); }
.ni-empty { text-align: center; padding: 1rem; color: var(--text-muted); font-size: 0.8rem; }

@media (max-width: 767px) {
  .si-form { flex-direction: column; }
}
</style>
