<template>
  <div class="users-table">
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!items || items.length === 0" message="No users found" />
    
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>Status</th>
            <th>Role</th>
            <th>VIP</th>
            <th>Last Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in items" :key="user.id">
            <td>
              <div class="user-cell">
                <div class="avatar">
                  {{ user.name?.charAt(0) || 'U' }}
                </div>
                <div class="user-info">
                  <div class="name">{{ user.name || 'Unknown' }}</div>
                  <div class="email">{{ user.email || 'No email' }}</div>
                </div>
              </div>
            </td>
            <td>
              <span :class="`tag tag-${getStatusColor(user.status)}`">
                {{ user.status || 'unknown' }}
              </span>
            </td>
            <td>
              <span :class="`tag tag-${getRoleColor(user.role)}`">
                {{ user.role || 'user' }}
              </span>
            </td>
            <td>
              <span v-if="user.is_vip" class="tag tag-yellow">VIP</span>
              <span v-else class="tag tag-gray">-</span>
            </td>
            <td>
              <div class="last-active">
                {{ formatDate(user.last_active) }}
              </div>
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-ghost btn-sm" @click="$emit('view', user)">
                  View
                </button>
                <button class="btn btn-ghost btn-sm" @click="$emit('edit', user)">
                  Edit
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'

interface User {
  id: string
  name?: string
  email?: string
  status?: string
  role?: string
  is_vip?: boolean
  last_active?: string
}

const props = defineProps<{
  items: User[]
  loading: boolean
  error?: string
}>()

const emit = defineEmits<{
  view: [user: User]
  edit: [user: User]
}>()

const getStatusColor = (status?: string) => {
  switch (status?.toLowerCase()) {
    case 'active': return 'green'
    case 'inactive': return 'gray'
    case 'banned': return 'red'
    default: return 'gray'
  }
}

const getRoleColor = (role?: string) => {
  switch (role?.toLowerCase()) {
    case 'admin': return 'red'
    case 'user': return 'blue'
    case 'guest': return 'gray'
    default: return 'gray'
  }
}

const formatDate = (date?: string) => {
  if (!date) return 'Never'
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`
  return d.toLocaleDateString()
}
</script>

<style scoped>
.users-table {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.name {
  font-weight: 500;
  color: var(--text);
}

.email {
  font-size: 12px;
  color: var(--text-muted);
}

.last-active {
  color: var(--text-muted);
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.tag {
  font-size: 11px;
  padding: 2px 6px;
}

@media (max-width: 768px) {
  table {
    min-width: 800px;
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>