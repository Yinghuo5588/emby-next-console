<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />
  <n-empty v-else-if="!items || items.length === 0" description="暂无用户" />

  <template v-else>
    <!-- Desktop: NDataTable -->
    <n-card class="desktop-only" size="small" style="overflow: hidden;">
      <n-data-table :columns="columns" :data="items" size="small" :bordered="false" :row-props="rowProps" />
    </n-card>

    <!-- Mobile: cards -->
    <div class="mobile-only">
      <router-link v-for="u in items" :key="u.user_id" :to="`/users/${u.user_id}`" class="user-card">
        <n-card size="small" style="margin-bottom: 8px;">
          <div class="uc-top">
            <n-avatar :size="36" round :style="{ background: '#3b82f6' }">{{ u.username?.charAt(0)?.toUpperCase() || '?' }}</n-avatar>
            <div class="uc-info">
              <div style="font-weight:500">{{ u.username }}</div>
              <n-space size="small">
                <n-tag :type="u.status === 'active' ? 'success' : 'error'" size="tiny">{{ u.status === 'active' ? '正常' : '禁用' }}</n-tag>
                <n-tag v-if="u.role === 'admin'" type="info" size="tiny">管理员</n-tag>
              </n-space>
            </div>
          </div>
          <div style="font-size:12px;color:var(--text-muted);text-align:right">{{ formatDate(u.last_active) }}</div>
        </n-card>
      </router-link>
    </div>
  </template>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { useRouter } from 'vue-router'
import type { DataTableColumns } from 'naive-ui'
import { NCard, NDataTable, NAvatar, NTag, NEmpty, NButton, NSpace } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const router = useRouter()

defineProps<{
  items: any[]
  loading: boolean
  error?: string | null
}>()

defineEmits<{ retry: []; view: [user: any] }>()

const columns: DataTableColumns = [
  {
    title: '用户', key: 'username',
    render: (row: any) => h('div', { style: 'display:flex;align-items:center;gap:10px' }, [
      h(NAvatar, { size: 36, round: true, style: 'background:#3b82f6' }, { default: () => row.username?.charAt(0)?.toUpperCase() || '?' }),
      h('div', {}, [
        h('div', { style: 'font-weight:500;font-size:13px' }, row.username),
        h('div', { style: 'font-size:12px;color:var(--text-muted)' }, row.display_name || ''),
      ]),
    ]),
  },
  {
    title: '状态', key: 'status', width: 80,
    render: (row: any) => h(NTag, { type: row.status === 'active' ? 'success' : 'error', size: 'small' }, { default: () => row.status === 'active' ? '正常' : '禁用' }),
  },
  {
    title: '角色', key: 'role', width: 80,
    render: (row: any) => h(NTag, { type: row.role === 'admin' ? 'info' : 'default', size: 'small' }, { default: () => row.role === 'admin' ? '管理员' : '用户' }),
  },
  {
    title: '最后活跃', key: 'last_active', width: 120,
    render: (row: any) => h('span', { style: 'font-size:12px;color:var(--text-muted)' }, formatDate(row.last_active)),
  },
  {
    title: '', key: 'actions', width: 80,
    render: (row: any) => h(NButton, { text: true, size: 'small', type: 'primary', onClick: () => router.push(`/users/${row.user_id}`) }, { default: () => '详情' }),
  },
]

function rowProps(row: any) {
  return { style: 'cursor:pointer', onClick: () => router.push(`/users/${row.user_id}`) }
}

function formatDate(iso?: string) {
  if (!iso) return '从未'
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.desktop-only { display: block; }
.mobile-only { display: none; }
.user-card { display: block; text-decoration: none; color: inherit; }
.uc-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.uc-info { flex: 1; min-width: 0; }
@media (max-width: 768px) {
  .desktop-only { display: none; }
  .mobile-only { display: flex; flex-direction: column; }
}
</style>
