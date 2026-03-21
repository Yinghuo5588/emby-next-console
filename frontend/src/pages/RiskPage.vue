<template>
 <div class="risk-page">
 <!-- 页头 -->
 <PageHeader title="风控" desc="异常事件检测与处置">
 <template #actions>
 <button
 class="btn btn-ghost"
 :disabled="summaryLoading || eventsLoading"
 @click="loadAll"
 >
 <span :class="{ spinning: summaryLoading || eventsLoading }">↻</span>
 刷新
 </button>
 </template>
 </PageHeader>

 <!-- ① 摘要卡片 -->
 <section class="summary-row">
 <template v-if="summaryLoading && !summary">
 <div v-for="i in 2" :key="i" class="stat-card card skeleton-card" />
 </template>
 <template v-else-if="summary">
 <!-- 待处理 -->
 <div
 class="card summary-card"
 :class="{ 'card-warn': summary.open_count > 0 }"
 >
 <div class="summary-label">待处理事件</div>
 <div class="summary-num" :class="summary.open_count > 0 ? 'num-warn' : 'num-ok'">
 {{ summary.open_count }}
 </div>
 <div class="summary-hint">
 <span v-if="summary.open_count > 0" class="hint-warn">需要处置</span>
 <span v-else class="hint-ok">✓ 无待处理</span>
 </div>
 </div>

 <!-- 高危 -->
 <div
 class="card summary-card"
 :class="{ 'card-danger': summary.high_count > 0 }"
 >
 <div class="summary-label">高危事件</div>
 <div class="summary-num" :class="summary.high_count > 0 ? 'num-danger' : 'num-ok'">
 {{ summary.high_count }}
 </div>
 <div class="summary-hint">
 <span v-if="summary.high_count > 0" class="hint-danger">⚠ 需优先处置</span>
 <span v-else class="hint-ok">✓ 无高危</span>
 </div>
 </div>
 </template>
 </section>

 <!-- 高危提示横幅（有高危且未全部处理时显示） -->
 <div v-if="summary && summary.high_count > 0" class="danger-banner">
 <span class="banner-icon">🔴</span>
 当前有 <strong>{{ summary.high_count }}</strong> 个高危风险事件待处理，请尽快排查并处置。
 </div>

 <!-- ② 筛选栏 -->
 <RiskFilterBar
 v-model="filters"
 style="margin-bottom: 16px;"
 @update:model-value="handleFilterChange"
 />

 <!-- ③ 事件列表 -->
 <RiskEventsTable
 :items="events"
 :loading="eventsLoading"
 :error="eventsError"
 :actioning-id="actioningId"
 @retry="loadEvents"
 @action="handleAction"
 />

 <!-- 操作反馈 Toast -->
 <Transition name="toast">
 <div v-if="toast" class="toast" :class="`toast-${toast.type}`">
 {{ toast.message }}
 </div>
 </Transition>
 </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RiskFilterBar, { type RiskFilterValues } from '@/components/risk/RiskFilterBar.vue'
import RiskEventsTable from '@/components/risk/RiskEventsTable.vue'
import { riskApi, type RiskSummary, type RiskEventItem } from '@/api/risk'

// ── 状态 ─────────────────────────────────────────
const summary = ref<RiskSummary | null>(null)
const summaryLoading = ref(false)

const events = ref<RiskEventItem[]>([])
const eventsLoading = ref(false)
const eventsError = ref<string | null>(null)

const actioningId = ref<string | null>(null)

const filters = reactive<RiskFilterValues>({
 status: 'open', // 默认展示待处理
 severity: '',
})

interface Toast { message: string; type: 'success' | 'error' }
const toast = ref<Toast | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

// ── 筛选变化监听 ──────────────────────────────────
watch(
 () => [filters.status, filters.severity],
 () => loadEvents(),
)

// ── 数据加载 ──────────────────────────────────────
async function loadSummary() {
 summaryLoading.value = true
 try {
 summary.value = await riskApi.summary()
 } finally {
 summaryLoading.value = false
 }
}

async function loadEvents() {
 eventsLoading.value = true
 eventsError.value = null
 try {
 const res = await riskApi.events(
 1,
 50,
 filters.status || undefined,
 filters.severity || undefined,
 )
 events.value = res.items
 } catch {
 eventsError.value = '获取风险事件列表失败，请重试'
 } finally {
 eventsLoading.value = false
 }
}

async function loadAll() {
 await Promise.all([loadSummary(), loadEvents()])
}

// ── 操作处理 ──────────────────────────────────────
async function handleAction(eventId: string, action: string) {
 actioningId.value = eventId
 try {
 await riskApi.action(eventId, action)
 showToast(action === 'resolve' ? '事件已标记为已解决' : '事件已忽略', 'success')
 // 操作成功后刷新 summary + 列表
 await loadAll()
 } catch {
 showToast('操作失败，请重试', 'error')
 } finally {
 actioningId.value = null
 }
}

function handleFilterChange(val: RiskFilterValues) {
 Object.assign(filters, val)
}

// ── Toast ─────────────────────────────────────────
function showToast(message: string, type: Toast['type']) {
 if (toastTimer) clearTimeout(toastTimer)
 toast.value = { message, type }
 toastTimer = setTimeout(() => { toast.value = null }, 2800)
}

// ── 初始化 ────────────────────────────────────────
onMounted(loadAll)
</script>

<style scoped>
/* ── 摘要卡片 ──────────────────────────────────── */
.summary-row {
 display: flex;
 gap: 14px;
 margin-bottom: 16px;
}

.skeleton-card {
 width: 180px;
 height: 96px;
 background: linear-gradient(
 90deg,
 var(--color-surface-2) 25%,
 var(--color-border) 50%,
 var(--color-surface-2) 75%
 );
 background-size: 200% 100%;
 animation: shimmer 1.4s infinite;
 border-radius: 10px;
}

@keyframes shimmer {
 to { background-position: -200% 0; }
}

.summary-card {
 min-width: 170px;
 padding: 16px 20px;
 transition: border-color 0.2s;
}

.card-warn {
 border-color: rgba(245, 158, 11, 0.45);
}

.card-danger {
 border-color: rgba(239, 68, 68, 0.45);
}

.summary-label {
 font-size: 12px;
 color: var(--color-text-muted);
 margin-bottom: 6px;
}

.summary-num {
 font-size: 36px;
 font-weight: 700;
 line-height: 1;
 margin-bottom: 6px;
}

.num-ok { color: var(--color-text); }
.num-warn { color: var(--color-warning); }
.num-danger { color: var(--color-danger); }

.summary-hint {
 font-size: 12px;
}

.hint-ok { color: var(--color-success); }
.hint-warn { color: var(--color-warning); }
.hint-danger { color: var(--color-danger); }

/* ── 高危横幅 ────────────────────────────────────── */
.danger-banner {
 display: flex;
 align-items: center;
 gap: 8px;
 padding: 10px 16px;
 background: rgba(239, 68, 68, 0.08);
 border: 1px solid rgba(239, 68, 68, 0.25);
 border-radius: 8px;
 font-size: 13px;
 color: var(--color-danger);
 margin-bottom: 16px;
}

.banner-icon {
 font-size: 15px;
 flex-shrink: 0;
}

.danger-banner strong {
 font-weight: 700;
}

/* ── 刷新按钮 ────────────────────────────────────── */
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
 background: rgba(34, 197, 94, 0.15);
 border: 1px solid rgba(34, 197, 94, 0.4);
 color: var(--color-success);
}

.toast-error {
 background: rgba(239, 68, 68, 0.15);
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