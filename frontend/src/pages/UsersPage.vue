<template>
  <div class="users-page">
    <PageHeader title="用户管理" />

    <!-- 搜索 + 筛选 -->
    <div class="filter-bar">
      <n-input v-model:value="search" placeholder="搜索用户名..." clearable size="medium" class="search-input">
        <template #prefix>
          <IosIcon name="search" :size="16" color="var(--text-muted)" :stroke-width="2" />
        </template>
      </n-input>
      <div class="filter-chips">
        <button v-for="f in filters" :key="f.key" class="chip" :class="{ active: activeFilter === f.key }" @click="activeFilter = f.key">
          <IosIcon v-if="f.icon" :name="f.icon" :size="13" :color="activeFilter === f.key ? '#fff' : 'var(--text-muted)'" :stroke-width="2" />
          {{ f.label }}
          <span v-if="f.count !== undefined" class="chip-count">{{ f.count }}</span>
        </button>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <transition name="slide-up">
      <div v-if="selectedIds.length > 0" class="batch-bar">
        <span class="batch-count">已选 {{ selectedIds.length }} 人</span>
        <div class="batch-actions">
          <n-button size="small" @click="batchAction('enable')">启用</n-button>
          <n-button size="small" @click="batchAction('disable')">禁用</n-button>
          <n-button size="small" @click="showRenewModal = true">续期</n-button>
          <n-button size="small" @click="batchAction('set_vip')">设VIP</n-button>
          <n-button size="small" @click="batchAction('unset_vip')">取消VIP</n-button>
          <n-button size="small" type="error" quaternary @click="batchAction('delete')">删除</n-button>
          <n-button size="small" quaternary @click="exitBatch">取消</n-button>
        </div>
      </div>
    </transition>

    <!-- 用户列表 -->
    <div v-if="loading" class="loading-state">
      <div v-for="i in 5" :key="i" class="skel-card">
        <div class="skel-avatar" />
        <div class="skel-body"><div class="skel-line w60" /><div class="skel-line w40" /></div>
      </div>
    </div>
    <div v-else-if="filteredUsers.length === 0" class="empty-state">
      <IosIcon name="users" :size="36" color="var(--text-muted)" :stroke-width="1.5" />
      <span>暂无用户</span>
    </div>
    <div v-else class="user-list">
      <div
        v-for="(user, idx) in filteredUsers"
        :key="user.user_id"
        class="user-card anim-in"
        :class="{ disabled: user.is_disabled, 'batch-selected': selectedIds.includes(user.user_id) }"
        :style="{ '--i': idx % 12 }"
        @click="onCardClick(user)"
      >
        <!-- 批量选择框 -->
        <div v-if="batchMode" class="batch-check" @click.stop>
          <n-checkbox :checked="selectedIds.includes(user.user_id)" @update:checked="toggleSelect(user.user_id, $event)" />
        </div>

        <!-- 头像 -->
        <div class="user-avatar">
          <img :src="usersApi.avatarUrl(user.user_id)" :alt="user.name" loading="lazy" />
          <span v-if="user.is_vip" class="vip-badge">VIP</span>
        </div>

        <!-- 信息 -->
        <div class="user-info">
          <div class="user-name">
            {{ user.name }}
            <span v-if="user.is_admin" class="role-tag admin">管理员</span>
            <span v-if="user.is_disabled" class="role-tag disabled">已禁用</span>
          </div>
          <div class="user-meta">
            <span v-if="user.expire_date">到期: {{ formatDate(user.expire_date) }}</span>
            <span v-else>永久有效</span>
            <span class="sep">·</span>
            <span>{{ user.max_concurrent }} 路并发</span>
          </div>
          <div v-if="user.note" class="user-note">{{ user.note }}</div>
        </div>

        <!-- 操作 -->
        <div v-if="!batchMode" class="rank-arrow">›</div>
      </div>
    </div>

    <!-- 批量模式切换 -->
    <div class="batch-toggle" v-if="users.length > 0" @click="batchMode = !batchMode">
      <IosIcon :name="batchMode ? 'check' : 'filter'" :size="14" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
      {{ batchMode ? '完成' : '多选操作' }}
    </div>

    <!-- 创建用户 FAB -->
    <n-button class="fab" type="primary" circle size="large" @click="showCreateModal = true">
      <n-icon size="24"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></n-icon>
    </n-button>

    <!-- 创建用户弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建用户" class="modal-card" :style="{ maxWidth: '440px' }">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="top">
        <n-form-item label="用户名" path="name">
          <n-input v-model:value="createForm.name" placeholder="Emby 登录名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="createForm.password" type="password" show-password-on="click" placeholder="登录密码" />
        </n-form-item>
        <n-form-item label="模板用户">
          <n-select v-model:value="createForm.template_user_id" :options="templateOptions" placeholder="选择模板（可选）" clearable />
        </n-form-item>
        <div class="form-row">
          <n-form-item label="过期天数" class="flex-1">
            <n-input-number v-model:value="createForm.expire_days" :min="0" :max="9999" placeholder="留空=永久" />
          </n-form-item>
          <n-form-item label="并发限制" class="flex-1">
            <n-input-number v-model:value="createForm.max_concurrent" :min="1" :max="10" />
          </n-form-item>
        </div>
        <n-form-item label="备注">
          <n-input v-model:value="createForm.note" type="textarea" placeholder="管理员备注" :rows="2" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button type="primary" block :loading="creating" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>

    <!-- 续期弹窗 -->
    <n-modal v-model:show="showRenewModal" preset="dialog" title="批量续期" positive-text="确认" negative-text="取消" @positive-click="handleRenew">
      <n-form-item label="续期天数">
        <n-input-number v-model:value="renewDays" :min="1" :max="9999" />
      </n-form-item>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NButton, NIcon, NCheckbox, NModal, NForm, NFormItem, NSelect, NInputNumber, useMessage, useDialog } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import { usersApi, type UserInfo, type CreateUserRequest } from '@/api/users'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const users = ref<UserInfo[]>([])
const loading = ref(true)
const search = ref('')
const activeFilter = ref('all')
const batchMode = ref(false)
const selectedIds = ref<string[]>([])
const showCreateModal = ref(false)
const showRenewModal = ref(false)
const renewDays = ref(30)
const creating = ref(false)

const createForm = ref<CreateUserRequest>({ name: '', password: '', max_concurrent: 2 })
const createRules = {
  name: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
}

const filters = computed(() => [
  { key: 'all', label: '全部', icon: 'users', count: users.value.length },
  { key: 'active', label: '活跃', icon: 'check', count: users.value.filter(u => !u.is_disabled).length },
  { key: 'disabled', label: '禁用', icon: 'alert', count: users.value.filter(u => u.is_disabled).length },
  { key: 'vip', label: 'VIP', icon: 'trophy', count: users.value.filter(u => u.is_vip).length },
  { key: 'expired', label: '已过期', icon: 'clock', count: users.value.filter(u => u.expire_date && new Date(u.expire_date) < new Date()).length },
])

const filteredUsers = computed(() => {
  let list = users.value
  if (activeFilter.value === 'active') list = list.filter(u => !u.is_disabled)
  else if (activeFilter.value === 'disabled') list = list.filter(u => u.is_disabled)
  else if (activeFilter.value === 'vip') list = list.filter(u => u.is_vip)
  else if (activeFilter.value === 'expired') list = list.filter(u => u.expire_date && new Date(u.expire_date) < new Date())
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(u => u.name.toLowerCase().includes(q))
  }
  return list
})

const templateOptions = computed(() =>
  users.value.map(u => ({ label: u.name, value: u.user_id }))
)

function formatDate(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function onCardClick(user: UserInfo) {
  if (batchMode.value) {
    toggleSelect(user.user_id, !selectedIds.value.includes(user.user_id))
  } else {
    router.push(`/users/${user.user_id}`)
  }
}

function toggleSelect(id: string, checked: boolean) {
  if (checked) selectedIds.value.push(id)
  else selectedIds.value = selectedIds.value.filter(i => i !== id)
}
function exitBatch() {
  selectedIds.value = []
  batchMode.value = false
}

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await usersApi.list()
    users.value = data.data ?? data
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  creating.value = true
  try {
    await usersApi.create(createForm.value)
    message.success('创建成功')
    showCreateModal.value = false
    createForm.value = { name: '', password: '', max_concurrent: 2 }
    await loadUsers()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function batchAction(op: string) {
  if (op === 'delete') {
    dialog.warning({
      title: '确认删除',
      content: `确定删除 ${selectedIds.value.length} 个用户？此操作不可撤销。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        await usersApi.batch({ operation: 'delete', user_ids: selectedIds.value })
        message.success('已删除')
        selectedIds.value = []
        batchMode.value = false
        await loadUsers()
      },
    })
  } else {
    await usersApi.batch({ operation: op, user_ids: selectedIds.value })
    message.success('操作成功')
    selectedIds.value = []
    batchMode.value = false
    await loadUsers()
  }
}

async function handleRenew() {
  await usersApi.batch({ operation: 'renew', user_ids: selectedIds.value, days: renewDays.value })
  message.success(`已续期 ${renewDays.value} 天`)
  selectedIds.value = []
  batchMode.value = false
  showRenewModal.value = false
  await loadUsers()
}

onMounted(loadUsers)
</script>

<style scoped>
.users-page { padding: 0.5rem 0; padding-bottom: 100px; }
.filter-bar { margin-bottom: 0.75rem; }
.search-input { margin-bottom: 0.5rem; }
.search-input :deep(.n-input) { border-radius: 12px; }
.filter-chips { display: flex; gap: 6px; overflow-x: auto; -webkit-overflow-scrolling: touch; padding: 2px 0; }
.chip { border: none; background: var(--bg-secondary); color: var(--text-muted); padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; cursor: pointer; white-space: nowrap; transition: all 0.15s; font-family: inherit; }
.chip.active { background: var(--brand); color: #fff; }
.chip-count { font-size: 0.7rem; margin-left: 4px; opacity: 0.7; }
.loading-state, .empty-state { text-align: center; padding: 1.5rem 1rem; color: var(--text-muted); font-size: 0.85rem; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }

/* ── 骨架屏 ── */
.skel-card { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 8px; }
.skel-avatar { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; flex-shrink: 0; }
.skel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.skel-line { height: 12px; border-radius: 6px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.skel-line.w60 { width: 60%; }
.skel-line.w40 { width: 40%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── 入场动画 ── */
.anim-in { opacity: 0; transform: translateY(10px); animation: slideUp 0.3s cubic-bezier(0.22,1,0.36,1) forwards; animation-delay: calc(var(--i, 0) * 30ms); }
@keyframes slideUp { to { opacity: 1; transform: translateY(0); } }

.vip-badge { position: absolute; bottom: -2px; right: -2px; background: linear-gradient(135deg, #FFD700, #FFA500); color: #fff; font-size: 0.55rem; font-weight: 700; padding: 1px 5px; border-radius: 4px; box-shadow: 0 2px 6px rgba(255,165,0,0.3); }
.user-avatar img { box-shadow: 0 2px 8px rgba(0,0,0,0.12); border-radius: 12px; }
.role-tag { font-size: 0.65rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; }
.role-tag.admin { background: rgba(0,122,255,0.1); color: #007AFF; }
.role-tag.disabled { background: rgba(255,59,48,0.1); color: #FF3B30; }
.rank-arrow { font-size: 1.2rem; color: var(--text-muted); opacity: 0.3; flex-shrink: 0; transition: opacity 0.15s; }
.user-card:hover .rank-arrow { opacity: 0.6; }
.chip { display: inline-flex; align-items: center; gap: 4px; }
.chip:active { transform: scale(0.95); }
.user-list { display: flex; flex-direction: column; gap: 1px; }
.user-card { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; cursor: pointer; transition: all 0.15s; }
.user-card:active { transform: scale(0.98); opacity: 0.8; }
.user-card.disabled { opacity: 0.5; }
.user-card.batch-selected { border-color: var(--brand); background: var(--brand-light); }
.batch-check { flex-shrink: 0; }
.user-avatar { width: 44px; height: 44px; border-radius: 12px; overflow: hidden; flex-shrink: 0; position: relative; background: var(--bg-secondary); }
.user-avatar img { width: 100%; height: 100%; object-fit: cover; }
.vip-badge { position: absolute; bottom: -2px; right: -2px; background: linear-gradient(135deg, #FFD700, #FFA500); color: #fff; font-size: 0.55rem; font-weight: 700; padding: 1px 4px; border-radius: 4px; }
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 0.9rem; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.role-tag { font-size: 0.65rem; font-weight: 600; padding: 1px 6px; border-radius: 4px; }
.role-tag.admin { background: var(--brand-light); color: var(--brand); }
.role-tag.disabled { background: var(--danger-light); color: var(--danger); }
.user-meta { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.sep { margin: 0 3px; }
.user-note { font-size: 0.7rem; color: var(--text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-action { flex-shrink: 0; }
.batch-bar { position: fixed; bottom: 0; left: 0; right: 0; background: var(--surface-strong); backdrop-filter: blur(20px); border-top: 1px solid var(--border); padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between; z-index: 100; }
.batch-count { font-size: 0.85rem; font-weight: 600; color: var(--brand); }
.batch-actions { display: flex; gap: 6px; }
.batch-toggle { text-align: center; padding: 1rem; color: var(--text-muted); font-size: 0.8rem; cursor: pointer; }
.fab { position: fixed; bottom: calc(80px + 0.5rem); right: 1.5rem; width: 52px; height: 52px; box-shadow: 0 4px 16px rgba(0,122,255,0.3); z-index: 50; }
.modal-card { border-radius: 16px; }
.form-row { display: flex; gap: 1rem; }
.flex-1 { flex: 1; }
.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.25s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }

@media (max-width: 767px) {
  .fab { bottom: calc(80px + 0.5rem); right: 1rem; width: 48px; height: 48px; }
  .batch-bar {
    bottom: 64px;
    padding: 0.6rem 0.75rem;
    flex-direction: column;
    gap: 6px;
    align-items: stretch;
  }
  .batch-count { font-size: 0.8rem; }
  .batch-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .batch-actions :deep(.n-button) {
    font-size: 0.72rem;
    padding: 0 8px;
    height: 28px;
  }
}
</style>
