<template>
  <n-card size="small" :class="{ unread: !notification.is_read }" style="margin-bottom:8px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
      <n-tag :type="levelType(notification.level)" size="tiny">{{ levelLabel(notification.level) }}</n-tag>
      <span style="font-size:11px;color:var(--text-muted)">{{ formatTime(notification.created_at) }}</span>
    </div>
    <div style="font-size:13px;font-weight:600;margin-bottom:4px">{{ notification.title }}</div>
    <div style="font-size:12px;color:var(--text-muted);line-height:1.5">{{ notification.message }}</div>
    <div v-if="!notification.is_read" style="margin-top:8px">
      <n-button text size="tiny" @click="$emit('markRead', notification.notification_id)">标记已读</n-button>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { NCard, NTag, NButton } from 'naive-ui'

defineProps<{ notification: any }>()
defineEmits<{ markRead: [id: string] }>()

function levelType(l: string) { return { info: 'info', warning: 'warning', error: 'error' }[l] as any ?? 'default' }
function levelLabel(l: string) { return { info: '信息', warning: '警告', error: '错误' }[l] ?? l }
function formatTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return new Date(iso).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.unread { border-color: var(--brand) !important; background: rgba(59, 130, 246, 0.05) !important; }
</style>
