<template>
 <div class="events-table-wrap card">
 <!-- 首次加载全覆盖 -->
 <div v-if="loading && items.length === 0" class="table-state">
 <LoadingState height="300px" />
 </div>

 <!-- error -->
 <div v-else-if="error" class="table-state">
 <ErrorState :message="error" @retry="emit('retry')" />
 </div>

 <template v-else>
 <!-- 刷新蒙层 -->
 <div v-if="loading" class="refresh-mask" />

 <table>
 <thead>
 <tr>
 <th style="width: 36%;">事件标题</th>
 <th>用户</th>
 <th>类型</th>
 <th>等级</th>
 <th>状态</th>
 <th>检测时间</th>
 <th style="width: 120px;">操作</th>
 </tr>
 </thead>
 <tbody>
 <tr v-if="items.length === 0">
 <td colspan="7">
 <div class="table-empty">暂无匹配事件</div>
 </td>
 </tr>

 <tr
 v-for="ev in items"
 :key="ev.event_id"
 class="event-row"
 :class="{ 'row-high': ev.severity === 'high' && ev.status === 'open' }"
 >
 <!-- 事件标题 -->
 <td>
 <div class="event-title-cell">
 <span
 v-if="ev.severity === 'high' && ev.status === 'open'"
 class="high-dot"
 title="高危"
 />
 <div>
 <div class="event-title">{{ ev.title }}</div>
 <div v-if="ev.description" class="event-desc">{{ ev.description }}</div>
 </div>
 </div>
 </td>

 <!-- 用户 -->
 <td>
 <RouterLink
 v-if="ev.user_id"
 :to="`/users/${ev.user_id}`"
 class="user-link"
 >
 {{ ev.username || ev.user_id }}
 </RouterLink>
 <span v-else class="muted">—</span>
 </td>

 <!-- 类型 -->
 <td>
 <span class="tag tag-gray event-type">{{ ev.event_type }}</span>
 </td>

 <!-- 等级 -->
 <td>
 <span class="tag" :class="severityClass(ev.severity)">
 {{ severityLabel(ev.severity) }}
 </span>
 </td>

 <!-- 状态 -->
 <td>
 <span class="tag" :class="statusClass(ev.status)">
 {{ statusLabel(ev.status) }}
 </span>
 </td>

 <!-- 检测时间 -->
 <td class="muted time-cell">{{ formatDateTime(ev.detected_at) }}</td>

 <!-- 操作 -->
 <td>
 <div v-if="ev.status === 'open'" class="action-btns">
 <button
 class="btn btn-resolve"
 :disabled="actioningId === ev.event_id"
 @click="emit('action', ev.event_id, 'resolve')"
 >
 {{ actioningId === ev.event_id ? '...' : '解决' }}
 </button>
 <button
 class="btn btn-ignore"
 :disabled="actioningId === ev.event_id"
 @click="emit('action', ev.event_id, 'ignore')"
 >
 忽略
 </button>
 </div>
 <span v-else class="muted handled-text">已处理</span>
 </td>
 </tr>
 </tbody>
 </table>
 </template>
 </div>
</template>

<script setup lang="ts">
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import type { RiskEventItem } from '@/api/risk'

defineProps<{
 items: RiskEventItem[]
 loading: boolean
 error: string | null
 actioningId: string | null
}>()

const emit = defineEmits<{
 retry: []
 action: [eventId: string, action: string]
}>()

function severityClass(s: string) {
 return { high: 'tag-red', medium: 'tag-yellow', low: 'tag-green' }[s] ?? 'tag-gray'
}

function severityLabel(s: string) {
 return { high: '高危', medium: '中危', low: '低危' }[s] ?? s
}

function statusClass(s: string) {
 return { open: 'tag-yellow', resolved: 'tag-green', ignored: 'tag-gray' }[s] ?? 'tag-gray'
}

function statusLabel(s: string) {
 return { open: '待处理', resolved: '已解决', ignored: '已忽略' }[s] ?? s
}

function formatDateTime(iso: string): string {
 return new Date(iso).toLocaleString('zh-CN', {
 month: '2-digit',
 day: '2-digit',
 hour: '2-digit',
 minute: '2-digit',
 })
}
</script>

<style scoped>
.events-table-wrap {
 padding: 0;
 position: relative;
 overflow: hidden;
}

.table-state {
 min-height: 300px;
 display: flex;
 align-items: center;
 justify-content: center;
}

.refresh-mask {
 position: absolute;
 inset: 0;
 background: rgba(15, 17, 23, 0.3);
 z-index: 1;
 pointer-events: none;
}

.table-empty {
 padding: 48px;
 text-align: center;
 color: var(--color-text-muted);
 font-size: 13px;
}

/* 高危行背景 */
.row-high td {
 background: rgba(239, 68, 68, 0.04);
}

.row-high:hover td {
 background: rgba(239, 68, 68, 0.08) !important;
}

/* 事件标题列 */
.event-title-cell {
 display: flex;
 align-items: flex-start;
 gap: 8px;
}

.high-dot {
 width: 7px;
 height: 7px;
 border-radius: 50%;
 background: var(--color-danger);
 flex-shrink: 0;
 margin-top: 5px;
 box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
 animation: pulse-red 2s ease-in-out infinite;
}

@keyframes pulse-red {
 0%, 100% { box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2); }
 50% { box-shadow: 0 0 0 5px rgba(239, 68, 68, 0.06); }
}

.event-title {
 font-size: 13px;
 font-weight: 500;
 line-height: 1.4;
}

.event-desc {
 font-size: 12px;
 color: var(--color-text-muted);
 margin-top: 2px;
 white-space: nowrap;
 overflow: hidden;
 text-overflow: ellipsis;
 max-width: 340px;
}

.event-type {
 font-size: 11px;
 white-space: nowrap;
}

/* 用户链接 */
.user-link {
 font-size: 13px;
 color: var(--color-text);
 font-weight: 500;
}

.user-link:hover {
 color: var(--color-primary);
}

/* 时间 */
.time-cell {
 font-size: 12px;
 white-space: nowrap;
}

.muted {
 color: var(--color-text-muted);
 font-size: 13px;
}

/* 操作按钮 */
.action-btns {
 display: flex;
 gap: 6px;
 align-items: center;
}

.btn-resolve {
 padding: 4px 10px;
 border-radius: 5px;
 font-size: 12px;
 font-weight: 500;
 background: rgba(34, 197, 94, 0.12);
 color: var(--color-success);
 border: 1px solid rgba(34, 197, 94, 0.3);
 transition: all 0.15s;
 cursor: pointer;
}

.btn-resolve:hover:not(:disabled) {
 background: rgba(34, 197, 94, 0.22);
}

.btn-ignore {
 padding: 4px 10px;
 border-radius: 5px;
 font-size: 12px;
 background: var(--color-surface-2);
 color: var(--color-text-muted);
 border: 1px solid var(--color-border);
 transition: all 0.15s;
 cursor: pointer;
}

.btn-ignore:hover:not(:disabled) {
 color: var(--color-text);
 border-color: var(--color-text-muted);
}

.btn-resolve:disabled,
.btn-ignore:disabled {
 opacity: 0.4;
 cursor: not-allowed;
}

.handled-text {
 font-size: 12px;
 font-style: italic;
}

/* 通用行 hover */
.event-row:hover td {
 background: var(--color-surface-2);
}
</style>