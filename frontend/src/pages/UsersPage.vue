<template>
  <div>
    <PageHeader title="用户管理" :desc="total > 0 ? `共 ${total} 名用户` : ''" />
    <UsersFilterBar v-model="filters" style="margin-bottom: 12px" @search="loadUsers(1)" @update:model-value="loadUsers(1)" />
    <UsersTable :items="users" :loading="loading" :error="error" @retry="loadUsers(currentPage)" />
    <PaginationBar v-if="!error" :total="total" :current-page="currentPage" :page-size="20" :disabled="loading" @change="loadUsers" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import UsersFilterBar from '@/components/users/UsersFilterBar.vue'
import UsersTable from '@/components/users/UsersTable.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { usersApi } from '@/api/users'

const users = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const loading = ref(false)
const error = ref<string | null>(null)
const filters = reactive({ search: '', status: '', is_vip: '', role: '' })

async function loadUsers(page: number) {
  loading.value = true; error.value = null; currentPage.value = page
  try {
    const res = await usersApi.list({ page, page_size: 20 })
    users.value = res.data?.items ?? []; total.value = res.data?.total ?? 0
  } catch { error.value = '获取用户列表失败' }
  finally { loading.value = false }
}

onMounted(() => loadUsers(1))
</script>
