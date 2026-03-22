<template>
  <div>
    <PageHeader title="风控中心" desc="并发越界检测 · 违规客户端拦截 · 异常事件处置">
      <template #actions>
        <n-button quaternary size="small" :loading="loading" @click="loadAll">刷新</n-button>
      </template>
    </PageHeader>

    <!-- 概览卡片 -->
    <div class="overview-row">
      <StatCard label="待处理事件" :value="summary?.open_count ?? 0" :danger="(summary?.open_count ?? 0) > 0" />
      <StatCard label="高危事件" :value="summary?.high_count ?? 0" :danger="(summary?.high_count ?? 0) > 0" />
      <StatCard label="黑名单客户端" :value="blacklist.length" />
    </div>

    <!-- 实时会话（可踢出） -->
    <n-card title="🔴 实时播放会话" size="small" style="margin-bottom: 16px;">
      <template #header-extra>
        <n-button text size="small" @click="loadSessions">刷新</n-button>
      </template>
      <LoadingState v-if="sessionsLoading" compact />
      <n-empty v-else-if="liveSessions.length === 0" description="暂无播放会话" />
      <div v-else class="sessions-grid">
        <div v-for="s in liveSessions" :key="s.Id" class="session-card">
          <div class="sc-header">
            <span class="sc-user">{{ s.UserName || '未知' }}</span>
            <n-tag v-if="s.Client" size="tiny" type="info">{{ s.Client }}</n-tag>
          </div>
          <div class="sc-media">{{ s.NowPlayingItem?.Name || '未知内容' }}</div>
          <n-button size="tiny" type="error" :loading="kickingId === s.Id" @click="doKick(s.Id, s.UserName)">
            踢出播放
          </n-button>
        </div>
      </div>
    </n-card>

    <!-- 客户端黑名单 -->
    <n-card title="🚫 客户端黑名单" size="small" style="margin-bottom: 16px;">
      <template #header-extra>
        <n-input-group size="small" style="width: 240px;">
          <n-input v-model:value="newBlacklistItem" placeholder="输入客户端名称" @keyup.enter="addToBlacklist" />
          <n-button type="primary" :disabled="!newBlacklistItem.trim()" @click="addToBlacklist">添加</n-button>
        </n-input-group>
      </template>
      <n-empty v-if="blacklist.length === 0" description="黑名单为空" />
      <n-space v-else size="small" wrap>
        <n-tag v-for="item in blacklist" :key="item" closable type="warning" size="small" @close="removeFromBlacklist(item)">
          {{ item }}
        </n-tag>
      </n-space>
    </n-card>

    <!-- 风控事件列表 -->
    <n-card title="📋 风控事件" size="small" style="margin-bottom: 16px;">
      <template #header-extra>
        <n-button-group size="small">
          <n-button v-for="s in ['', 'open', 'resolved', 'ignored']" :key="s" :type="eventFilter.status === s ? 'primary' : 'default'" @click="eventFilter.status = s; loadEvents()">
            {{ statusLabel(s) }}
          </n-button>
        </n-button-group>
      </template>

      <LoadingState v-if="eventsLoading && events.length === 0" />
      <n-empty v-else-if="events.length === 0" description="系统正常运行中 ✅" />
      <div v-else class="events-list">
        <div v-for="ev in events" :key="ev.event_id" class="event-item" :class="{ 'event-high': ev.severity === 'high' && ev.status === 'open', 'event-open': ev.status === 'open' }">
          <div class="ev-content">
            <div class="ev-title">
              <n-tag :type="severityType(ev.severity)" size="tiny">{{ severityLabel(ev.severity) }}</n-tag>
              {{ ev.title }}
            </div>
            <div class="ev-desc">{{ ev.description || '—' }}</div>
            <div class="ev-time">{{ formatTime(ev.detected_at) }}</div>
          </div>
          <div v-if="ev.status === 'open'" class="ev-actions">
            <n-button size="tiny" type="primary" :loading="actioningId === ev.event_id" @click="handleAction(ev.event_id, 'resolve')">解决</n-button>
            <n-button size="tiny" quaternary :loading="actioningId === ev.event_id" @click="handleAction(ev.event_id, 'ignore')">忽略</n-button>
            <n-button v-if="ev.user_id" size="tiny" type="error" :loading="banningId === ev.user_id" @click="doBan(ev.user_id, ev.title)">封禁</n-button>
          </div>
          <div v-else class="ev-status">
            <n-tag :type="ev.status === 'resolved' ? 'success' : 'default'" size="small">{{ ev.status === 'resolved' ? '已解决' : '已忽略' }}</n-tag>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 执法日志 -->
    <n-card title="📝 执法日志" size="small">
      <n-empty v-if="actionLogs.length === 0" description="暂无执法记录" />
      <div v-else class="log-list">
        <div v-for="log in actionLogs" :key="log.id" class="log-item">
          <n-tag :type="logType(log.action)" size="tiny">{{ logLabel(log.action) }}</n-tag>
          <span class="log-target">{{ log.target }}</span>
          <span class="log-reason">{{ log.reason }}</span>
          <span class="log-time">{{ formatTime(log.created_at) }}</span>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { NCard, NButton, NButtonGroup, NTag, NInput, NInputGroup, NSpace, NEmpty, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { riskApi } from '@/api/risk'
import type { RiskActionLog } from '@/api/risk'
import { systemApi } from '@/api/system'
import apiClient from '@/api/client'

const msg = useMessage()

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
const liveSessions = ref<any[]>([])
const sessionsLoading = ref(false)
const actionLogs = ref<RiskActionLog[]>([])

async function loadSummary() { loading.value = true; try { summary.value = (await riskApi.summary()).data } finally { loading.value = false } }
async function loadEvents() { eventsLoading.value = true; try { const res = await riskApi.events(1, 50, eventFilter.status || undefined); events.value = res.data?.items ?? [] } catch { events.value = [] } finally { eventsLoading.value = false } }
async function loadBlacklist() { try { const res = await systemApi.clientBlacklist(); blacklist.value = res.data ?? [] } catch { blacklist.value = [] } }
async function loadSessions() { sessionsLoading.value = true; try { const res = await apiClient.get('/system/sessions'); liveSessions.value = (res.data?.data ?? []).filter((s: any) => s.NowPlayingItem) } catch { liveSessions.value = [] } finally { sessionsLoading.value = false } }
async function loadActionLogs() { try { const res = await riskApi.logs(1, 20); actionLogs.value = res.data?.items ?? [] } catch { actionLogs.value = [] } }

async function doKick(sessionId: string, userName: string) {
  kickingId.value = sessionId
  try { const res = await riskApi.kick(sessionId); if (res.data?.success) { msg.success(`已踢出 ${userName || '会话'}`); await loadSessions(); await loadActionLogs() } else { msg.error('踢出失败') } } catch { msg.error('踢出失败') } finally { kickingId.value = null }
}
async function doBan(userId: string, title: string) {
  banningId.value = userId
  try { const res = await riskApi.ban(userId); if (res.data?.success) { msg.success('已封禁用户'); await loadAll() } else { msg.error('封禁失败') } } catch { msg.error('封禁失败') } finally { banningId.value = null }
}
async function addToBlacklist() { const name = newBlacklistItem.value.trim(); if (!name) return; try { await systemApi.addClientBlacklist(name); blacklist.value.push(name); newBlacklistItem.value = ''; msg.success(`已添加 ${name}`) } catch { msg.error('添加失败') } }
async function removeFromBlacklist(name: string) { try { await systemApi.removeClientBlacklist(name); blacklist.value = blacklist.value.filter(x => x !== name); msg.success(`已移除 ${name}`) } catch { msg.error('移除失败') } }
async function handleAction(id: string, action: string) { actioningId.value = id; try { await riskApi.action(id, action as 'resolve' | 'ignore'); msg.success(action === 'resolve' ? '已解决' : '已忽略'); await loadAll() } catch { msg.error('操作失败') } finally { actioningId.value = null } }
async function loadAll() { await Promise.all([loadSummary(), loadEvents(), loadBlacklist(), loadSessions(), loadActionLogs()]) }

function severityType(s: string) { return { high: 'error', medium: 'warning', low: 'info' }[s] as any ?? 'default' }
function severityLabel(s: string) { return { high: '高危', medium: '中危', low: '低危' }[s] ?? s }
function statusLabel(s: string) { return { '': '全部', open: '待处理', resolved: '已解决', ignored: '已忽略' }[s] ?? s }
function logType(a: string) { return { kick: 'error', ban: 'error', unban: 'success' }[a] as any ?? 'default' }
function logLabel(a: string) { return { kick: '踢出', ban: '封禁', unban: '解封' }[a] ?? a }
function formatTime(iso: string) { const d = new Date(iso); const diff = Date.now() - d.getTime(); if (diff < 60000) return '刚刚'; if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`; if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`; return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }

onMounted(loadAll)
</script>

<style scoped>
.overview-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 16px; }
.sessions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; }
.session-card { display: flex; flex-direction: column; gap: 6px; padding: 10px; border: 1px solid var(--border); border-radius: var(--radius); }
.sc-header { display: flex; align-items: center; gap: 6px; }
.sc-user { font-weight: 600; font-size: 13px; }
.sc-media { font-size: 12px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.events-list { display: flex; flex-direction: column; gap: 8px; }
.event-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: var(--radius); border: 1px solid var(--border); }
.event-item.event-open.event-high { border-color: var(--danger); background: rgba(208,48,80,0.05); }
.event-item.event-open:not(.event-high) { border-color: var(--warning); }
.ev-content { flex: 1; min-width: 0; }
.ev-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.ev-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.ev-time { font-size: 11px; color: var(--text-muted); }
.ev-actions { display: flex; gap: 6px; flex-shrink: 0; }
.ev-status { flex-shrink: 0; }
.log-list { display: flex; flex-direction: column; gap: 6px; }
.log-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
.log-item:last-child { border-bottom: none; }
.log-target { font-weight: 500; }
.log-reason { color: var(--text-muted); flex: 1; }
.log-time { color: var(--text-muted); white-space: nowrap; }
@media (max-width: 768px) { .overview-row { grid-template-columns: 1fr; } .sessions-grid { grid-template-columns: 1fr; } .event-item { flex-direction: column; } }
</style>
