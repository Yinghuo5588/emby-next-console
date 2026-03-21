<template>
  <div class="users-table">
    <LoadingState v-if="loading" height="120px" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!items || items.length === 0" title="暂无用户" />

    <!-- Desktop table -->
    <div v-else class="table-wrap desktop-only">
      <table>
        <thead>
          <tr>
            <th>用户</th>
            <th>状态</th>
            <th>角色</th>
            <th>最后活跃</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.user_id" @click="$emit('view', u)" style="cursor:pointer">
            <td>
              <div class="user-cell">
                <div class="avatar">{{ u.username?.charAt(0)?.toUpperCase() || '?' }}</div>
                <div class="user-meta">
                  <div class="uname">{{ u.username }}</div>
                  <div class="uemail">{{ u.display_name || '' }}</div>
                </div>
              </div>
            </td>
            <td><span class="tag" :class="u.status === 'active' ? 'tag-green' : 'tag-red'">{{ u.status === 'active' ? '正常' : '禁用' }}</span></td>
            <td><span class="tag" :class="u.role === 'admin' ? 'tag-blue' : 'tag-gray'">{{ u.role === 'admin' ? '管理员' : '用户' }}</span></td>
            <td class="muted">{{ formatDate(u.last_active) }}</td>
            <td>
              <RouterLink :to="`/users/${u.user_id}`" class="btn btn-ghost btn-sm">详情</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile cards -->
    <div v-if="items && items.length > 0" class="cards-wrap mobile-only">
      <RouterLink v-for="u in items" :key="u.user_id" :to="`/users/${u.user_id}`" class="user-card card">
        <div class="uc-top">
          <div class="avatar">{{ u.username?.charAt(0)?.toUpperCase() || '?' }}</div>
          <div class="uc-info">
            <div class="uname">{{ u.username }}</div>
            <div class="uc-meta">
              <span class="tag" :class="u.status === 'active' ? 'tag-green' : 'tag-red'" style="font-size:10px">{{ u.status === 'active' ? '正常' : '禁用' }}</span>
              <span v-if="u.role === 'admin'" class="tag tag-blue" style="font-size:10px">管理员</span>
            </div>
          </div>
        </div>
        <div class="uc-bottom">
          <span class="muted">{{ formatDate(u.last_active) }}</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

defineProps<{
  items: any[]
  loading: boolean
  error?: string | null
}>()

defineEmits<{ view: [user: any] }>()

function formatDate(iso?: string) {
  if (!iso) return '从未'
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.users-table { overflow: hidden; }
.table-wrap { overflow-x: auto; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--brand); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; flex-shrink: 0; }
.user-cell { display: flex; align-items: center; gap: 10px; }
.user-meta { min-width: 0; }
.uname { font-weight: 500; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.uemail { font-size: 12px; color: var(--text-muted); }
.muted { color: var(--text-muted); font-size: 12px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }

.cards-wrap { display: flex; flex-direction: column; gap: 8px; }
.user-card { display: block; text-decoration: none; color: inherit; padding: 12px; }
.uc-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.uc-info { flex: 1; min-width: 0; }
.uc-meta { display: flex; gap: 6px; margin-top: 4px; }
.uc-bottom { display: flex; justify-content: flex-end; }

.desktop-only { display: block; }
.mobile-only { display: none; }

@media (max-width: 768px) {
  .desktop-only { display: none; }
  .mobile-only { display: flex; }
}
</style>
