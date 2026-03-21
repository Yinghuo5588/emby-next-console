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

    <!-- 并发限额设置 -->
    <section class="card" style="margin-bottom: 16px;">
      <div class="section-head">
        <span class="section-title">⚙️ 默认并发限额</span>
      </div>
      <div class="limit-row">
        <span class="limit-label">每用户最大同时播放数</span>
        <div class="limit-controls">
          <button class="btn btn-sm" :disabled="concurrentLimit <= 1" @click="updateConcurrentLimit(concurrentLimit - 1)">−</button>
          <span class="limit-num">{{ concurrentLimit }}</span>
          <button class="btn btn-sm" :disabled="concurrentLimit >= 10" @click="updateConcurrentLimit(concurrentLimit + 1)">+</button>
        </div>
      </div>
      <p class="limit-hint">天眼系统每 60 秒扫描一次，超过限额的用户将自动触发风控事件</p>
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
      <p class="limit-hint" style="margin-top: 8px;">命中黑名单的客户端会被自动踢出并删除设备，webhook 实时拦截</p>
    </section>

    <!-- 风控事件列表 -->
    <section class="card">
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
          </div>
          <div v-else class="ev-status">
            <span class="tag" :class="ev.status === 'resolved' ? 'tag-green' : 'tag-gray'">{{ ev.status === 'resolved' ? '已解决' : '已忽略' }}</span>
          </div>
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
import { systemApi } from '@/api/system'

const summary = ref<any>(null)
const events = ref<any[]>([])
const eventsLoading = ref(false)
const loading = ref(false)
const actioningId = ref<string | null>(null)
const blacklist = ref<string[]>([])
const newBlacklistItem = ref('')
const concurrentLimit = ref(2)
const eventFilter = reactive({ status: 'open' })
const toast = ref<{ message: string; type: string } | null>(null)

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

async function updateConcurrentLimit(val: number) {
  concurrentLimit.value = val
  // TODO: 保存到后端 system settings
  showToast(`默认并发限额已设为 ${val}`, 'success')
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

async function loadAll() { await Promise.all([loadSummary(), loadEvents(), loadBlacklist()]) }

function severityTag(s: string) { return { high: 'tag-red', medium: 'tag-yellow', low: 'tag-blue' }[s] ?? 'tag-gray' }
function severityLabel(s: string) { return { high: '高危', medium: '中危', low: '低危' }[s] ?? s }
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

.limit-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; }
.limit-label { font-size: 13px; color: var(--text-soft); }
.limit-controls { display: flex; align-items: center; gap: 12px; }
.limit-num { font-size: 24px; font-weight: 700; min-width: 40px; text-align: center; }
.limit-hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

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
.ev-actions { display: flex; gap: 6px; flex-shrink: 0; }
.ev-status { flex-shrink: 0; }
.btn-sm { padding: 4px 10px; font-size: 12px; }

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
}
</style>
