<template>
  <div class="risk-events-table">
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <EmptyState v-else-if="!items || items.length === 0" message="No risk events found" />
    
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>Event</th>
            <th>Severity</th>
            <th>Status</th>
            <th>User</th>
            <th>IP Address</th>
            <th>Time</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in items" :key="event.id">
            <td>
              <div class="event-cell">
                <div class="event-title">{{ event.title }}</div>
                <div class="event-desc">{{ event.description }}</div>
              </div>
            </td>
            <td>
              <span :class="`tag tag-${getSeverityColor(event.severity)}`">
                {{ event.severity }}
              </span>
            </td>
            <td>
              <span :class="`tag tag-${getStatusColor(event.status)}`">
                {{ event.status }}
              </span>
            </td>
            <td>
              <div v-if="event.user" class="user-cell">
                <div class="avatar">
                  {{ event.user.name?.charAt(0) || 'U' }}
                </div>
                <div class="user-info">
                  <div class="name">{{ event.user.name || 'Unknown' }}</div>
                  <div class="email">{{ event.user.email || 'No email' }}</div>
                </div>
              </div>
              <span v-else class="tag tag-gray">System</span>
            </td>
            <td>
              <code class="ip-address">{{ event.ip_address || 'N/A' }}</code>
            </td>
            <td>
              <div class="time-cell">
                {{ formatTime(event.created_at) }}
              </div>
            </td>
            <td>
              <div class="actions">
                <button 
                  v-if="event.status === 'open'" 
                  class="btn btn-ghost btn-sm" 
                  @click="$emit('investigate', event)"
                >
                  Investigate
                </button>
                <button 
                  v-if="event.status === 'investigating'" 
                  class="btn btn-ghost btn-sm" 
                  @click="$emit('resolve', event)"
                >
                  Resolve
                </button>
                <button 
                  v-if="event.status !== 'dismissed'" 
                  class="btn btn-ghost btn-sm" 
                  @click="$emit('dismiss', event)"
                >
                  Dismiss
                </button>
                <button 
                  class="btn btn-ghost btn-sm" 
                  @click="$emit('view', event)"
                >
                  Details
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
}

interface RiskEvent {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'open' | 'investigating' | 'resolved' | 'dismissed'
  user?: User
  ip_address?: string
  created_at: string
}

const props = defineProps<{
  items: RiskEvent[]
  loading: boolean
  error?: string
}>()

const emit = defineEmits<{
  view: [event: RiskEvent]
  investigate: [event: RiskEvent]
  resolve: [event: RiskEvent]
  dismiss: [event: RiskEvent]
}>()

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'red'
    case 'high': return 'red'
    case 'medium': return 'yellow'
    case 'low': return 'blue'
    case 'info': return 'gray'
    default: return 'gray'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'open': return 'red'
    case 'investigating': return 'yellow'
    case 'resolved': return 'green'
    case 'dismissed': return 'gray'
    default: return 'gray'
  }
}

const formatTime = (date: string) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return d.toLocaleDateString()
}
</script>

<style scoped>
.risk-events-table {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.event-cell {
  max-width: 300px;
}

.event-title {
  font-weight: 500;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.event-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.name {
  font-weight: 500;
  color: var(--text);
  font-size: 12px;
}

.email {
  font-size: 11px;
  color: var(--text-muted);
}

.ip-address {
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
}

.time-cell {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 2px 6px;
  font-size: 11px;
}

.tag {
  font-size: 10px;
  padding: 1px 4px;
}

@media (max-width: 768px) {
  table {
    min-width: 1000px;
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>