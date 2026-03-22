<template>
  <div>
    <PageHeader title="任务中心" desc="异步任务队列管理" />

    <div v-if="stats" class="stats-row">
      <StatCard label="总计" :value="stats.total" />
      <StatCard label="运行中" :value="stats.running" highlight />
      <StatCard label="待处理" :value="stats.pending" />
      <StatCard label="已完成" :value="stats.completed" />
      <StatCard v-if="stats.failed" label="失败" :value="stats.failed" danger />
    </div>

    <n-space size="small" style="margin-bottom: 12px;">
      <n-select v-model:value="filterStatus" :options="statusOptions" size="small" style="width: 140px" />
    </n-space>

    <LoadingState v-if="loading" compact />
    <n-empty v-else-if="tasks.length === 0" description="暂无任务" />
    <div v-else class="task-list">
      <n-card v-for="t in tasks" :key="t.id" size="small" style="margin-bottom: 8px;">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
          <n-tag size="tiny">{{ t.task_type }}</n-tag>
          <n-tag :type="statusType(t.status)" size="tiny">{{ statusLabel(t.status) }}</n-tag>
          <span style="margin-left:auto;font-size:11px;color:var(--text-muted)">{{ t.created_at?.slice(0, 16) }}</span>
        </div>
        <div v-if="t.status === 'running'" style="display:flex;gap:8px;align-items:center;margin:6px 0">
          <n-progress :percentage="t.progress" :show-indicator="false" style="flex:1" />
          <span style="font-size:11px;color:var(--text-muted)">{{ t.progress }}%</span>
        </div>
        <div v-if="t.error" style="font-size:11px;color:var(--danger)">{{ t.error }}</div>
        <div v-if="t.status === 'pending' || t.status === 'running'" style="margin-top:6px">
          <n-button text size="tiny" type="error" @click="cancelTask(t.id)">取消</n-button>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { NCard, NTag, NSelect, NSpace, NEmpty, NButton, NProgress, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { tasksApi } from '@/api/tasks'
import type { TaskItem, TaskStats } from '@/api/tasks'

const msg = useMessage()
const loading = ref(true)
const tasks = ref<TaskItem[]>([])
const stats = ref<TaskStats | null>(null)
const filterStatus = ref('')

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' },
]

function statusType(s: string) { return { pending: 'warning', running: 'info', completed: 'success', failed: 'error', cancelled: 'default' }[s] as any ?? 'default' }
function statusLabel(s: string) { return { pending: '待处理', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] ?? s }

async function loadTasks() { loading.value = true; try { const res = await tasksApi.list(filterStatus.value || undefined); tasks.value = res.data?.items ?? [] } finally { loading.value = false } }
async function loadStats() { try { const res = await tasksApi.stats(); stats.value = res.data ?? null } catch {} }
async function cancelTask(id: string) { await tasksApi.cancel(id); msg.success('已取消'); await loadTasks(); await loadStats() }

watch(filterStatus, loadTasks)
onMounted(() => { loadTasks(); loadStats() })
</script>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; margin-bottom: 16px; }
.task-list { display: flex; flex-direction: column; gap: 4px; }
</style>
