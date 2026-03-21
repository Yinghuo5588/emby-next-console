<template>
 <div class="users-page">
 <!-- 页头 -->
 <PageHeader
 title="用户管理"
 :desc="total > 0 ? `共 ${total} 名用户` : ''"
 >
 <template #actions>
 <button class="btn btn-ghost" @click="handleReset">重置筛选</button>
 </template>
 </PageHeader>

 <!-- 筛选栏 -->
 <UsersFilterBar
 v-model="filters"
 style="margin-bottom: 16px;"
 @search="handleSearch"
 @update:model-value="handleFilterChange"
 />

 <!-- 用户表格 -->
 <UsersTable
 :items="users"
 :loading="loading"
 :error="error"
 @retry="loadUsers(currentPage)"
 />

 <!-- 分页（error 或 loading 首屏时不显示） -->
 <PaginationBar
 v-if="!error && !(loading && users.length === 0)"
 :total="total"
 :current-page="currentPage"
 :page-size="PAGE_SIZE"
 :disabled="loading"
 style="background: var(--color-surface); border-radius: 0 0 10px 10px;"
 @change="loadUsers"
 />
 </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import UsersFilterBar, { type FilterValues } from '@/components/users/UsersFilterBar.vue'
import UsersTable from '@/components/users/UsersTable.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { usersApi, type UserListItem } from '@/api/users'

const PAGE_SIZE = 20

// --- state ---
const users = ref<UserListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const loading = ref(false)
const error = ref<string | null>(null)

const filters = reactive<FilterValues>({
 search: '',
 status: '',
 is_vip: '',
 role: '',
})

// 监听 status / is_vip / role 变化，立即刷新第 1 页
// search 需要手动回车 / 点击，不在这里 watch
watch(
 () => [filters.status, filters.is_vip, filters.role],
 () => loadUsers(1),
)

// --- methods ---
function handleSearch(_value: string) {
 loadUsers(1)
}

function handleFilterChange(newVal: FilterValues) {
 Object.assign(filters, newVal)
}

function handleReset() {
 Object.assign(filters, {
 search: '',
 status: '',
 is_vip: '',
 role: '',
 })
 loadUsers(1)
}

async function loadUsers(page: number) {
 loading.value = true
 error.value = null
 currentPage.value = page

 try {
 // 构建请求参数
 // 注意：当前 stub API 仅支持 page / page_size；
 // status 等筛选参数已预留，后端实现后自动生效，无需改动前端。
 const params: Record<string, unknown> = {
 page,
 page_size: PAGE_SIZE,
 }

 if (filters.status) params.status = filters.status
 // is_vip / role / search 后端支持后取消注释即可：
 // if (filters.is_vip) params.is_vip = filters.is_vip === 'true'
 // if (filters.role) params.role = filters.role
 // if (filters.search) params.search = filters.search

 const res = await usersApi.list(params as any)
 users.value = res.items
 total.value = res.total
 } catch {
 error.value = '获取用户列表失败，请重试'
 users.value = []
 total.value = 0
 } finally {
 loading.value = false
 }
}

onMounted(() => loadUsers(1))
</script>

<style scoped>
.users-page { }
</style>