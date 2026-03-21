<template>
 <div class="table-wrap card">
 <!-- loading overlay（首次加载，无数据时全覆盖） -->
 <div v-if="loading && items.length === 0" class="table-state">
 <LoadingState height="280px" />
 </div>

 <!-- error -->
 <div v-else-if="error" class="table-state">
 <ErrorState :message="error" @retry="emit('retry')" />
 </div>

 <!-- 正常渲染（含刷新时的半透明蒙层） -->
 <template v-else>
 <div v-if="loading" class="refresh-mask" />

 <table>
 <thead>
 <tr>
 <th>用户</th>
 <th>状态</th>
 <th>角色</th>
 <th>VIP</th>
 <th>到期时间</th>
 <th>注册时间</th>
 <th style="width: 72px;">操作</th>
 </tr>
 </thead>
 <tbody>
 <!-- empty -->
 <tr v-if="items.length === 0">
 <td colspan="7">
 <div class="row-empty">暂无匹配用户</div>
 </td>
 </tr>

 <tr v-for="u in items" :key="u.user_id" class="user-row">
 <!-- 用户列 -->
 <td>
 <div class="user-cell">
 <RouterLink :to="`/users/${u.user_id}`" class="user-name">
 {{ u.display_name || u.username }}
 </RouterLink>
 <span class="user-handle">@{{ u.username }}</span>
 </div>
 </td>

 <!-- 状态 -->
 <td>
 <span class="tag" :class="statusClass(u.status)">
 {{ statusLabel(u.status) }}
 </span>
 </td>

 <!-- 角色 -->
 <td>
 <span class="tag" :class="u.role === 'admin' ? 'tag-purple' : 'tag-gray'">
 {{ u.role === 'admin' ? '管理员' : '用户' }}
 </span>
 </td>

 <!-- VIP -->
 <td>
 <span v-if="u.is_vip" class="vip-badge">⭐ VIP</span>
 <span v-else class="tag tag-gray" style="opacity:.6;">—</span>
 </td>

 <!-- 到期时间 -->
 <td>
 <span :class="{ 'text-expiring': isExpiringSoon(u.expire_at) }">
 {{ u.expire_at ? formatDate(u.expire_at) : '永久' }}
 </span>
 <span
 v-if="isExpiringSoon(u.expire_at)"
 class="expiring-tip"
 >即将到期</span>
 </td>

 <!-- 注册时间 -->
 <td class="muted">{{ formatDate(u.created_at) }}</td>

 <!-- 操作 -->
 <td>
 <RouterLink
 :to="`/users/${u.user_id}`"
 class="btn btn-ghost action-btn"
 >
 详情
 </RouterLink>
 </td>
 </tr>
 </tbody>
 </table>
 </template>
 </div>
</template>

<script setup lang="ts">
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import type { UserListItem, UserStatus } from '@/api/users'
import { formatDate, isExpiringSoon } from '@/utils/time'

defineProps<{
 items: UserListItem[]
 loading: boolean
 error: string | null
}>()

const emit = defineEmits<{ retry: [] }>()

function statusClass(s: UserStatus) {
 const map: Record<string, string> = {
 active: 'tag-green',
 disabled: 'tag-gray',
 expired: 'tag-yellow',
 }
 return map[s] ?? 'tag-gray'
}

function statusLabel(s: UserStatus) {
 const map: Record<string, string> = {
 active: '活跃',
 disabled: '禁用',
 expired: '已过期',
 }
 return map[s] ?? s
}
</script>

<style scoped>
.table-wrap {
 padding: 0;
 position: relative;
 overflow: hidden;
}

/* 全覆盖状态容器 */
.table-state {
 min-height: 280px;
 display: flex;
 align-items: center;
 justify-content: center;
}

/* 刷新时半透明蒙层，不打断表格显示 */
.refresh-mask {
 position: absolute;
 inset: 0;
 background: rgba(15, 17, 23, 0.35);
 z-index: 1;
 pointer-events: none;
}

/* 空行 */
.row-empty {
 padding: 48px;
 text-align: center;
 color: var(--color-text-muted);
 font-size: 13px;
}

/* 用户列 */
.user-cell {
 display: flex;
 flex-direction: column;
 gap: 2px;
}

.user-name {
 font-weight: 500;
 font-size: 13px;
 color: var(--color-text);
 line-height: 1.3;
}

.user-name:hover {
 color: var(--color-primary);
}

.user-handle {
 font-size: 12px;
 color: var(--color-text-muted);
}

/* VIP */
.vip-badge {
 font-size: 12px;
 font-weight: 600;
 color: #f59e0b;
}

/* 到期 */
.text-expiring {
 color: var(--color-warning);
}

.expiring-tip {
 display: block;
 font-size: 11px;
 color: var(--color-warning);
 opacity: 0.8;
 margin-top: 1px;
}

/* 操作按钮 */
.action-btn {
 padding: 4px 10px;
 font-size: 12px;
}

.muted {
 color: var(--color-text-muted);
 font-size: 13px;
}

/* 行 hover */
.user-row:hover td {
 background: var(--color-surface-2);
}
</style>