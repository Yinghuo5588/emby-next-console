<template>
  <div>
    <PageHeader title="通知中心" desc="系统通知与提醒">
      <template #actions>
        <button v-if="unreadCount > 0" class="btn btn-ghost" :disabled="markingAll" @click="handleMarkAll">{{ markingAll ? '处理中...' : '全部已读' }}</button>
      </template>
    </PageHeader>

    <div class="unread-banner" :class="{ 'has-unread': unreadCount > 0 }">
      <template v-if="unreadCount > 0"><span class="dot" />你有 <strong>{{ unreadCount }}</strong> 条未读通知</template>
      <template v-else>✓ 所有通知均已读</template>
    </div>

    <NotificationList :items="notifications" :loading="loading" :error="error" :marking-id="markingId" :has-more="hasMore" :loading-more="loadingMore" @retry="loadNotifications" @mark-read="handleMarkRead" @load-more="loadMore" />

    <Transition name="toast"><div v-if="toast" class="toast" :class="`toast-${toast.type}`">{{ toast.message }}</div></Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import NotificationList from '@/components/notifications/NotificationList.vue'
import { notificationsApi } from '@/api/notifications'

const notifications = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const markingId = ref<string | null>(null)
const markingAll = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)
const unreadCount = computed(() => notifications.value.filter((n: any) => !n.is_read).length)
const hasMore = computed(() => notifications.value.length < total.value)
const toast = ref<{ message: string; type: string } | null>(null)

async function loadNotifications() { loading.value = true; error.value = null; currentPage.value = 1; try { const r = await notificationsApi.list(1, 30); notifications.value = r.data?.items ?? []; total.value = r.data?.total ?? 0 } catch { error.value = '获取通知失败' } finally { loading.value = false } }
async function loadMore() { if (loadingMore.value || !hasMore.value) return; loadingMore.value = true; try { const r = await notificationsApi.list(currentPage.value + 1, 30); notifications.value.push(...(r.data?.items ?? [])); total.value = r.data?.total ?? 0; currentPage.value++ } finally { loadingMore.value = false } }
async function handleMarkRead(id: string) { markingId.value = id; try { await notificationsApi.markRead(id); const item = notifications.value.find((n: any) => n.notification_id === id); if (item) item.is_read = true; showToast('已标记已读', 'success') } catch { showToast('操作失败', 'error') } finally { markingId.value = null } }
async function handleMarkAll() { markingAll.value = true; try { await notificationsApi.markAllRead(); notifications.value.forEach((n: any) => { n.is_read = true }); showToast('全部已读', 'success') } catch { showToast('操作失败', 'error') } finally { markingAll.value = false } }
function showToast(message: string, type: string) { toast.value = { message, type }; setTimeout(() => { toast.value = null }, 2500) }

onMounted(loadNotifications)
</script>

<style scoped>
.unread-banner { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-radius: 8px; font-size: 13px; margin-bottom: 16px; background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.unread-banner.has-unread { background: var(--brand-light); border-color: var(--brand); color: var(--text); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--brand); flex-shrink: 0; }
strong { color: var(--brand); font-weight: 700; }
.toast { position: fixed; bottom: 32px; right: 32px; padding: 10px 18px; border-radius: 8px; font-size: 13px; z-index: 9999; box-shadow: var(--shadow-lg); }
.toast-success { background: var(--success-light); border: 1px solid var(--success); color: var(--success); }
.toast-error { background: var(--danger-light); border: 1px solid var(--danger); color: var(--danger); }
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
