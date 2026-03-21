<template>
  <div class="notification-card" :class="{ unread: !notification.is_read }">
    <div class="nc-header">
      <span class="tag" :class="levelTag(notification.level)">{{ levelLabel(notification.level) }}</span>
      <span class="nc-time">{{ formatTime(notification.created_at) }}</span>
    </div>
    <div class="nc-body">
      <div class="nc-title">{{ notification.title }}</div>
      <div class="nc-msg">{{ notification.message }}</div>
    </div>
    <div v-if="!notification.is_read" class="nc-actions">
      <button class="btn btn-ghost btn-sm" @click="$emit('markRead', notification.notification_id)">标记已读</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ notification: any }>()
defineEmits<{ markRead: [id: string] }>()

function levelTag(l: string) { return { info: 'tag-blue', warning: 'tag-yellow', error: 'tag-red' }[l] ?? 'tag-gray' }
function levelLabel(l: string) { return { info: '信息', warning: '警告', error: '错误' }[l] ?? l }
function formatTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.notification-card { padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); }
.notification-card.unread { border-color: var(--brand); background: var(--brand-light); }
.nc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.nc-time { font-size: 11px; color: var(--text-muted); }
.nc-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.nc-msg { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.nc-actions { margin-top: 8px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
</style>
