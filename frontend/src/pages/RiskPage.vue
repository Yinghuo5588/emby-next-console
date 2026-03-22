<template>
  <div>
    <PageHeader title="风控中心" desc="并发越界检测 · 违规客户端拦截 · 异常事件处置">
      <template #actions>
        <button class="btn btn-ghost" :disabled="loading" @click="loadAll">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </template>
    </PageHeader>

    <!-- 概览卡片 -->
    <section class="overview-row">
      <div class="card overview-card" :class="{ 'card-warning': (summary?.open_count ?? 0) > 0 }">
        <div class="ov-icon">📋</div>
        <div class="ov-info">
          <div class="ov-label">待处理事件</div>
          <div class="ov-value" :class="{ 'text-warning': (summary?.open_count ?? 0) > 0 }">{{ summary?.open_count ?? 0 }}</div>
        </div>
      </div>
      <div class="card overview-card" :class="{ 'card-danger': (summary?.high_count ?? 0) > 0 }">
        <div class="ov-icon">🚨</div>
        <div class="ov-info">
          <div class="ov-label">高危事件</div>
          <div class="ov-value" :class="{ 'text-danger': (summary?.high_count ?? 0) > 0 }">{{ summary?.high_count ?? 0 }}</div>
        </div>
      </div>
      <div class="card overview-card">
        <div class="ov-icon">🚫</div>
        <div class="ov-info">
          <div class="ov-label">黑名单客户端</div>
          <div class="ov-value">{{ blacklist.length }}</div>
        </div>
      </div>
    </section>

    <!-- 实时会话（可踢出） -->
    <section class="card" style="margin-bottom: 16px;">
      <div class="section-head">
        <span class="section-title">🔴 实时播放会话</span>
        <button class="btn btn-sm btn-ghost" @click="loadSessions">刷新</button>
      </div>
      <LoadingState v-if="sessionsLoading" height="80px" />
      <EmptyState v-else-if="liveSessions.length === 0" title="暂无播放会话" desc="" />
      <div v-else class="sessions-grid">
        <div v-for="s in liveSessions" :key="s.Id" class="session-card card">
          <div class="sc-header">
            <span class="sc-user">{{ s.UserName || '未知' }}</span>
            <span class="sc-client tag tag-blue">{{ s.Client || '' }}</span>
          </div>
          <div class="sc-media">{{ s.NowPlayingItem?.Name || '未知内容' }}</div>
          <div class="sc-device">{{ s.DeviceName || '' }}</div>
          <button class="btn btn-sm btn-danger" :disabled="kickingId === s.Id" @click="doKick(s.Id, s.UserName)">
            {{ kickingId === s.Id ? '踢出中...' : '🚫 踢出播放' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 客户端黑名单 -->
    <section class="card" style="margin-bottom: 16px;">
      <div class="section-head">
        <span class="section-title">🚫 客户端黑名单</span>
        <div class="blacklist-add">
          <input v-model="newBlacklistItem" class="bl-input" placeholder="输入客户端名称 (如: Infuse)" @keyup.enter="addToBlacklist" />
          <button class="btn btn-sm btn-primary" :disabled="!newBlacklistItem.trim()" @click="addToBlacklist">添加</button>
        </div>
      </div>
      <div v-if="blacklist.length === 0" class="empty-hint">黑名单为空，未拦截任何客户端</div>
      <div v-else class="blacklist-list">
        <div v-for="item in blacklist" :key="item" class="bl-item">
          <span class="bl-name">{{ item }}</span>
          <button class="btn btn-ghost btn-sm" @click="removeFromBlacklist(item)">移除</button>
        </div>
      </div>
    </section>

    <!-- 风控事件列表 -->
    <section class="card" style="margin-bottom: 16px;">
      <div class="section-head">
        <span class="section-title">📋 风控事件</span>
        <div class="filter-tabs">
          <button class="tab" :class="{ active: eventFilter.status === '' }" @click="eventFilter.status = ''; loadEvents()">全部</button>
          <button class="tab" :class="{ active: eventFilter.status === 'open' }" @click="eventFilter.status = 'open'; loadEvents()">待处理</button>
          <button class="tab" :class="{ active: eventFilter.status === 'resolved' }" @click="eventFilter.status = 'resolved'; loadEvents()">已解决</button>
          <button class="tab" :class="{ active: eventFilter.status === 'ignored' }" @click="eventFilter.status = 'ignored'; loadEvents()">已忽略</button>
        </div>
      </div>

      <LoadingState v-if="eventsLoading && events.length === 0" height="120px" />
      <EmptyState v-else-if="events.length === 0" title="暂无风控事件" desc="系统正常运行中 ✅" />
      <div v-else class="events-list">
        <div v-for="ev in events" :key="ev.event_id" class="event-item" :class="{ 'event-high': ev.severity === 'high', 'event-open': ev.status === 'open' }">
          <div class="ev-severity">
            <span class="tag" :class="severityTag(ev.severity)">{{ severityLabel(ev.severity) }}</span>
          </div>
          <div class="ev-content">
            <div class="ev-title">{{ ev.title }}</div>
            <div class="ev-desc">{{ ev.description || '—' }}</div>
            <div class="ev-time">{{ formatTime(ev.detected_at) }}</div>
          </div>
          <div v-if="ev.status === 'open'" class="ev-actions">
            <button class="btn btn-sm btn-primary" :disabled="actioningId === ev.event_id" @click="handleAction(ev.event_id, 'resolve')">解决</button>
            <button class="btn btn-sm btn-ghost" :disabled="actioningId === ev.event_id" @click="handleAction(ev.event_id, 'ignore')">忽略</button>
            <button v-if="ev.user_id" class="btn btn-sm btn-danger" :disabled="banningId === ev.user_id" @click="doBan(ev.user_id, ev.title)">
              {{ banningId === ev.user_id ? '封禁中...' : '🚫 封禁' }}
            </button>
          </div>
          <div v-else class="ev-status">
            <span class="tag" :class="ev.status === 'resolved' ? 'tag-green' : 'tag-gray'">{{ ev.status === 'resolved' ? '已解决' : '已忽略' }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 执法日志 -->
    <section class="card">
      <div class="section-head">
        <span class="section-title">📝 执法日志</span>
      </div>
      <EmptyState v-if="actionLogs.length === 0" title="暂无执法记录" desc="" />
      <div v-else class="log-list">
        <div v-for="log in actionLogs" :key="log.id" class="log-item">
          <span class="tag" :class="logTag(log.action)">{{ logLabel(log.action) }}</span>
          <span class="log-target">{{ log.target }}</span>
          <span class="log-reason">{{ log.reason }}</span>
          <span class="log-time">{{ formatTime(log.created_at) }}</span>
        </div>
      </div>
    </section>

    <Transition name="toast">
      <div v-if="toast" class="toast" :class="`toast-${toast.type}`">{{ toast.message }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { riskApi } from '@/api/risk'
import type { RiskActionLog } from '@/api/risk'
import { systemApi } from '@/api/system'
import apiClient from '@/api/client'

const summary = ref<any>(null)
const events = ref<any[]>([])
const eventsLoading = ref(false)
const loading = ref(false)
const actioningId = ref<string | null>(null)
const banningId = ref<string | null>(null)
const kickingId = ref<string | null>(null)
const blacklist = ref<string[]>([])
const newBlacklistItem = ref('')
const eventFilter = reactive({ status: 'open' })
const toast = ref<{ message: string; type: string } | null>(null)

// Live sessions
const liveSessions = ref<any[]>([])
const sessionsLoading = ref(false)

// Action logs
const actionLogs = ref<RiskActionLog[]>([])

async function loadSummary() {
  loading.value = true
  try { summary.value = (await riskApi.summary()).data } finally { loading.value = false }
}

async function loadEvents() {
  eventsLoading.value = true
  try {
    const res = await riskApi.events(1, 50, eventFilter.status || undefined)
    events.value = res.data?.items ?? []
  } catch { events.value = [] }
  finally { eventsLoading.value = false }
}

async function loadBlacklist() {
  try {
    const res = await systemApi.clientBlacklist()
    blacklist.value = res.data ?? []
  } catch { blacklist.value = [] }
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    const res = await apiClient.get('/dashboard/summary')
    liveSessions.value = res.data?.data?.sessions ?? []
    // Also get active sessions from Emby
    const res2 = await apiClient.get('/system/sessions')
    const embySessions = res2.data?.data ?? []
    liveSessions.value = embySessions.filter((s: any) => s.NowPlayingItem)
  } catch { liveSessions.value = [] }
  finally { sessionsLoading.value = false }
}

async function loadActionLogs() {
  try {
    const res = await riskApi.logs(1, 20)
    actionLogs.value = res.data?.items ?? []
  } catch { actionLogs.value = [] }
}

async function doKick(sessionId: string, userName: string) {
  kickingId.value = sessionId
  try {
    const res = await riskApi.kick(sessionId)
    if (res.data?.success) {
      showToast(`已踢出 ${userName || '会话'}`, 'success')
      await loadSessions()
      await loadActionLogs()
    } else {
      showToast('踢出失败', 'error')
    }
  } catch { showToast('踢出失败', 'error') }
  finally { kickingId.value = null }
}

async function doBan(userId: string, title: string) {
  banningId.value = userId
  try {
    const res = await riskApi.ban(userId)
    if (res.data?.success) {
      showToast(`已封禁用户`, 'success')
      await loadAll()
    } else {
      showToast('封禁失败', 'error')
    }
  } catch { showToast('封禁失败', 'error') }
  finally { banningId.value = null }
}

async function addToBlacklist() {
  const name = newBlacklistItem.value.trim()
  if (!name) return
  try {
    await systemApi.addClientBlacklist(name)
    blacklist.value.push(name)
    newBlacklistItem.value = ''
    showToast(`已添加 ${name} 到黑名单`, 'success')
  } catch { showToast('添加失败', 'error') }
}

async function removeFromBlacklist(name: string) {
  try {
    await systemApi.removeClientBlacklist(name)
    blacklist.value = blacklist.value.filter(x => x !== name)
    showToast(`已移除 ${name}`, 'success')
  } catch { showToast('移除失败', 'error') }
}

async function handleAction(id: string, action: string) {
  actioningId.value = id
  try {
    await riskApi.action(id, action as 'resolve' | 'ignore')
    showToast(action === 'resolve' ? '已解决' : '已忽略', 'success')
    await loadAll()
  } catch { showToast('操作失败', 'error') }
  finally { actioningId.value = null }
}

async function loadAll() { await Promise.all([loadSummary(), loadEvents(), loadBlacklist(), loadSessions(), loadActionLogs()]) }

function severityTag(s: string) { return { high: 'tag-red', medium: 'tag-yellow', low: 'tag-blue' }[s] ?? 'tag-gray' }
function severityLabel(s: string) { return { high: '高危', medium: '中危', low: '低危' }[s] ?? s }
function logTag(a: string) { return { kick: 'tag-red', ban: 'tag-red', unban: 'tag-green' }[a] ?? 'tag-gray' }
function logLabel(a: string) { return { kick: '踢出', ban: '封禁', unban: '解封' }[a] ?? a }
function formatTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
function showToast(message: string, type: string) { toast.value = { message, type }; setTimeout(() => { toast.value = null }, 2500) }

onMounted(loadAll)
</script>

<style scoped>
.overview-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 16px; }
.overview-card { display: flex; align-items: center; gap: 12px; padding: 16px; }
.card-warning { border-color: var(--warning); }
.card-danger { border-color: var(--danger); }
.ov-icon { font-size: 28px; }
.ov-label { font-size: 12px; color: var(--text-muted); }
.ov-value { font-size: 28px; font-weight: 700; }
.text-warning { color: var(--warning); }
.text-danger { color: var(--danger); }

.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.section-title { font-weight: 600; font-size: 14px; }

/* Sessions grid */
.sessions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; }
.session-card { padding: 12px; display: flex; flex-direction: column; gap: 6px; }
.sc-header { display: flex; align-items: center; justify-content: space-between; }
.sc-user { font-weight: 600; font-size: 13px; }
.sc-media { font-size: 12px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-device { font-size: 11px; color: var(--text-muted); }
.btn-danger { background: var(--danger); color: #fff; border: none; }
.btn-danger:hover { opacity: 0.9; }

.blacklist-add { display: flex; gap: 8px; }
.bl-input { width: 180px; padding: 6px 10px; font-size: 13px; }
.blacklist-list { display: flex; flex-wrap: wrap; gap: 8px; }
.bl-item { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--bg-secondary); border-radius: 8px; font-size: 13px; }
.bl-name { font-weight: 500; }
.empty-hint { font-size: 13px; color: var(--text-muted); padding: 12px 0; }

.filter-tabs { display: flex; gap: 4px; }
.tab { padding: 4px 12px; border-radius: 6px; font-size: 12px; background: transparent; color: var(--text-muted); border: 1px solid var(--border); cursor: pointer; }
.tab.active { background: var(--brand); color: #fff; border-color: var(--brand); }

.events-list { display: flex; flex-direction: column; gap: 8px; }
.event-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 8px; border: 1px solid var(--border); transition: border-color 0.2s; }
.event-item.event-open.event-high { border-color: var(--danger); background: var(--danger-light); }
.event-item.event-open:not(.event-high) { border-color: var(--warning); }
.ev-content { flex: 1; min-width: 0; }
.ev-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.ev-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.ev-time { font-size: 11px; color: var(--text-muted); }
.ev-actions { display: flex; gap: 6px; flex-shrink: 0; align-items: center; }
.ev-status { flex-shrink: 0; }
.btn-sm { padding: 4px 10px; font-size: 12px; }

/* Action logs */
.log-list { display: flex; flex-direction: column; gap: 6px; }
.log-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
.log-target { font-weight: 500; }
.log-reason { color: var(--text-muted); flex: 1; }
.log-time { color: var(--text-muted); white-space: nowrap; }

.toast { position: fixed; bottom: 32px; right: 32px; padding: 10px 18px; border-radius: 8px; font-size: 13px; z-index: 9999; box-shadow: var(--shadow-lg); }
.toast-success { background: var(--success-light); border: 1px solid var(--success); color: var(--success); }
.toast-error { background: var(--danger-light); border: 1px solid var(--danger); color: var(--danger); }
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }

@media (max-width: 768px) {
  .overview-row { grid-template-columns: 1fr; }
  .section-head { flex-direction: column; align-items: stretch; }
  .blacklist-add { flex-wrap: wrap; }
  .bl-input { width: 100%; }
  .event-item { flex-direction: column; }
  .ev-actions { width: 100%; }
  .ev-actions .btn { flex: 1; }
  .sessions-grid { grid-template-columns: 1fr; }
}
</style>
