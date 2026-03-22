<template>
  <div>
    <PageHeader title="通知中心" desc="系统通知、通道、模板与规则管理">
      <template #actions>
        <button v-if="unreadCount > 0" class="btn btn-ghost" :disabled="markingAll" @click="handleMarkAll">
          {{ markingAll ? '处理中...' : '全部已读' }}
        </button>
      </template>
    </PageHeader>

    <!-- Tab 栏 -->
    <div class="tab-bar">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <!-- Tab 1: 通知列表 -->
    <div v-show="activeTab === 'list'">
      <div class="unread-banner" :class="{ 'has-unread': unreadCount > 0 }">
        <template v-if="unreadCount > 0"><span class="dot" />你有 <strong>{{ unreadCount }}</strong> 条未读通知</template>
        <template v-else>✓ 所有通知均已读</template>
      </div>
      <NotificationList :items="notifications" :loading="loading" :error="error" :marking-id="markingId" :has-more="hasMore" :loading-more="loadingMore" @retry="loadNotifications" @mark-read="handleMarkRead" @load-more="loadMore" />
    </div>

    <!-- Tab 2: 通道配置 -->
    <div v-show="activeTab === 'channels'">
      <ChannelConfig />
    </div>

    <!-- Tab 3: 模板编辑 -->
    <div v-show="activeTab === 'templates'">
      <TemplateEditor />
    </div>

    <!-- Tab 4: 场景矩阵 -->
    <div v-show="activeTab === 'rules'">
      <RuleMatrix />
    </div>

    <!-- Tab 5: 发送记录 -->
    <div v-show="activeTab === 'logs'">
      <div class="card" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
        <select v-model="logFilter.status" style="padding: 6px; border-radius: 6px; font-size: 12px; background: var(--bg); border: 1px solid var(--border);">
          <option value="">全部状态</option>
          <option value="sent">已发送</option>
          <option value="pending">待发送</option>
          <option value="failed">失败</option>
        </select>
        <select v-model="logFilter.eventType" style="padding: 6px; border-radius: 6px; font-size: 12px; background: var(--bg); border: 1px solid var(--border);">
          <option value="">全部事件</option>
          <option value="risk_high">风控-高危</option>
          <option value="new_episode">新剧集</option>
          <option value="server_error">服务器错误</option>
        </select>
      </div>
      <div v-if="logsLoading" class="muted" style="text-align: center; padding: 24px;">加载中...</div>
      <div v-else-if="logs.length === 0" class="muted" style="text-align: center; padding: 24px;">暂无发送记录</div>
      <div v-else class="logs-list">
        <div v-for="log in logs" :key="log.id" class="card log-card">
          <div class="log-head">
            <span class="tag">{{ log.event_type }}</span>
            <span :class="log.status === 'sent' ? 'tag tag-green' : log.status === 'failed' ? 'tag tag-red' : 'tag tag-yellow'">
              {{ log.status }}
            </span>
            <span class="log-time muted">{{ log.created_at?.slice(0, 16) }}</span>
          </div>
          <div class="log-title">{{ log.title }}</div>
          <div v-if="log.error_message" class="log-error muted">{{ log.error_message }}</div>
        </div>
        <div v-if="logsTotal > logs.length" style="text-align: center; margin-top: 12px;">
          <button class="btn btn-ghost" @click="logPage++; loadLogs()">加载更多</button>
        </div>
      </div>
    </div>

    <Transition name="toast"><div v-if="toast" class="toast" :class="`toast-${toast.type}`">{{ toast.message }}</div></Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ChannelConfig from '@/components/notifications/ChannelConfig.vue'
import TemplateEditor from '@/components/notifications/TemplateEditor.vue'
import RuleMatrix from '@/components/notifications/RuleMatrix.vue'
import NotificationList from '@/components/notifications/NotificationList.vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationLog } from '@/api/notifications-ext'

const activeTab = ref('list')
const tabs = [
  { key: 'list', icon: '📬', label: '通知' },
  { key: 'channels', icon: '📡', label: '通道' },
  { key: 'templates', icon: '📝', label: '模板' },
  { key: 'rules', icon: '⚙️', label: '规则' },
  { key: 'logs', icon: '📋', label: '记录' },
]

// 通知列表（保留原有逻辑）
const notifications = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const unreadCount = ref(0)
const markingAll = ref(false)
const markingId = ref<number | null>(null)
const hasMore = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const toast = ref<{ type: string; message: string } | null>(null)

// 发送记录
const logs = ref<NotificationLog[]>([])
const logsLoading = ref(false)
const logsTotal = ref(0)
const logPage = ref(1)
const logFilter = ref({ status: '', eventType: '' })

async function loadNotifications() {
  loading.value = true; error.value = ''
  try {
    // 原有通知加载逻辑
    const { default: apiClient } = await import('@/api/client')
    const res = await apiClient.get('/notifications', { params: { page: page.value, page_size: 20 } })
    const data = res.data?.data
    notifications.value = data?.items ?? []
    unreadCount.value = data?.unread_count ?? 0
    hasMore.value = (data?.total ?? 0) > notifications.value.length
  } catch (e: any) { error.value = e.message || '加载失败' }
  finally { loading.value = false }
}

async function loadMore() {
  loadingMore.value = true; page.value++
  try {
    const { default: apiClient } = await import('@/api/client')
    const res = await apiClient.get('/notifications', { params: { page: page.value, page_size: 20 } })
    const items = res.data?.data?.items ?? []
    notifications.value.push(...items)
    hasMore.value = items.length >= 20
  } finally { loadingMore.value = false }
}

async function handleMarkRead(id: number) {
  markingId.value = id
  try {
    const { default: apiClient } = await import('@/api/client')
    await apiClient.post(`/notifications/${id}/read`)
    const n = notifications.value.find(n => n.id === id)
    if (n) { n.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1) }
  } finally { markingId.value = null }
}

async function handleMarkAll() {
  markingAll.value = true
  try {
    const { default: apiClient } = await import('@/api/client')
    await apiClient.post('/notifications/read-all')
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } finally { markingAll.value = false }
}

// 日志
async function loadLogs() {
  logsLoading.value = true
  try {
    const res = await notificationsExtApi.listLogs(logPage.value, 20, logFilter.value.eventType || undefined, logFilter.value.status || undefined)
    if (logPage.value === 1) logs.value = []
    logs.value.push(...(res.data?.items ?? []))
    logsTotal.value = res.data?.total ?? 0
  } finally { logsLoading.value = false }
}

watch([logFilter], () => { logPage.value = 1; loadLogs() }, { deep: true })

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; overflow-x: auto; }
.tab-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text-muted); cursor: pointer; font-size: 13px; white-space: nowrap; }
.tab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.unread-banner { padding: 10px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; background: var(--bg-secondary); }
.has-unread { background: var(--primary-light, rgba(59,130,246,0.08)); }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--primary); margin-right: 6px; }
.logs-list { display: flex; flex-direction: column; gap: 8px; }
.log-card { padding: 10px; }
.log-head { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.log-time { margin-left: auto; font-size: 11px; }
.log-title { font-size: 13px; font-weight: 500; }
.log-error { font-size: 11px; margin-top: 4px; color: var(--danger); }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: var(--bg-secondary); }
.tag-green { background: #d1fae5; color: #059669; }
.tag-red { background: #fee2e2; color: #dc2626; }
.tag-yellow { background: #fef3c7; color: #d97706; }
.muted { color: var(--text-muted); }
</style>