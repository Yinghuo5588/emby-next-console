<template>
  <div class="ctrl-page">
    <PageHeader title="管控中心" desc="并发管控 · 客户端拦截 · 事件处置">
      <template #actions>
        <n-button quaternary size="small" :loading="scanning" @click="handleScan">扫描</n-button>
        <n-button quaternary size="small" type="warning" :loading="sweeping" @click="handleSweep">扫荡</n-button>
        <n-button quaternary size="small" @click="loadAll">刷新</n-button>
      </template>
    </PageHeader>

    <!-- 概览 -->
    <div class="overview-row">
      <StatCard label="待处理" :value="summary?.open_count ?? 0" :danger="(summary?.open_count ?? 0) > 0" />
      <StatCard label="高危" :value="summary?.high_count ?? 0" :danger="(summary?.high_count ?? 0) > 0" />
      <StatCard label="播放中" :value="liveSessions.length" />
      <StatCard label="黑名单" :value="blacklist.length" />
    </div>

    <!-- 实时播放 -->
    <div class="section-card">
      <div class="section-head">
        <span class="section-title">🔴 实时播放</span>
        <n-button text size="tiny" @click="loadSessions">刷新</n-button>
      </div>
      <LoadingState v-if="sessionsLoading" compact />
      <n-empty v-else-if="liveSessions.length === 0" description="暂无播放" />
      <div v-else class="session-list">
        <div v-for="s in liveSessions" :key="s.Id" class="session-card">
          <div class="sc-top">
            <span class="sc-user">{{ s.UserName || '未知' }}</span>
            <n-tag v-if="s.Client" size="tiny" type="info">{{ s.Client }}</n-tag>
          </div>
          <div class="sc-media">{{ s.NowPlayingItem?.Name || '-' }}</div>
          <div class="sc-actions">
            <n-button size="tiny" type="error" :loading="kicking === s.Id" @click="doKick(s.Id, s.DeviceId || '', 'soft')">停止</n-button>
            <n-button size="tiny" type="error" quaternary :loading="kicking === s.Id+'h'" @click="doKick(s.Id, s.DeviceId || '', 'hard')">强踢</n-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 并发状态 -->
    <div class="section-card">
      <div class="section-head">
        <span class="section-title">📊 并发状态</span>
        <n-button text size="tiny" @click="loadConcurrent">刷新</n-button>
      </div>
      <LoadingState v-if="concurrentLoading" compact />
      <n-empty v-else-if="concurrent.length === 0" description="无活跃用户" />
      <div v-else class="cc-list">
        <div v-for="u in concurrent" :key="u.user_id" class="cc-card" :class="{ exceeded: u.exceeded }">
          <div class="cc-top">
            <span class="cc-name">{{ u.user_name || u.user_id }}</span>
            <n-tag :type="u.exceeded ? 'error' : 'success'" size="tiny">{{ u.current }}/{{ u.max }}</n-tag>
          </div>
          <div v-for="sess in u.sessions" :key="sess.session_id" class="cc-sess">
            <span class="cc-client">{{ sess.client }}</span>
            <span class="cc-title">{{ sess.title }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 黑名单 -->
    <div class="section-card">
      <div class="section-head"><span class="section-title">🚫 客户端黑名单</span></div>
      <div class="bl-add">
        <n-input v-model:value="newItem" placeholder="客户端名称" size="small" @keyup.enter="addBl" />
        <n-button type="primary" size="small" :disabled="!newItem.trim()" @click="addBl">添加</n-button>
      </div>
      <n-empty v-if="blacklist.length === 0" description="空" />
      <div v-else class="bl-tags">
        <n-tag v-for="item in blacklist" :key="item" closable type="warning" size="small" @close="removeBl(item)">{{ item }}</n-tag>
      </div>
    </div>

    <!-- 风控事件 -->
    <div class="section-card">
      <div class="section-head">
        <span class="section-title">⚠️ 风控事件</span>
        <div class="filter-pills">
          <button v-for="s in ['', 'open', 'resolved', 'ignored']" :key="s" class="pill" :class="{ active: evFilter.status === s }" @click="evFilter.status = s; loadEvents()">{{ sLabel(s) }}</button>
        </div>
      </div>
      <LoadingState v-if="evLoading && events.length === 0" />
      <n-empty v-else-if="events.length === 0" description="系统正常 ✅" />
      <div v-else class="ev-list">
        <div v-for="ev in events" :key="ev.event_id" class="ev-item" :class="{ 'ev-high': ev.severity === 'high' && ev.status === 'open', 'ev-open': ev.status === 'open' }">
          <div class="ev-main">
            <div class="ev-title"><n-tag :type="svType(ev.severity)" size="tiny">{{ svLabel(ev.severity) }}</n-tag> <span>{{ ev.title }}</span></div>
            <div class="ev-desc">{{ ev.description || '-' }}</div>
            <div class="ev-time">{{ fmtTime(ev.detected_at) }}</div>
          </div>
          <div v-if="ev.status === 'open'" class="ev-acts">
            <n-button size="tiny" type="primary" :loading="acting === ev.event_id" @click="doAction(ev.event_id, 'resolve')">解决</n-button>
            <n-button size="tiny" quaternary :loading="acting === ev.event_id" @click="doAction(ev.event_id, 'ignore')">忽略</n-button>
          </div>
          <div v-else class="ev-status">
            <n-tag :type="ev.status === 'resolved' ? 'success' : 'default'" size="small">{{ ev.status === 'resolved' ? '已解决' : '已忽略' }}</n-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 执法日志 -->
    <div class="section-card">
      <div class="section-head"><span class="section-title">📋 执法日志</span></div>
      <n-empty v-if="logs.length === 0" description="暂无记录" />
      <div v-else class="log-list">
        <div v-for="l in logs" :key="l.id" class="log-item">
          <n-tag :type="logType(l.action)" size="tiny">{{ logLabel(l.action) }}</n-tag>
          <span class="log-target">{{ l.target }}</span>
          <span class="log-reason">{{ l.reason }}</span>
          <span class="log-time">{{ fmtTime(l.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { NButton, NTag, NInput, NEmpty, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { riskApi } from '@/api/risk'
import type { RiskActionLog, ConcurrentItem } from '@/api/risk'
import apiClient from '@/api/client'

const msg = useMessage()
const summary = ref<any>(null)
const events = ref<any[]>([])
const evLoading = ref(false)
const acting = ref<string | null>(null)
const kicking = ref<string | null>(null)
const scanning = ref(false)
const sweeping = ref(false)
const blacklist = ref<string[]>([])
const newItem = ref('')
const evFilter = reactive({ status: 'open' })
const liveSessions = ref<any[]>([])
const sessionsLoading = ref(false)
const logs = ref<RiskActionLog[]>([])
const concurrent = ref<ConcurrentItem[]>([])
const concurrentLoading = ref(false)

async function loadSummary() { try { summary.value = (await riskApi.summary()).data } catch {} }
async function loadEvents() {
  evLoading.value = true
  try { const r = await riskApi.events(1, 50, evFilter.status || undefined); events.value = r.data?.items ?? [] }
  catch { events.value = [] }
  finally { evLoading.value = false }
}
async function loadBlacklist() { try { const r = await riskApi.blacklist(); blacklist.value = r.data ?? [] } catch { blacklist.value = [] } }
async function loadSessions() {
  sessionsLoading.value = true
  try { const r = await apiClient.get('/system/sessions'); liveSessions.value = (r.data?.data ?? []).filter((s: any) => s.NowPlayingItem) }
  catch { liveSessions.value = [] }
  finally { sessionsLoading.value = false }
}
async function loadConcurrent() {
  concurrentLoading.value = true
  try { const r = await riskApi.concurrentStatus(); concurrent.value = r.data ?? [] }
  catch { concurrent.value = [] }
  finally { concurrentLoading.value = false }
}
async function loadLogs() { try { const r = await riskApi.logs(1, 20); logs.value = r.data?.items ?? [] } catch { logs.value = [] } }

async function doKick(sessionId: string, deviceId: string, level: string) {
  kicking.value = level === 'hard' ? sessionId + 'h' : sessionId
  try {
    const r = await riskApi.kick(sessionId, deviceId, level)
    if (r.data?.success) { msg.success(level === 'hard' ? '已强制踢出' : '已停止播放'); await loadAll() }
    else { msg.error('失败') }
  } catch { msg.error('失败') }
  finally { kicking.value = null }
}

async function addBl() {
  const n = newItem.value.trim(); if (!n) return
  try { const r = await riskApi.addBlacklist(n); blacklist.value = r.data ?? [...blacklist.value, n.toLowerCase()]; newItem.value = ''; msg.success(`已添加 ${n}`) }
  catch { msg.error('失败') }
}
async function removeBl(n: string) {
  try { const r = await riskApi.removeBlacklist(n); blacklist.value = r.data ?? blacklist.value.filter(x => x !== n); msg.success(`已移除`) }
  catch { msg.error('失败') }
}
async function doAction(id: string, action: string) {
  acting.value = id
  try { await riskApi.action(id, action as any); msg.success(action === 'resolve' ? '已解决' : '已忽略'); await loadAll() }
  catch { msg.error('失败') }
  finally { acting.value = null }
}
async function handleScan() {
  scanning.value = true
  try { const r = await riskApi.scan(); const d = r.data; if (d) msg.success(`扫描: 拦截${d.blocked?.length||0} 越界${d.violations?.length||0}`); await loadAll() }
  catch { msg.error('失败') }
  finally { scanning.value = false }
}
async function handleSweep() {
  sweeping.value = true
  try { const r = await riskApi.sweep(); msg.success(r.data?.deleted_count ? `删除${r.data.deleted_count}个设备` : '无匹配'); await loadAll() }
  catch { msg.error('失败') }
  finally { sweeping.value = false }
}
async function loadAll() { await Promise.all([loadSummary(), loadEvents(), loadBlacklist(), loadSessions(), loadLogs(), loadConcurrent()]) }

function svType(s: string) { return ({ high: 'error', medium: 'warning', low: 'info' })[s] as any ?? 'default' }
function svLabel(s: string) { return ({ high: '高危', medium: '中危', low: '低危' })[s] ?? s }
function sLabel(s: string) { return ({ '': '全部', open: '待处理', resolved: '已解决', ignored: '已忽略' })[s] ?? s }
function logType(a: string) { return ({ kick: 'error', ban: 'error', unban: 'success', device_sweep: 'warning' })[a] as any ?? 'default' }
function logLabel(a: string) { return ({ kick: '踢出', ban: '封禁', unban: '解封', device_sweep: '设备清除' })[a] ?? a }
function fmtTime(iso: string) {
  const d = new Date(iso), diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadAll)
</script>

<style scoped>
.ctrl-page { padding-bottom: 24px; }
.overview-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; margin-bottom: 14px; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; gap: 8px; flex-wrap: wrap; }
.section-title { font-size: 14px; font-weight: 600; }
.session-list { display: flex; flex-direction: column; gap: 8px; }
.session-card { padding: 10px; border: 1px solid var(--border); border-radius: var(--radius); }
.sc-top { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.sc-user { font-weight: 600; font-size: 13px; }
.sc-media { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sc-actions { display: flex; gap: 6px; }
.cc-list { display: flex; flex-direction: column; gap: 8px; }
.cc-card { padding: 10px; border: 1px solid var(--border); border-radius: var(--radius); }
.cc-card.exceeded { border-color: var(--danger); background: rgba(255,59,48,0.04); }
.cc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.cc-name { font-weight: 600; font-size: 13px; }
.cc-sess { font-size: 12px; color: var(--text-muted); padding: 2px 0; display: flex; gap: 6px; }
.cc-client { color: var(--brand); font-weight: 500; white-space: nowrap; }
.cc-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bl-add { display: flex; gap: 8px; margin-bottom: 10px; }
.bl-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.filter-pills { display: flex; gap: 4px; }
.pill { border: none; background: var(--bg); color: var(--text-muted); font-size: 12px; padding: 4px 10px; border-radius: 20px; cursor: pointer; font-family: inherit; }
.pill.active { background: var(--brand); color: #fff; }
.ev-list { display: flex; flex-direction: column; gap: 8px; }
.ev-item { display: flex; gap: 10px; padding: 10px; border-radius: var(--radius); border: 1px solid var(--border); }
.ev-item.ev-high.ev-open { border-color: var(--danger); background: rgba(208,48,80,0.05); }
.ev-item.ev-open:not(.ev-high) { border-color: var(--warning); }
.ev-main { flex: 1; min-width: 0; }
.ev-title { font-size: 13px; font-weight: 600; margin-bottom: 3px; display: flex; align-items: center; gap: 6px; }
.ev-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 3px; }
.ev-time { font-size: 11px; color: var(--text-muted); }
.ev-acts { display: flex; gap: 4px; flex-direction: column; flex-shrink: 0; }
.ev-status { flex-shrink: 0; }
.log-list { display: flex; flex-direction: column; gap: 6px; }
.log-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid var(--border); font-size: 12px; flex-wrap: wrap; }
.log-item:last-child { border-bottom: none; }
.log-target { font-weight: 500; }
.log-reason { color: var(--text-muted); flex: 1; min-width: 0; }
.log-time { color: var(--text-muted); white-space: nowrap; font-size: 11px; }
@media (min-width: 769px) {
  .overview-row { grid-template-columns: repeat(4, 1fr); }
  .ev-item { flex-direction: row; }
  .ev-acts { flex-direction: row; }
}
</style>
