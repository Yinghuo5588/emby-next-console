<template>
  <div>
    <PageHeader title="邀请管理" desc="生成与管理邀请码">
      <template #actions>
        <n-button type="primary" size="small" @click="$router.push('/admin/users/invites/create')">+ 创建邀请</n-button>
      </template>
    </PageHeader>

    <div v-if="stats" class="stat-grid">
      <StatCard label="总发出" :value="stats.total" />
      <StatCard label="有效中" :value="stats.active" highlight />
      <StatCard label="已使用" :value="stats.used" />
      <StatCard label="已过期" :value="stats.expired" danger />
      <StatCard label="已禁用" :value="stats.disabled" danger />
    </div>

    <n-space size="small" style="margin-bottom: 12px;">
      <n-select v-model:value="statusFilter" :options="statusOptions" size="small" style="width: 140px" @update:value="loadInvites(1)" />
    </n-space>

    <LoadingState v-if="loading" />
    <n-card v-else size="small" style="overflow: auto;">
      <n-empty v-if="invites.length === 0" description="暂无邀请码" />
      <n-data-table v-else :columns="columns" :data="invites" size="small" :bordered="false" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, NSelect, NSpace, NCard, NEmpty, NDataTable, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { invitesApi, type InviteCode, type InviteStats } from '@/api/invites'

const msg = useMessage()
const invites = ref<InviteCode[]>([])
const stats = ref<InviteStats | null>(null)
const loading = ref(false)
const statusFilter = ref('')

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '有效', value: 'active' },
  { label: '已使用', value: 'used' },
  { label: '已过期', value: 'expired' },
  { label: '已禁用', value: 'disabled' },
]

const columns: DataTableColumns = [
  {
    title: '邀请码', key: 'code',
    render: (row: any) => h('div', { style: 'display:flex;align-items:center;gap:6px' }, [
      h('code', { style: 'background:var(--bg-secondary);padding:2px 8px;border-radius:4px;font-weight:600;letter-spacing:1px' }, row.code),
      h(NButton, { text: true, size: 'tiny', onClick: () => copyLink(row.code) }, { default: () => '复制链接' }),
    ]),
  },
  {
    title: '状态', key: 'status', width: 80,
    render: (row: any) => {
      const type = { active: 'success', used: 'info', expired: 'warning', disabled: 'error' }[row.status] as any ?? 'default'
      const label = { active: '有效', used: '已使用', expired: '已过期', disabled: '已禁用' }[row.status] ?? row.status
      return h(NTag, { type, size: 'small' }, { default: () => label })
    },
  },
  { title: '使用次数', key: 'used_count', width: 100, render: (r: any) => `${r.used_count} / ${r.max_uses}` },
  { title: '过期时间', key: 'expires_at', width: 120, render: (r: any) => r.expires_at ? new Date(r.expires_at).toLocaleDateString('zh-CN') : '永不过期' },
  { title: '创建时间', key: 'created_at', width: 120, render: (r: any) => new Date(r.created_at).toLocaleDateString('zh-CN') },
  {
    title: '', key: 'actions', width: 80,
    render: (row: any) => row.status === 'active'
      ? h(NButton, { text: true, size: 'tiny', type: 'error', onClick: () => disableInvite(row.id) }, { default: () => '禁用' })
      : null,
  },
]

async function loadStats() { const res = await invitesApi.stats(); stats.value = res.data ?? null }
async function loadInvites(page = 1) { loading.value = true; try { const res = await invitesApi.list(statusFilter.value || undefined, page); invites.value = res.data?.items ?? [] } finally { loading.value = false } }
async function disableInvite(id: number) { await invitesApi.disable(id); msg.success('已禁用'); await loadInvites(); await loadStats() }
function copyLink(code: string) { navigator.clipboard.writeText(`${window.location.origin}/register?code=${code}`); msg.success('链接已复制') }

onMounted(() => { loadStats(); loadInvites() })
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
</style>
