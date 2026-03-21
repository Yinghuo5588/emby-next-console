<template>
 <div class="notifications-page">
 <!-- 页头 -->
 <PageHeader title="通知中心" desc="系统通知、风控提醒与关键事件">
 <template #actions>
 <button
 v-if="unreadCount > 0"
 class="btn btn-ghost"
 :disabled="markingAll"
 @click="handleMarkAll"
 >
 {{ markingAll ? '处理中...' : '全部标为已读' }}
 </button>
 </template>
 </PageHeader>

 <!-- 未读摘要区 -->
 <div class="unread-banner" :class="{ 'has-unread': unreadCount > 0 }">
 <template v-if="unreadCount > 0">
 <span class="unread-dot-wrap">
 <span class="unread-dot" />
 </span>
 <span class="unread-text">
 你有 <strong>{{ unreadCount }}</strong> 条未读通知
 </span>
 </template>
 <template v-else>
 <span class="all-read-icon">✓</span>
 <span class="unread-text all-read-text">所有通知均已读</span>
 </template>
 </div>

 <!-- 通知列表 -->
 <NotificationList
 :items="notifications"
 :loading="loading"
 :error="error"
 :marking-id="markingId"
 :has-more="hasMore"
 :loading-more="loadingMore"
 @retry="loadNotifications"
 @mark-read="handleMarkRead"
 @load-more="loadMore"
 />

 <!-- 操作 Toast -->
 <Transition name="toast">
 <div v-if="toast" class="toast" :class="`toast-${toast.type}`">
 {{ toast.message }}
 </div>
 </Transition>
 </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import NotificationList from '@/components/notifications/NotificationList.vue'
import { notificationsApi, type NotificationItem } from '@/api/notifications'
import { useNotificationsStore } from '@/stores/notifications'

const notifStore = useNotificationsStore()

// ── 状态 ─────────────────────────────────────────
const notifications = ref<NotificationItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const markingId = ref<string | null>(null)
const markingAll = ref(false)

// 分页状态（为后续分页扩展预留）
const currentPage = ref(1)
const PAGE_SIZE = 30
const total = ref(0)
const loadingMore = ref(false)

const hasMore = computed(
 () => notifications.value.length < total.value,
)

const unreadCount = computed(
 () => notifications.value.filter(n => !n.is_read).length,
)

// Toast
interface Toast { message: string; type: 'success' | 'error' }
const toast = ref<Toast | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

// ── 数据加载 ──────────────────────────────────────
async function loadNotifications() {
 loading.value = true
 error.value = null
 currentPage.value = 1
 try {
 const res = await notificationsApi.list(1, PAGE_SIZE)
 notifications.value = res.items
 total.value = res.total
 } catch {
 error.value = '获取通知失败，请重试'
 } finally {
 loading.value = false
 }
}

async function loadMore() {
 if (loadingMore.value || !hasMore.value) return
 loadingMore.value = true
 try {
 const nextPage = currentPage.value + 1
 const res = await notificationsApi.list(nextPage, PAGE_SIZE)
 notifications.value.push(...res.items)
 total.value = res.total
 currentPage.value = nextPage
 } finally {
 loadingMore.value = false
 }
}

// ── 操作 ─────────────────────────────────────────
async function handleMarkRead(id: string) {
 markingId.value = id
 try {
 await notificationsApi.markRead(id)
 // 本地更新，不重新请求
 const item = notifications.value.find(n => n.notification_id === id)
 if (item) item.is_read = true
 // 同步 sidebar 角标
 notifStore.fetchUnreadCount()
 showToast('已标记为已读', 'success')
 } catch {
 showToast('操作失败，请重试', 'error')
 } finally {
 markingId.value = null
 }
}

async function handleMarkAll() {
 markingAll.value = true
 try {
 await notificationsApi.markAllRead()
 // 本地全部标为已读
 notifications.value.forEach(n => { n.is_read = true })
 notifStore.fetchUnreadCount()
 showToast('已全部标为已读', 'success')
 } catch {
 showToast('操作失败，请重试', 'error')
 } finally {
 markingAll.value = false
 }
}

// ── Toast ─────────────────────────────────────────
function showToast(message: string, type: Toast['type']) {
 if (toastTimer) clearTimeout(toastTimer)
 toast.value = { message, type }
 toastTimer = setTimeout(() => { toast.value = null }, 2500)
}

// ── 初始化 ────────────────────────────────────────
onMounted(loadNotifications)
</script>

<style scoped>
/* ── 未读摘要横幅 ──────────────────────────────── */
.unread-banner {
 display: flex;
 align-items: center;
 gap: 10px;
 padding: 12px 16px;
 border-radius: 8px;
 font-size: 13px;
 margin-bottom: 20px;
 background: var(--color-surface);
 border: 1px solid var(--color-border);
 color: var(--color-text-muted);
 transition: border-color 0.2s, background 0.2s;
}

.unread-banner.has-unread {
 background: rgba(99, 102, 241, 0.06);
 border-color: rgba(99, 102, 241, 0.3);
 color: var(--color-text);
}

.unread-dot-wrap {
 display: flex;
 align-items: center;
 flex-shrink: 0;
}

.unread-dot {
 width: 8px;
 height: 8px;
 border-radius: 50%;
 background: var(--color-primary);
 box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
 animation: pulse-blue 2s ease-in-out infinite;
}

@keyframes pulse-blue {
 0%, 100% { box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }
 50% { box-shadow: 0 0 0 5px rgba(99, 102, 241, 0.05); }
}

.unread-text strong {
 color: var(--color-primary);
 font-weight: 700;
}

.all-read-icon {
 color: var(--color-success);
 font-size: 14px;
}

.all-read-text {
 color: var(--color-text-muted);
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