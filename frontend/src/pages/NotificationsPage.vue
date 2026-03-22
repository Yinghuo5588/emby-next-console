<template>
  <div>
    <PageHeader title="通知中心" desc="系统通知、通道、模板与规则管理">
      <template #actions>
        <n-button v-if="unreadCount > 0" quaternary size="small" :loading="markingAll" @click="handleMarkAll">全部已读</n-button>
      </template>
    </PageHeader>

    <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
      <n-tab-pane name="list" tab="📬 通知">
        <div class="unread-banner" :class="{ 'has-unread': unreadCount > 0 }">
          <template v-if="unreadCount > 0"><span class="dot" />你有 <strong>{{ unreadCount }}</strong> 条未读通知</template>
          <template v-else>✓ 所有通知均已读</template>
        </div>
        <NotificationList :items="notifications" :loading="loading" :error="error" :marking-id="markingId" :has-more="hasMore" :loading-more="loadingMore" @retry="loadNotifications" @mark-read="handleMarkRead" @load-more="loadMore" />
      </n-tab-pane>
      <n-tab-pane name="channels">
        <template #tab><IosIcon name="link" :size="16" /> 通道</template>
        <ChannelConfig />
      </n-tab-pane>
      <n-tab-pane name="templates">
        <template #tab><IosIcon name="save" :size="16" /> 模板</template>
        <TemplateEditor />
      </n-tab-pane>
      <n-tab-pane name="rules">
        <template #tab><IosIcon name="settings" :size="16" /> 规则</template>
        <RuleMatrix />
      </n-tab-pane>
      <n-tab-pane name="logs">
        <template #tab><IosIcon name="check" :size="16" /> 记录</template>
        <div style="margin-bottom: 12px; display: flex; gap: 8px;">
          <n-select v-model:value="logFilter.status" :options="statusOptions" clearable placeholder="全部状态" size="small" style="width: 140px" />
          <n-select v-model:value="logFilter.eventType" :options="eventOptions" clearable placeholder="全部事件" size="small" style="width: 160px" />
        </div>
        <LoadingState v-if="logsLoading && logs.length === 0" compact />
        <n-empty v-else-if="logs.length === 0" description="暂无发送记录" />
        <div v-else class="logs-list">
          <n-card v-for="log in logs" :key="log.id" size="small" style="margin-bottom: 8px;">
            <div class="log-head">
              <n-tag size="tiny">{{ log.event_type }}</n-tag>
              <n-tag :type="logStatusType(log.status)" size="tiny">{{ log.status }}</n-tag>
              <span class="log-time">{{ log.created_at?.slice(0, 16) }}</span>
            </div>
            <div class="log-title">{{ log.title }}</div>
            <div v-if="log.error_message" class="log-error">{{ log.error_message }}</div>
          </n-card>
          <div v-if="logsTotal > logs.length" style="text-align: center; margin-top: 12px;">
            <n-button text @click="logPage++; loadLogs()">加载更多</n-button>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { NTabs, NTabPane, NButton, NTag, NSelect, NCard, NEmpty } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ChannelConfig from '@/components/notifications/ChannelConfig.vue'
import TemplateEditor from '@/components/notifications/TemplateEditor.vue'
import RuleMatrix from '@/components/notifications/RuleMatrix.vue'
import NotificationList from '@/components/notifications/NotificationList.vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationLog } from '@/api/notifications-ext'
import apiClient from '@/api/client'

const activeTab = ref('list')

const notifications = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const unreadCount = ref(0)
const markingAll = ref(false)
const markingId = ref<number | null>(null)
const hasMore = ref(false)
const loadingMore = ref(false)
const page = ref(1)

const logs = ref<NotificationLog[]>([])
const logsLoading = ref(false)
const logsTotal = ref(0)
const logPage = ref(1)
const logFilter = ref({ status: null as string | null, eventType: null as string | null })

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已发送', value: 'sent' },
  { label: '待发送', value: 'pending' },
  { label: '失败', value: 'failed' },
]
const eventOptions = [
  { label: '全部事件', value: '' },
  { label: '风控-高危', value: 'risk_high' },
  { label: '新剧集', value: 'new_episode' },
  { label: '服务器错误', value: 'server_error' },
]

async function loadNotifications() {
  loading.value = true; error.value = ''
  try {
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
    const res = await apiClient.get('/notifications', { params: { page: page.value, page_size: 20 } })
    const items = res.data?.data?.items ?? []
    notifications.value.push(...items)
    hasMore.value = items.length >= 20
  } finally { loadingMore.value = false }
}

async function handleMarkRead(id: number) {
  markingId.value = id
  try {
    await apiClient.post(`/notifications/${id}/read`)
    const n = notifications.value.find(n => n.id === id)
    if (n) { n.is_read = true; unreadCount.value = Math.max(0, unreadCount.value - 1) }
  } finally { markingId.value = null }
}

async function handleMarkAll() {
  markingAll.value = true
  try {
    await apiClient.post('/notifications/read-all')
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } finally { markingAll.value = false }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const res = await notificationsExtApi.listLogs(logPage.value, 20, logFilter.value.eventType || undefined, logFilter.value.status || undefined)
    if (logPage.value === 1) logs.value = []
    logs.value.push(...(res.data?.items ?? []))
    logsTotal.value = res.data?.total ?? 0
  } finally { logsLoading.value = false }
}

function logStatusType(s: string) { return { sent: 'success', pending: 'warning', failed: 'error' }[s] as any ?? 'default' }

watch([logFilter], () => { logPage.value = 1; loadLogs() }, { deep: true })

onMounted(() => { loadNotifications() })
</script>

<style scoped>
.unread-banner { padding: 10px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; background: var(--bg-secondary); }
.has-unread { background: rgba(59,130,246,0.08); }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--brand); margin-right: 6px; }
.logs-list { display: flex; flex-direction: column; gap: 4px; }
.log-head { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
.log-time { margin-left: auto; font-size: 11px; color: var(--text-muted); }
.log-title { font-size: 13px; font-weight: 500; }
.log-error { font-size: 11px; margin-top: 4px; color: var(--danger); }
</style>
