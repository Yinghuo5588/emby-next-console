<template>
  <div class="users-page">
    <PageHeader title="Users" desc="Manage system users and permissions">
      <template #actions>
        <button class="btn btn-primary" @click="handleAddUser">
          Add User
        </button>
      </template>
    </PageHeader>
    
    <div class="users-content">
      <UsersFilterBar v-model="filter" />
      
      <div class="table-section">
        <UsersTable
          :items="filteredUsers"
          :loading="loading"
          :error="error"
          @view="handleViewUser"
          @edit="handleEditUser"
        />
        
        <PaginationBar
          v-if="!loading && !error && filteredUsers.length > 0"
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-items="totalItems"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import UsersFilterBar from '@/components/users/UsersFilterBar.vue'
import UsersTable from '@/components/users/UsersTable.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { fetchUsers } from '@/api/users'

interface User {
  id: string
  name?: string
  email?: string
  status?: string
  role?: string
  is_vip?: boolean
  last_active?: string
}

interface FilterValues {
  search: string
  status: string
  is_vip: string
  role: string
}

const router = useRouter()

const loading = ref(true)
const error = ref('')
const users = ref<User[]>([])
const filter = ref<FilterValues>({
  search: '',
  status: '',
  is_vip: '',
  role: ''
})
const currentPage = ref(1)
const pageSize = 20
const totalItems = ref(0)

const filteredUsers = computed(() => {
  let filtered = [...users.value]
  
  if (filter.value.search) {
    const search = filter.value.search.toLowerCase()
    filtered = filtered.filter(user => 
      user.name?.toLowerCase().includes(search) ||
      user.email?.toLowerCase().includes(search)
    )
  }
  
  if (filter.value.status) {
    filtered = filtered.filter(user => user.status === filter.value.status)
  }
  
  if (filter.value.is_vip !== '') {
    const isVip = filter.value.is_vip === 'true'
    filtered = filtered.filter(user => user.is_vip === isVip)
  }
  
  if (filter.value.role) {
    filtered = filtered.filter(user => user.role === filter.value.role)
  }
  
  totalItems.value = filtered.length
  
  // Pagination
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filtered.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(totalItems.value / pageSize)
})

const fetchUserData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const data = await fetchUsers()
    users.value = data.users || []
    
    // Mock data for demonstration
    if (users.value.length === 0) {
      users.value = [
        { id: '1', name: 'John Doe', email: 'john@example.com', status: 'active', role: 'admin', is_vip: true, last_active: new Date().toISOString() },
        { id: '2', name: 'Jane Smith', email: 'jane@example.com', status: 'active', role: 'user', is_vip: true, last_active: new Date(Date.now() - 86400000).toISOString() },
        { id: '3', name: 'Bob Johnson', email: 'bob@example.com', status: 'inactive', role: 'user', is_vip: false, last_active: new Date(Date.now() - 172800000).toISOString() },
        { id: '4', name: 'Alice Brown', email: 'alice@example.com', status: 'active', role: 'guest', is_vip: false, last_active: new Date(Date.now() - 3600000).toISOString() },
        { id: '5', name: 'Charlie Wilson', email: 'charlie@example.com', status: 'banned', role: 'user', is_vip: false, last_active: new Date(Date.now() - 2592000000).toISOString() },
        { id: '6', name: 'David Lee', email: 'david@example.com', status: 'active', role: 'admin', is_vip: true, last_active: new Date().toISOString() },
        { id: '7', name: 'Eva Garcia', email: 'eva@example.com', status: 'active', role: 'user', is_vip: true, last_active: new Date(Date.now() - 43200000).toISOString() },
        { id: '8', name: 'Frank Miller', email: 'frank@example.com', status: 'inactive', role: 'user', is_vip: false, last_active: new Date(Date.now() - 604800000).toISOString() }
      ]
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load users'
  } finally {
    loading.value = false
  }
}

const handleViewUser = (user: User) => {
  router.push(`/users/${user.id}`)
}

const handleEditUser = (user: User) => {
  // TODO: Implement edit user modal
  console.log('Edit user:', user)
}

const handleAddUser = () => {
  // TODO: Implement add user modal
  console.log('Add user')
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

onMounted(() => {
  fetchUserData()
})
</script>

<style scoped>
.users-page {
  padding-bottom: 2rem;
}

.users-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.table-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>