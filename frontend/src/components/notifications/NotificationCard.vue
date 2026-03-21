<template>
 <div class="notif-card" :class="{ unread: !item.is_read }">
 <!-- 未读指示条 -->
 <div class="unread-bar" />

 <div class="card-body">
 <!-- 顶行：level 标签 + 标题 + 时间 -->
 <div class="card-head">
 <span class="tag level-tag" :class="levelClass(item.level)">
 {{ levelLabel(item.level) }}
 </span>
 <span class="notif-title" :class="{ 'title-unread': !item.is_read }">
 {{ item.title }}
 </span>
 <span class="notif-time">{{ fromNow(item.created_at) }}</span>
 </div>

 <!-- 正文摘要 -->
 <p class="notif-body">{{ item.message }}</p>

 <!-- 底行：详情链接 + 标记已读 -->
 <div class="card-foot">
 <a
 v-if="item.action_url"
 :href="item.action_url"
 class="action-link"
 target="_self"
 >
 查看详情 →
 </a>
 <div v-else class="spacer" />

 <button
 v-if="!item.is_read"
 class="btn btn-read"
 :disabled="marking"
 @click="emit('mark-read', item.notification_id)"
 >
 {{ marking ? '...' : '标为已读' }}
 </button>
 <span v-else class="read-badge">✓ 已读</span>
 </div>
 </div>
 </div>
</template>

<script setup lang="ts">
import type { NotificationItem } from '@/api/notifications'
import { fromNow } from '@/utils/time'

defineProps<{
 item: NotificationItem
 marking?: boolean
}>()

const emit = defineEmits<{
 'mark-read': [id: string]
}>()

function levelClass(level: string) {
 return {
 info: 'tag-gray',
 warning: 'tag-yellow',
 error: 'tag-red',
 }[level] ?? 'tag-gray'
}

function levelLabel(level: string) {
 return { info: '通知', warning: '警告', error: '错误' }[level] ?? level
}
</script>

<style scoped>
.notif-card {
 display: flex;
 background: var(--color-surface);
 border: 1px solid var(--color-border);
 border-radius: 10px;
 overflow: hidden;
 transition: border-color 0.15s, box-shadow 0.15s;
}

.notif-card:hover {
 border-color: rgba(99, 102, 241, 0.3);
 box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

/* 未读左侧彩色条 */
.unread-bar {
 width: 3px;
 background: transparent;
 flex-shrink: 0;
 transition: background 0.2s;
}

.notif-card.unread .unread-bar {
 background: var(--color-primary);
}

.card-body {
 flex: 1;
 padding: 14px 18px;
 min-width: 0;
 display: flex;
 flex-direction: column;
 gap: 8px;
}

/* 顶行 */
.card-head {
 display: flex;
 align-items: center;
 gap: 10px;
 flex-wrap: wrap;
}

.level-tag {
 font-size: 11px;
 padding: 2px 7px;
 flex-shrink: 0;
}

.notif-title {
 font-size: 14px;
 font-weight: 500;
 color: var(--color-text-muted);
 flex: 1;
 white-space: nowrap;
 overflow: hidden;
 text-overflow: ellipsis;
 min-width: 0;
 transition: color 0.15s;
}

.title-unread {
 color: var(--color-text);
}

.notif-time {
 font-size: 12px;
 color: var(--color-text-muted);
 flex-shrink: 0;
 white-space: nowrap;
}

/* 正文 */
.notif-body {
 font-size: 13px;
 color: var(--color-text-muted);
 line-height: 1.6;
 margin: 0;
 /* 最多显示 2 行 */
 display: -webkit-box;
 -webkit-line-clamp: 2;
 -webkit-box-orient: vertical;
 overflow: hidden;
}

/* 底行 */
.card-foot {
 display: flex;
 align-items: center;
 justify-content: space-between;
 gap: 12px;
 margin-top: 2px;
}

.action-link {
 font-size: 12px;
 color: var(--color-primary);
 flex-shrink: 0;
}

.action-link:hover {
 color: var(--color-primary-hover);
}

.spacer {
 flex: 1;
}

.btn-read {
 padding: 3px 10px;
 border-radius: 5px;
 font-size: 12px;
 background: var(--color-surface-2);
 color: var(--color-text-muted);
 border: 1px solid var(--color-border);
 cursor: pointer;
 transition: all 0.15s;
 flex-shrink: 0;
}

.btn-read:hover:not(:disabled) {
 color: var(--color-text);
 border-color: var(--color-text-muted);
}

.btn-read:disabled {
 opacity: 0.4;
 cursor: not-allowed;
}

.read-badge {
 font-size: 12px;
 color: var(--color-text-muted);
 opacity: 0.6;
}
</style>