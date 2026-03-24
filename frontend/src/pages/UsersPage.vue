<template>
  <div>
    <PageHeader title="用户管理" :desc="total > 0 ? `共 ${total} 名用户` : ''" />
    <UsersFilterBar v-model="filters" style="margin-bottom: 12px" @search="loadUsers(1)" @update:model-value="loadUsers(1)" />

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span class="batch-count">已选 {{ selectedIds.length }} 人</span>
      <n-space size="small">
        <n-button size="small" type="error" @click="batchAction('delete')">删除</n-button>
        <n-button size="small" type="warning" @click="batchAction('disable')">禁用</n-button>
        <n-button size="small" type="success" @click="batchAction('enable')">启用</n-button>
        <n-button size="small" type="info" @click="showRenewModal = true">续期</n-button>
        <n-button size="small" @click="selectedIds = []">取消</n-button>
      </n-space>
    </div>

    <UsersTable
      :items="users"
      :loading="loading"
      :error="error"
      :selected-ids="selectedIds"
      @retry="loadUsers(currentPage)"
      @toggle-select="toggleSelect"
      @toggle-select-all="toggleSelectAll"
    />
    <PaginationBar v-if="!error" :total="total" :current-page="currentPage" :page-size="20" :disabled="loading" @change="loadUsers" />

    <!-- 续期弹窗 -->
    <n-modal v-model:show="showRenewModal" preset="dialog" title="批量续期" positive-text="确定" negative-text="取消" @positive-click="doRenew">
      <n-input-number v-model:value="renewDays" :min="1" :max="3650" placeholder="续期天数" style="width: 100%" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useMessage, NModal, NInputNumber, NSpace, NButton } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import UsersFilterBar from '@/components/users/UsersFilterBar.vue'
import UsersTable from '@/components/users/UsersTable.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { usersApi } from '@/api/users'

const message = useMessage()
const users = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const loading = ref(false)
const error = ref<string | null>(null)
const filters = reactive({ search: '', status: '', is_vip: '', role: '' })
const selectedIds = ref<string[]>([])
const showRenewModal = ref(false)
const renewDays = ref(30)

async function loadUsers(page: number) {
  loading.value = true; error.value = null; currentPage.value = page
  try {
    const res = await usersApi.list({ page, page_size: 20 })
    users.value = res.data?.items ?? []; total.value = res.data?.total ?? 0
  } catch { error.value = '获取用户列表失败' }
  finally { loading.value = false }
}

function toggleSelect(userId: string) {
  const idx = selectedIds.value.indexOf(userId)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(userId)
}

function toggleSelectAll() {
  if (selectedIds.value.length === users.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = users.value.map(u => u.user_id)
  }
}

async function batchAction(action: string) {
  const actionName: Record<string, string> = { delete: '删除', enable: '启用', disable: '禁用' }
  const ids = [...selectedIds.value]
  if (action === 'delete' && !confirm(`确定删除 ${ids.length} 个用户？此操作不可恢复！`)) return
  try {
    const res = await usersApi.batch({ action: action as any, user_ids: ids })
    const r = res.data
    message.success(`${actionName[action]}成功 ${r.success.length} 个`)
    if (r.failed.length > 0) message.warning(`${r.failed.length} 个失败`)
    selectedIds.value = []
    loadUsers(currentPage.value)
  } catch { message.error('批量操作失败') }
}

async function doRenew() {
  const ids = [...selectedIds.value]
  try {
    const res = await usersApi.batch({ action: 'renew', user_ids: ids, days: renewDays.value })
    const r = res.data
    message.success(`续期成功 ${r.success.length} 个`)
    if (r.failed.length > 0) message.warning(`${r.failed.length} 个失败`)
    selectedIds.value = []
    showRenewModal.value = false
    loadUsers(currentPage.value)
  } catch { message.error('续期失败') }
}

onMounted(() => loadUsers(1))
</script>

<style scoped>
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  margin-bottom: 8px;
  background: var(--primary-color-suppl, #f0f5ff);
  border-radius: var(--radius-lg, 8px);
  border: 1px solid var(--primary-color, #3b82f6);
}
.batch-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--primary-color, #3b82f6);
}
</style>
