<template>
 <div class="notif-list">
 <LoadingState v-if="loading && items.length === 0" height="300px" />

 <ErrorState
 v-else-if="error"
 :message="error"
 height="200px"
 @retry="emit('retry')"
 />

 <template v-else>
 <!-- 空状态 -->
 <div v-if="items.length === 0" class="list-empty">
 <div class="empty-icon">◎</div>
 <div class="empty-title">暂无通知</div>
 <div class="empty-desc">系统通知、风控提醒等会出现在这里</div>
 </div>

 <!-- 通知卡片流 -->
 <TransitionGroup v-else name="notif" tag="div" class="card-flow">
 <NotificationCard
 v-for="item in items"
 :key="item.notification_id"
 :item="item"
 :marking="markingId === item.notification_id"
 @mark-read="emit('mark-read', $event)"
 />
 </TransitionGroup>

 <!-- 加载更多（有 hasMore 时显示） -->
 <div v-if="hasMore" class="load-more">
 <button
 class="btn btn-ghost load-more-btn"
 :disabled="loadingMore"
 @click="emit('load-more')"
 >
 {{ loadingMore ? '加载中...' : '加载更多' }}
 </button>
 </div>
 </template>
 </div>
</template>

<script setup lang="ts">
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import NotificationCard from './NotificationCard.vue'
import type { NotificationItem } from '@/api/notifications'

defineProps<{
 items: NotificationItem[]
 loading: boolean
 error: string | null
 markingId: string | null
 hasMore?: boolean
 loadingMore?: boolean
}>()

const emit = defineEmits<{
 retry: []
 'mark-read': [id: string]
 'load-more': []
}>()
</script>

<style scoped>
.notif-list { }

.list-empty {
 display: flex;
 flex-direction: column;
 align-items: center;
 padding: 64px 24px;
 text-align: center;
}

.empty-icon {
 font-size: 36px;
 color: var(--color-border);
 margin-bottom: 14px;
}

.empty-title {
 font-size: 15px;
 font-weight: 500;
 color: var(--color-text-muted);
 margin-bottom: 6px;
}

.empty-desc {
 font-size: 13px;
 color: var(--color-text-muted);
 opacity: 0.7;
}

/* 卡片流 */
.card-flow {
 display: flex;
 flex-direction: column;
 gap: 10px;
}

/* 加载更多 */
.load-more {
 display: flex;
 justify-content: center;
 margin-top: 16px;
}

.load-more-btn {
 min-width: 120px;
 justify-content: center;
}

/* 卡片进出动画 */
.notif-enter-active {
 transition: opacity 0.25s, transform 0.25s;
}

.notif-leave-active {
 transition: opacity 0.2s, transform 0.2s;
}

.notif-enter-from {
 opacity: 0;
 transform: translateY(-6px);
}

.notif-leave-to {
 opacity: 0;
 transform: translateX(10px);
}
</style>