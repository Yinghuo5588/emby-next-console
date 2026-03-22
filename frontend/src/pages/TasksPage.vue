<template>
  <div>
    <PageHeader title="任务中心" desc="异步任务队列管理" />

    <div v-if="stats" class="stats-row" style="margin-bottom: 16px;">
      <div class="card stat-mini"><div class="sm-val">{{ stats.total }}</div><div class="sm-label">总计</div></div>
      <div class="card stat-mini"><div class="sm-val">{{ stats.running }}</div><div class="sm-label">运行中</div></div>
      <div class="card stat-mini"><div class="sm-val">{{ stats.pending }}</div><div class="sm-label">待处理</div></div>
      <div class="card stat-mini"><div class="sm-val">{{ stats.completed }}</div><div class="sm-label">已完成</div></div>
      <div class="card stat-mini" v-if="stats.failed"><div class="sm-val" style="color:var(--danger)">{{ stats.failed }}</div><div class="sm-label">失败</div></div>
    </div>

    <div class="card" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
      <select v-model="filterStatus" style="padding: 6px; border-radius: 6px; font-size: 12px; background: var(--bg); border: 1px solid var(--border);">
        <option value="">全部状态</option>
        <option value="pending">待处理</option>
        <option value="running">运行中</option>
        <option value="completed">已完成</option>
        <option value="failed">失败</option>
        <option value="cancelled">已取消</option>
      </select>
    </div>

    <LoadingState v-if="loading" height="80px" />
    <EmptyState v-else-if="tasks.length === 0" title="暂无任务" desc="异步操作会显示在这里" />
    <div v-else class="task-list">
      <div v-for="t in tasks" :key="t.id" class="card task-card">
        <div class="task-head">
          <span class="tag">{{ t.task_type }}</span>
          <span class="tag" :class="statusClass(t.status)">{{ statusLabel(t.status) }}</span>
          <span class="muted" style="margin-left:auto; font-size:11px;">{{ t.created_at?.slice(0, 16) }}</span>
        </div>
        <div v-if="t.status === 'running'" class="task-progress">
          <div class="progress-bar"><div class="progress-fill" :style="{ width: t.progress + '%' }"></div></div>
          <span class="progress-text">{{ t.progress }}%</span>
        </div>
        <div v-if="t.error" class="muted" style="font-size:11px; color:var(--danger)">{{ t.error }}</div>
        <div class="task-actions">
          <button v-if="t.status === 'pending' || t.status === 'running'" class="btn btn-ghost btn-sm" style="color:var(--danger);" @click="cancelTask(t.id)">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { tasksApi } from '@/api/tasks'
import type { TaskItem, TaskStats } from '@/api/tasks'

const loading = ref(true)
const tasks = ref<TaskItem[]>([])
const stats = ref<TaskStats | null>(null)
const filterStatus = ref('')

function statusClass(s: string) {
  return { pending: 'tag-yellow', running: 'tag-blue', completed: 'tag-green', failed: 'tag-red', cancelled: 'tag-gray' }[s] || 'tag-gray'
}
function statusLabel(s: string) {
  return { pending: '待处理', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] || s
}

async function loadTasks() {
  loading.value = true
  try {
    const res = await tasksApi.list(filterStatus.value || undefined)
    tasks.value = res.data?.items ?? []
  } finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await tasksApi.stats()
    stats.value = res.data ?? null
  } catch {}
}

async function cancelTask(id: string) {
  if (!confirm('确定取消此任务？')) return
  await tasksApi.cancel(id)
  await loadTasks()
  await loadStats()
}

watch(filterStatus, loadTasks)
onMounted(() => { loadTasks(); loadStats() })
</script>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; }
.stat-mini { text-align: center; padding: 12px; }
.sm-val { font-size: 22px; font-weight: 700; }
.sm-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.task-list { display: flex; flex-direction: column; gap: 8px; }
.task-card { padding: 12px; }
.task-head { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.task-progress { display: flex; gap: 8px; align-items: center; margin: 6px 0; }
.progress-bar { flex: 1; height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--primary); transition: width 0.3s; }
.progress-text { font-size: 11px; color: var(--text-muted); }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: var(--bg-secondary); }
.tag-green { background: #d1fae5; color: #059669; }
.tag-red { background: #fee2e2; color: #dc2626; }
.tag-yellow { background: #fef3c7; color: #d97706; }
.tag-blue { background: #dbeafe; color: #2563eb; }
.tag-gray { background: var(--bg-secondary); color: var(--text-muted); }
.muted { color: var(--text-muted); }
.btn-sm { padding: 4px 8px; font-size: 12px; }
</style>
