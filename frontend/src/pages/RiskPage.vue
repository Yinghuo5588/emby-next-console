<template>
  <div>
    <PageHeader title="风控" desc="异常事件检测与处置">
      <template #actions><button class="btn btn-ghost" :disabled="loading" @click="loadAll">刷新</button></template>
    </PageHeader>

    <section class="summary-row">
      <div class="card summary-card" :class="{ 'card-warn': summary?.open_count > 0 }">
        <div class="summary-label">待处理</div>
        <div class="summary-num" :class="(summary?.open_count ?? 0) > 0 ? 'num-warn' : ''">{{ summary?.open_count ?? '—' }}</div>
      </div>
      <div class="card summary-card" :class="{ 'card-danger': summary?.high_count > 0 }">
        <div class="summary-label">高危事件</div>
        <div class="summary-num" :class="(summary?.high_count ?? 0) > 0 ? 'num-danger' : ''">{{ summary?.high_count ?? '—' }}</div>
      </div>
    </section>

    <div v-if="summary?.high_count > 0" class="danger-banner">当前有 {{ summary.high_count }} 个高危事件待处理</div>

    <RiskFilterBar v-model="filters" style="margin-bottom: 12px" @update:model-value="loadEvents" />
    <RiskEventsTable :items="events" :loading="eventsLoading" :error="eventsError" :actioning-id="actioningId" @retry="loadEvents" @action="handleAction" />

    <Transition name="toast"><div v-if="toast" class="toast" :class="`toast-${toast.type}`">{{ toast.message }}</div></Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RiskFilterBar from '@/components/risk/RiskFilterBar.vue'
import RiskEventsTable from '@/components/risk/RiskEventsTable.vue'
import { riskApi } from '@/api/risk'

const summary = ref<any>(null)
const events = ref<any[]>([])
const eventsLoading = ref(false)
const eventsError = ref<string | null>(null)
const actioningId = ref<string | null>(null)
const loading = ref(false)
const filters = reactive({ status: 'open', severity: '' })
const toast = ref<{ message: string; type: string } | null>(null)

async function loadSummary() { loading.value = true; try { summary.value = (await riskApi.summary()).data } finally { loading.value = false } }
async function loadEvents() { eventsLoading.value = true; eventsError.value = null; try { events.value = (await riskApi.events(1, 50, filters.status || undefined, filters.severity || undefined)).data?.items ?? [] } catch { eventsError.value = '获取事件列表失败' } finally { eventsLoading.value = false } }
async function loadAll() { await Promise.all([loadSummary(), loadEvents()]) }
async function handleAction(id: string, action: string) { actioningId.value = id; try { await riskApi.action(id, action); showToast(action === 'resolve' ? '已解决' : '已忽略', 'success'); await loadAll() } catch { showToast('操作失败', 'error') } finally { actioningId.value = null } }
function showToast(message: string, type: string) { toast.value = { message, type }; setTimeout(() => { toast.value = null }, 2500) }

onMounted(loadAll)
</script>

<style scoped>
.summary-row { display: flex; gap: 12px; margin-bottom: 16px; }
.summary-card { min-width: 160px; padding: 16px; }
.card-warn { border-color: var(--warning); }
.card-danger { border-color: var(--danger); }
.summary-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.summary-num { font-size: 36px; font-weight: 700; }
.num-warn { color: var(--warning); }
.num-danger { color: var(--danger); }
.danger-banner { padding: 10px 16px; background: var(--danger-light); border: 1px solid var(--danger); border-radius: 8px; font-size: 13px; color: var(--danger); margin-bottom: 16px; }
.toast { position: fixed; bottom: 32px; right: 32px; padding: 10px 18px; border-radius: 8px; font-size: 13px; z-index: 9999; box-shadow: var(--shadow-lg); }
.toast-success { background: var(--success-light); border: 1px solid var(--success); color: var(--success); }
.toast-error { background: var(--danger-light); border: 1px solid var(--danger); color: var(--danger); }
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
