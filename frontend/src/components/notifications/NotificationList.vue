<template>
  <div>
    <LoadingState v-if="loading" height="120px" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!items || items.length === 0" title="暂无通知" desc="系统正常运行中" />

    <div v-else class="notif-list">
      <NotificationCard
        v-for="n in items"
        :key="n.notification_id"
        :notification="n"
        @mark-read="(id) => $emit('markRead', id)"
      />
      <div v-if="hasMore" class="load-more">
        <button class="btn btn-ghost" :disabled="loadingMore" @click="$emit('loadMore')">{{ loadingMore ? '加载中...' : '加载更多' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import NotificationCard from './NotificationCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

defineProps<{
  items: any[]
  loading: boolean
  error?: string | null
  hasMore: boolean
  loadingMore: boolean
}>()

defineEmits<{ markRead: [id: string]; loadMore: [] }>()
</script>

<style scoped>
.notif-list { display: flex; flex-direction: column; gap: 8px; }
.load-more { display: flex; justify-content: center; padding: 12px; }
</style>
