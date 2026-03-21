<template>
  <div class="notification-card" :class="{ unread: !notification.read }">
    <div class="notification-header">
      <span :class="`badge badge-${getLevelColor(notification.level)}`">
        {{ notification.level }}
      </span>
      <div class="time">{{ formatTime(notification.created_at) }}</div>
    </div>
    
    <div class="notification-body">
      <h4 class="title">{{ notification.title }}</h4>
      <p class="body">{{ notification.body }}</p>
    </div>
    
    <div class="notification-footer">
      <button 
        v-if="!notification.read" 
        class="btn btn-ghost btn-sm" 
        @click="$emit('mark-read', notification)"
      >
        Mark as read
      </button>
      <button 
        class="btn btn-ghost btn-sm" 
        @click="$emit('view', notification)"
      >
        View details
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
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
  notification: Notification
}>()

const emit = defineEmits<{
  'mark-read': [notification: Notification]
  'view': [notification: Notification]
}>()

const getLevelColor = (level: string) => {
  switch (level) {
    case 'error': return 'red'
    case 'warning': return 'yellow'
    case 'success': return 'green'
    case 'info': return 'blue'
    default: return 'gray'
  }
}

const formatTime = (date: string) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString()
}
</script>

<style scoped>
.notification-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  transition: all 0.2s;
}

.notification-card.unread {
  background: var(--surface-strong);
  border-color: var(--brand);
  box-shadow: 0 0 0 1px var(--brand-light);
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-red {
  background: var(--danger-light);
  color: var(--danger);
}

.badge-yellow {
  background: var(--warning-light);
  color: var(--warning);
}

.badge-green {
  background: var(--success-light);
  color: var(--success);
}

.badge-blue {
  background: var(--brand-light);
  color: var(--brand);
}

.badge-gray {
  background: var(--bg-secondary);
  color: var(--text-muted);
}

.time {
  font-size: 12px;
  color: var(--text-muted);
}

.notification-body {
  margin-bottom: 1rem;
}

.title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.5rem 0;
  line-height: 1.3;
}

.body {
  font-size: 0.875rem;
  color: var(--text-soft);
  margin: 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-footer {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .notification-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .notification-footer {
    flex-direction: column;
  }
}
</style>