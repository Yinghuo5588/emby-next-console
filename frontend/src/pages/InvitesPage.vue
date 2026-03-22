<template>
  <div>
    <PageHeader title="邀请管理" desc="生成与管理邀请码">
      <template #actions>
        <RouterLink to="/admin/users/invites/create" class="btn btn-primary">+ 创建邀请</RouterLink>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <div class="stat-grid" v-if="stats">
      <StatCard label="总发出" :value="stats.total" />
      <StatCard label="有效中" :value="stats.active" color="green" />
      <StatCard label="已使用" :value="stats.used" color="blue" />
      <StatCard label="已过期" :value="stats.expired" color="yellow" />
      <StatCard label="已禁用" :value="stats.disabled" color="red" />
    </div>

    <!-- 筛选 -->
    <div class="filter-row">
      <select v-model="statusFilter" @change="loadInvites(1)">
        <option value="">全部状态</option>
        <option value="active">有效</option>
        <option value="used">已使用</option>
        <option value="expired">已过期</option>
        <option value="disabled">已禁用</option>
      </select>
    </div>

    <!-- 邀请码列表 -->
    <LoadingState v-if="loading" height="120px" />
    <div v-else class="card" style="padding: 0; overflow: auto;">
      <table>
        <thead>
          <tr>
            <th>邀请码</th>
            <th>状态</th>
            <th>使用次数</th>
            <th>过期时间</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="invites.length === 0">
            <td colspan="6" class="empty">暂无邀请码</td>
          </tr>
          <tr v-for="inv in invites" :key="inv.id">
            <td>
              <code class="invite-code">{{ inv.code }}</code>
              <button class="btn btn-ghost btn-sm" @click="copyLink(inv.code)" style="margin-left: 6px;">复制链接</button>
            </td>
            <td>
              <span class="tag" :class="statusTag(inv.status)">{{ statusLabel(inv.status) }}</span>
            </td>
            <td>{{ inv.used_count }} / {{ inv.max_uses }}</td>
            <td class="muted">{{ inv.expires_at ? new Date(inv.expires_at).toLocaleDateString('zh-CN') : '永不过期' }}</td>
            <td class="muted">{{ new Date(inv.created_at).toLocaleDateString('zh-CN') }}</td>
            <td>
              <button v-if="inv.status === 'active'" class="btn btn-ghost btn-sm btn-danger" @click="disableInvite(inv.id)">禁用</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { invitesApi, type InviteCode, type InviteStats } from '@/api/invites'

const invites = ref<InviteCode[]>([])
const stats = ref<InviteStats | null>(null)
const loading = ref(false)
const statusFilter = ref('')

async function loadStats() {
  const res = await invitesApi.stats()
  stats.value = res.data ?? null
}

async function loadInvites(page = 1) {
  loading.value = true
  try {
    const res = await invitesApi.list(statusFilter.value || undefined, page)
    invites.value = res.data?.items ?? []
  } finally {
    loading.value = false
  }
}

async function disableInvite(id: number) {
  if (!confirm('确定禁用此邀请码？')) return
  await invitesApi.disable(id)
  await loadInvites()
  await loadStats()
}

function copyLink(code: string) {
  const url = `${window.location.origin}/register?code=${code}`
  navigator.clipboard.writeText(url)
  alert('链接已复制')
}

function statusTag(s: string) {
  return { active: 'tag-green', used: 'tag-blue', expired: 'tag-yellow', disabled: 'tag-red' }[s] ?? 'tag-gray'
}
function statusLabel(s: string) {
  return { active: '有效', used: '已使用', expired: '已过期', disabled: '已禁用' }[s] ?? s
}

onMounted(() => { loadStats(); loadInvites() })
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
.filter-row { display: flex; gap: 8px; margin-bottom: 16px; }
.filter-row select { min-width: 120px; }
.invite-code { background: var(--bg-secondary); padding: 2px 8px; border-radius: 4px; font-weight: 600; letter-spacing: 1px; }
.btn-sm { padding: 3px 8px; font-size: 12px; }
.btn-danger { color: var(--danger); }
.muted { color: var(--text-muted); font-size: 12px; }
.empty { text-align: center; padding: 40px !important; color: var(--text-muted); }
</style>