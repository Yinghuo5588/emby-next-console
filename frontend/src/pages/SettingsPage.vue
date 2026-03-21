<template>
 <div class="settings-page">
 <PageHeader title="系统设置" desc="健康状态、配置管理与后台任务" />

 <!-- ① 系统健康区 -->
 <section class="health-section">
 <div class="section-label">系统健康</div>

 <LoadingState v-if="healthLoading && !health" height="80px" />
 <ErrorState
 v-else-if="healthError"
 :message="healthError"
 compact
 @retry="loadHealth"
 />
 <div v-else-if="health" class="health-grid">
 <!-- 整体状态 -->
 <div class="health-card" :class="`health-${health.status}`">
 <div class="health-icon">{{ health.status === 'ok' ? '✓' : '⚠' }}</div>
 <div class="health-info">
 <div class="health-name">整体状态</div>
 <div class="health-val">{{ health.status === 'ok' ? '正常' : '降级' }}</div>
 </div>
 </div>

 <!-- 数据库 -->
 <div class="health-card" :class="`health-${health.db}`">
 <div class="health-icon">{{ health.db === 'ok' ? '✓' : '✗' }}</div>
 <div class="health-info">
 <div class="health-name">数据库</div>
 <div class="health-val">{{ health.db === 'ok' ? '连接正常' : '连接异常' }}</div>
 </div>
 </div>

 <!-- Redis -->
 <div class="health-card" :class="`health-${health.redis}`">
 <div class="health-icon">{{ health.redis === 'ok' ? '✓' : '✗' }}</div>
 <div class="health-info">
 <div class="health-name">Redis</div>
 <div class="health-val">{{ health.redis === 'ok' ? '连接正常' : '连接异常' }}</div>
 </div>
 </div>

 <!-- 版本 -->
 <div v-if="health.version" class="health-card health-neutral">
 <div class="health-icon">◈</div>
 <div class="health-info">
 <div class="health-name">版本</div>
 <div class="health-val">{{ health.version }}</div>
 </div>
 </div>
 </div>
 </section>

 <!-- ② 配置项区 -->
 <section class="settings-section">
 <div class="section-header">
 <div class="section-label">系统配置</div>
 <button
 class="btn btn-ghost refresh-btn"
 :disabled="settingsLoading"
 @click="loadSettings"
 >
 <span :class="{ spinning: settingsLoading }">↻</span>
 刷新
 </button>
 </div>

 <LoadingState v-if="settingsLoading && settings.length === 0" height="200px" />
 <ErrorState
 v-else-if="settingsError"
 :message="settingsError"
 @retry="loadSettings"
 />
 <div v-else-if="settings.length === 0" class="section-empty">
 暂无配置项
 </div>

 <template v-else>
 <!-- 按 group 分组渲染 -->
 <div
 v-for="group in settingGroups"
 :key="group.name"
 class="settings-group"
 >
 <div class="group-label">{{ groupLabel(group.name) }}</div>
 <div class="group-card card">
 <div
 v-for="item in group.items"
 :key="item.setting_key"
 class="setting-row"
 >
 <!-- 左：key + 描述 -->
 <div class="setting-meta">
 <div class="setting-key">{{ item.setting_key }}</div>
 <div v-if="item.description" class="setting-desc">
 {{ item.description }}
 </div>
 </div>

 <!-- 中：值展示 / 编辑输入框 -->
 <div class="setting-value-wrap">
 <template v-if="editingKey === item.setting_key">
 <input
 ref="editInputRef"
 v-model="editingValue"
 class="setting-input"
 @keyup.enter="saveSetting(item.setting_key)"
 @keyup.escape="cancelEdit"
 />
 </template>
 <span v-else class="setting-value">
 {{ displayValue(item.value) }}
 </span>
 </div>

 <!-- 右：操作按钮 -->
 <div class="setting-actions">
 <template v-if="editingKey === item.setting_key">
 <button
 class="btn btn-save"
 :disabled="savingKey === item.setting_key"
 @click="saveSetting(item.setting_key)"
 >
 {{ savingKey === item.setting_key ? '保存中...' : '保存' }}
 </button>
 <button class="btn btn-cancel" @click="cancelEdit">取消</button>
 </template>
 <button
 v-else
 class="btn btn-ghost edit-btn"
 @click="startEdit(item)"
 >
 编辑
 </button>
 </div>
 </div>
 </div>
 </template>
 </section>

 <!-- ③ 后台任务区 -->
 <section class="jobs-section">
 <div class="section-header">
 <div class="section-label">后台任务记录</div>
 <button
 class="btn btn-ghost refresh-btn"
 :disabled="jobsLoading"
 @click="loadJobs"
 >
 <span :class="{ spinning: jobsLoading }">↻</span>
 刷新
 </button>
 </div>

 <div class="card" style="padding: 0;">
 <LoadingState v-if="jobsLoading && jobs.length === 0" height="160px" />
 <ErrorState
 v-else-if="jobsError"
 :message="jobsError"
 compact
 @retry="loadJobs"
 />
 <template v-else>
 <table>
 <thead>
 <tr>
 <th>任务类型</th>
 <th>状态</th>
 <th>开始时间</th>
 <th>结束时间</th>
 <th>耗时</th>
 <th>错误信息</th>
 </tr>
 </thead>
 <tbody>
 <tr v-if="jobs.length === 0">
 <td colspan="6">
 <div class="table-empty">暂无任务记录</div>
 </td>
 </tr>
 <tr v-for="job in jobs" :key="(job as any).job_id ?? Math.random()">
 <td>
 <span class="job-type">{{ (job as any).job_type ?? '—' }}</span>
 </td>
 <td>
 <span class="tag" :class="jobStatusClass((job as any).status)">
 {{ jobStatusLabel((job as any).status) }}
 </span>
 </td>
 <td class="muted time-cell">
 {{ (job as any).started_at ? formatDateTime((job as any).started_at) : '—' }}
 </td>
 <td class="muted time-cell">
 {{ (job as any).finished_at ? formatDateTime((job as any).finished_at) : '—' }}
 </td>
 <td class="muted">
 {{ calcDuration((job as any).started_at, (job as any).finished_at) }}
 </td>
 <td>
 <span
 v-if="(job as any).error_message"
 class="error-msg"
 :title="(job as any).error_message"
 >
 {{ truncate((job as any).error_message, 40) }}
 </span>
 <span v-else class="muted">—</span>
 </td>
 </tr>
 </tbody>
 </table>
 </template>
 </div>
 </section>

 <!-- Toast -->
 <Transition name="toast">
 <div v-if="toast" class="toast" :class="`toast-${toast.type}`">
 {{ toast.message }}
 </div>
 </Transition>
 </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { systemApi, type SettingItem, type HealthResponse } from '@/api/system'

// ── 状态 ─────────────────────────────────────────
const health = ref<HealthResponse | null>(null)
const healthLoading = ref(false)
const healthError = ref<string | null>(null)

const settings = ref<SettingItem[]>([])
const settingsLoading = ref(false)
const settingsError = ref<string | null>(null)

const jobs = ref<unknown[]>([])
const jobsLoading = ref(false)
const jobsError = ref<string | null>(null)

// 编辑状态
const editingKey = ref<string | null>(null)
const editingValue = ref('')
const savingKey = ref<string | null>(null)
const editInputRef = ref<HTMLInputElement | null>(null)

// Toast
interface Toast { message: string; type: 'success' | 'error' }
const toast = ref<Toast | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

// ── 分组计算 ──────────────────────────────────────
const settingGroups = computed(() => {
 const map = new Map<string, SettingItem[]>()
 for (const item of settings.value) {
 const g = item.setting_group ?? 'general'
 if (!map.has(g)) map.set(g, [])
 map.get(g)!.push(item)
 }
 return Array.from(map.entries()).map(([name, items]) => ({ name, items }))
})

// ── 数据加载 ──────────────────────────────────────
async function loadHealth() {
 healthLoading.value = true
 healthError.value = null
 try {
 health.value = await systemApi.health()
 } catch {
 healthError.value = '获取健康状态失败'
 } finally {
 healthLoading.value = false
 }
}

async function loadSettings() {
 settingsLoading.value = true
 settingsError.value = null
 try {
 settings.value = await systemApi.settings()
 } catch {
 settingsError.value = '获取配置项失败'
 } finally {
 settingsLoading.value = false
 }
}

async function loadJobs() {
 jobsLoading.value = true
 jobsError.value = null
 try {
 jobs.value = await systemApi.jobs()
 } catch {
 jobsError.value = '获取任务记录失败'
 } finally {
 jobsLoading.value = false
 }
}

// ── 编辑配置 ──────────────────────────────────────
function startEdit(item: SettingItem) {
 editingKey.value = item.setting_key
 editingValue.value =
 typeof item.value === 'string' ? item.value : JSON.stringify(item.value)
 nextTick(() => {
 editInputRef.value?.focus()
 })
}

function cancelEdit() {
 editingKey.value = null
 editingValue.value = ''
}

async function saveSetting(key: string) {
 savingKey.value = key
 try {
 // 尝试 JSON.parse，失败则按字符串提交
 let parsed: unknown = editingValue.value
 try {
 parsed = JSON.parse(editingValue.value)
 } catch {
 // 保持字符串
 }

 const updated = await systemApi.updateSetting(key, parsed)

 // 本地更新
 const idx = settings.value.findIndex(s => s.setting_key === key)
 if (idx >= 0) settings.value[idx] = updated

 cancelEdit()
 showToast('配置已保存', 'success')
 } catch {
 showToast('保存失败，请重试', 'error')
 } finally {
 savingKey.value = null
 }
}

// ── 工具函数 ──────────────────────────────────────
function displayValue(value: unknown): string {
 if (value === null || value === undefined) return '—'
 if (typeof value === 'string') return value || '（空）'
 return JSON.stringify(value)
}

function groupLabel(key: string): string {
 const map: Record<string, string> = {
 general: '通用设置',
 emby: 'Emby 集成',
 risk: '风控配置',
 notification: '通知配置',
 system: '系统配置',
 }
 return map[key] ?? key
}

function jobStatusClass(s: string) {
 return {
 success: 'tag-green',
 failed: 'tag-red',
 running: 'tag-yellow',
 pending: 'tag-gray',
 }[s] ?? 'tag-gray'
}

function jobStatusLabel(s: string) {
 return {
 success: '成功',
 failed: '失败',
 running: '运行中',
 pending: '等待中',
 }[s] ?? s
}

function formatDateTime(iso: string): string {
 return new Date(iso).toLocaleString('zh-CN', {
 month: '2-digit',
 day: '2-digit',
 hour: '2-digit',
 minute: '2-digit',
 second: '2-digit',
 })
}

function calcDuration(start: string | null, end: string | null): string {
 if (!start || !end) return '—'
 const ms = new Date(end).getTime() - new Date(start).getTime()
 if (ms < 0) return '—'
 if (ms < 1000) return `${ms}ms`
 if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
 return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

function truncate(str: string, len: number): string {
 return str.length > len ? str.slice(0, len) + '…' : str
}

function showToast(message: string, type: Toast['type']) {
 if (toastTimer) clearTimeout(toastTimer)
 toast.value = { message, type }
 toastTimer = setTimeout(() => { toast.value = null }, 2500)
}

// ── 初始化 ────────────────────────────────────────
onMounted(() => {
 Promise.all([loadHealth(), loadSettings(), loadJobs()])
})
</script>

<style scoped>
/* ── 通用分区 ──────────────────────────────────── */
.settings-page {
 display: flex;
 flex-direction: column;
 gap: 28px;
}

.section-label {
 font-size: 13px;
 font-weight: 600;
 color: var(--color-text-muted);
 text-transform: uppercase;
 letter-spacing: 0.06em;
 margin-bottom: 12px;
}

.section-header {
 display: flex;
 align-items: center;
 justify-content: space-between;
 margin-bottom: 12px;
}

.section-header .section-label {
 margin-bottom: 0;
}

.section-empty {
 color: var(--color-text-muted);
 font-size: 13px;
 padding: 24px 0;
 text-align: center;
}

/* ── 健康区 ─────────────────────────────────────── */
.health-grid {
 display: flex;
 gap: 12px;
 flex-wrap: wrap;
}

.health-card {
 display: flex;
 align-items: center;
 gap: 12px;
 padding: 14px 18px;
 border-radius: 10px;
 border: 1px solid var(--color-border);
 background: var(--color-surface);
 min-width: 150px;
 flex: 1;
 transition: border-color 0.2s;
}

.health-ok {
 border-color: rgba(34, 197, 94, 0.35);
 background: rgba(34, 197, 94, 0.04);
}

.health-error {
 border-color: rgba(239, 68, 68, 0.35);
 background: rgba(239, 68, 68, 0.04);
}

.health-degraded {
 border-color: rgba(245, 158, 11, 0.35);
 background: rgba(245, 158, 11, 0.04);
}

.health-neutral {
 border-color: var(--color-border);
}

.health-icon {
 font-size: 18px;
 width: 32px;
 height: 32px;
 border-radius: 8px;
 display: flex;
 align-items: center;
 justify-content: center;
 flex-shrink: 0;
 background: var(--color-surface-2);
}

.health-ok .health-icon { color: var(--color-success); background: rgba(34, 197, 94, 0.1); }
.health-error .health-icon { color: var(--color-danger); background: rgba(239, 68, 68, 0.1); }
.health-degraded .health-icon { color: var(--color-warning); background: rgba(245, 158, 11, 0.1); }
.health-neutral .health-icon { color: var(--color-primary); background: rgba(99, 102, 241, 0.1); }

.health-name {
 font-size: 12px;
 color: var(--color-text-muted);
 margin-bottom: 2px;
}

.health-val {
 font-size: 14px;
 font-weight: 600;
}

.health-ok .health-val { color: var(--color-success); }
.health-error .health-val { color: var(--color-danger); }
.health-degraded .health-val { color: var(--color-warning); }

/* ── 配置区 ─────────────────────────────────────── */
.settings-group {
 margin-bottom: 16px;
}

.settings-group:last-child {
 margin-bottom: 0;
}

.group-label {
 font-size: 12px;
 font-weight: 600;
 color: var(--color-text-muted);
 margin-bottom: 8px;
 padding-left: 2px;
}

.group-card {
 padding: 0;
 overflow: hidden;
}

.setting-row {
 display: flex;
 align-items: center;
 gap: 16px;
 padding: 14px 20px;
 border-bottom: 1px solid var(--color-border);
 transition: background 0.12s;
}

.setting-row:last-child {
 border-bottom: none;
}

.setting-row:hover {
 background: var(--color-surface-2);
}

/* 左列：key + 描述 */
.setting-meta {
 width: 260px;
 flex-shrink: 0;
}

.setting-key {
 font-size: 13px;
 font-weight: 500;
 font-family: 'SF Mono', 'Fira Code', monospace;
 color: var(--color-text);
}

.setting-desc {
 font-size: 12px;
 color: var(--color-text-muted);
 margin-top: 2px;
 line-height: 1.4;
}

/* 中列：值 */
.setting-value-wrap {
 flex: 1;
 min-width: 0;
}

.setting-value {
 font-size: 13px;
 color: var(--color-text-muted);
 font-family: 'SF Mono', 'Fira Code', monospace;
 word-break: break-all;
}

.setting-input {
 width: 100%;
 padding: 7px 10px;
 background: var(--color-surface-2);
 border: 1px solid var(--color-primary);
 border-radius: 6px;
 color: var(--color-text);
 font-size: 13px;
 font-family: 'SF Mono', 'Fira Code', monospace;
 outline: none;
 box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
}

/* 右列：操作按钮 */
.setting-actions {
 display: flex;
 gap: 6px;
 flex-shrink: 0;
 min-width: 100px;
 justify-content: flex-end;
}

.edit-btn {
 padding: 4px 12px;
 font-size: 12px;
}

.btn-save {
 padding: 4px 12px;
 border-radius: 5px;
 font-size: 12px;
 font-weight: 500;
 background: rgba(99, 102, 241, 0.12);
 color: var(--color-primary);
 border: 1px solid rgba(99, 102, 241, 0.35);
 cursor: pointer;
 transition: all 0.15s;
}

.btn-save:hover:not(:disabled) {
 background: rgba(99, 102, 241, 0.22);
}

.btn-save:disabled {
 opacity: 0.45;
 cursor: not-allowed;
}

.btn-cancel {
 padding: 4px 10px;
 border-radius: 5px;
 font-size: 12px;
 background: var(--color-surface-2);
 color: var(--color-text-muted);
 border: 1px solid var(--color-border);
 cursor: pointer;
 transition: all 0.15s;
}

.btn-cancel:hover {
 color: var(--color-text);
 border-color: var(--color-text-muted);
}

/* ── 后台任务区 ──────────────────────────────────── */
.table-empty {
 padding: 40px;
 text-align: center;
 color: var(--color-text-muted);
 font-size: 13px;
}

.job-type {
 font-size: 13px;
 font-weight: 500;
 font-family: 'SF Mono', 'Fira Code', monospace;
}

.time-cell {
 font-size: 12px;
 white-space: nowrap;
}

.muted {
 color: var(--color-text-muted);
 font-size: 13px;
}

.error-msg {
 font-size: 12px;
 color: var(--color-danger);
 cursor: help;
}

/* ── 刷新按钮 ────────────────────────────────────── */
.refresh-btn {
 display: flex;
 align-items: center;
 gap: 5px;
 padding: 4px 10px;
 font-size: 12px;
}

.spinning {
 display: inline-block;
 animation: spin 0.7s linear infinite;
}

@keyframes spin {
 to { transform: rotate(360deg); }
}

/* ── Toast ───────────────────────────────────────── */
.toast {
 position: fixed;
 bottom: 32px;
 right: 32px;
 padding: 10px 18px;
 border-radius: 8px;
 font-size: 13px;
 font-weight: 500;
 z-index: 9999;
 box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
 pointer-events: none;
}

.toast-success {
 background: rgba(34, 197, 94, 0.14);
 border: 1px solid rgba(34, 197, 94, 0.4);
 color: var(--color-success);
}

.toast-error {
 background: rgba(239, 68, 68, 0.14);
 border: 1px solid rgba(239, 68, 68, 0.4);
 color: var(--color-danger);
}

.toast-enter-active,
.toast-leave-active {
 transition: opacity 0.25s, transform 0.25s;
}

.toast-enter-from,
.toast-leave-to {
 opacity: 0;
 transform: translateY(8px);
}
</style>