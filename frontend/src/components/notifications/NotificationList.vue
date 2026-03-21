<template>
  <div class="notification-list">
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!notifications || notifications.length === 0" message="No notifications" />
    
    <div v-else>
      <div class="list-container">
        <NotificationCard
          v-for="notification in notifications"
          :key="notification.id"
          :notification="notification"
          @mark-read="$emit('mark-read', notification)"
          @view="$emit('view', notification)"
        />
      </div>
      
      <div v-if="hasMore" class="load-more">
        <button class="btn btn-ghost" @click="$emit('load-more')" :disabled="loadingMore">
          {{ loadingMore ? 'Loading...' : 'Load more' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import NotificationCard from './NotificationCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

interface Notification {
  id: string
  title: string
  body: string
  level: 'info' | 'warning' | 'error' | 'success'
  read: boolean
  created_at: string
  metadata?: Record<string, any>
}

const props = defineProps<{
  notifications: Notification[]
  loading: boolean
  error?: string
  hasMore: boolean
  loadingMore: boolean
}>()

const emit = defineEmits<{
  'mark-read': [notification: Notification]
  'view': [notification: Notification]
  'load-more': []
}>()
</script>

<style scoped>
.notification-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 1rem;
}

.load-more .btn {
  min-width: 120px;
}
</style>