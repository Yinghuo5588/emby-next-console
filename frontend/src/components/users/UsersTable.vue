<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />
  <n-empty v-else-if="!items || items.length === 0" description="暂无用户" />

  <template v-else>
    <!-- Desktop: NDataTable -->
    <n-card class="desktop-only" size="small" style="overflow: hidden;">
      <n-data-table
        :columns="columns"
        :data="items"
        :row-key="(r: any) => r.user_id"
        :checked-row-keys="selectedIds"
        size="small"
        :bordered="false"
        :row-props="rowProps"
        @update:checked-row-keys="$emit('toggle-select-all')"
      />
    </n-card>

    <!-- Mobile: cards -->
    <div class="mobile-only">
      <div v-for="u in items" :key="u.user_id" class="user-card">
        <n-card size="small" style="margin-bottom: 8px;">
          <div class="uc-top">
            <n-checkbox :checked="selectedIds?.includes(u.user_id)" @update:checked="$emit('toggle-select', u.user_id)" />
            <router-link :to="`/users/${u.user_id}`" style="display:flex;align-items:center;gap:10px;flex:1;text-decoration:none;color:inherit">
              <n-avatar :src="`/api/v1/proxy/user_image/${u.user_id}`" :size="36" round :style="{ background: '#3b82f6' }" fallback-src="">{{ u.username?.charAt(0)?.toUpperCase() || '?' }}</n-avatar>
              <div class="uc-info">
                <div style="font-weight:500">{{ u.username }}</div>
                <n-space size="small">
                  <n-tag :type="u.status === 'active' ? 'success' : 'error'" size="tiny">{{ u.status === 'active' ? '正常' : '禁用' }}</n-tag>
                  <n-tag v-if="u.role === 'admin'" type="info" size="tiny">管理员</n-tag>
                  <n-tag v-if="isExpired(u.expire_at)" type="error" size="tiny">已过期</n-tag>
                </n-space>
              </div>
            </router-link>
          </div>
          <div class="uc-meta">
            <span v-if="u.expire_at" :class="{ expired: isExpired(u.expire_at) }">🕐 {{ formatDate(u.expire_at) }}</span>
            <span v-if="u.max_concurrent">👥 {{ u.max_concurrent }}路</span>
            <span v-if="u.note">📝 {{ u.note }}</span>
          </div>
        </n-card>
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { useRouter } from 'vue-router'
import type { DataTableColumns } from 'naive-ui'
import { NCard, NDataTable, NAvatar, NTag, NEmpty, NButton, NSpace, NCheckbox } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'

const router = useRouter()

defineProps<{
  items: any[]
  loading: boolean
  error?: string | null
  selectedIds?: string[]
}>()

defineEmits<{
  retry: []
  view: [user: any]
  'toggle-select': [userId: string]
  'toggle-select-all': []
}>()

const columns: DataTableColumns = [
  {
    title: '用户', key: 'username',
    render: (row: any) => h('div', { style: 'display:flex;align-items:center;gap:10px' }, [
      h(NAvatar, { size: 36, round: true, src: `/api/v1/proxy/user_image/${row.user_id}`, fallbackSrc: '', style: 'background:#3b82f6' }, { default: () => row.username?.charAt(0)?.toUpperCase() || '?' }),
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
    title: '过期时间', key: 'expire_at', width: 110,
    render: (row: any) => {
      if (!row.expire_at) return h('span', { style: 'font-size:12px;color:var(--text-muted)' }, '永久')
      const expired = isExpired(row.expire_at)
      return h(NTag, { type: expired ? 'error' : 'warning', size: 'tiny' }, { default: () => formatDate(row.expire_at) })
    },
  },
  {
    title: '并发', key: 'max_concurrent', width: 60,
    render: (row: any) => h('span', { style: 'font-size:12px' }, row.max_concurrent ? `${row.max_concurrent}路` : '不限'),
  },
  {
    title: '备注', key: 'note', width: 100, ellipsis: { tooltip: true },
    render: (row: any) => h('span', { style: 'font-size:12px;color:var(--text-muted)' }, row.note || ''),
  },
]

function rowProps(row: any) {
  return { style: 'cursor:pointer', onClick: (e: MouseEvent) => { if (!(e.target as HTMLElement).closest('.n-checkbox')) router.push(`/users/${row.user_id}`) } }
}

function isExpired(date?: string) {
  if (!date) return false
  return new Date(date).getTime() < Date.now()
}

function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<style scoped>
.desktop-only { display: block; }
.mobile-only { display: none; }
.user-card { display: block; }
.uc-top { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.uc-info { flex: 1; min-width: 0; }
.uc-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); }
.uc-meta .expired { color: var(--error-color, #e74c3c); }
@media (max-width: 768px) {
  .desktop-only { display: none; }
  .mobile-only { display: flex; flex-direction: column; }
}
</style>
