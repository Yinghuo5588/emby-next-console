<template>
  <div class="risk-filter-bar">
    <div class="filter-group">
      <label>Status</label>
      <select v-model="localFilter.status" @change="updateFilter">
        <option value="">All Status</option>
        <option value="open">Open</option>
        <option value="investigating">Investigating</option>
        <option value="resolved">Resolved</option>
        <option value="dismissed">Dismissed</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label>Severity</label>
      <select v-model="localFilter.severity" @change="updateFilter">
        <option value="">All Severity</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
        <option value="info">Info</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label>Time Range</label>
      <select v-model="localFilter.timeRange" @change="updateFilter">
        <option value="24h">Last 24 hours</option>
        <option value="7d">Last 7 days</option>
        <option value="30d">Last 30 days</option>
        <option value="all">All time</option>
      </select>
    </div>
    
    <button class="btn btn-ghost" @click="resetFilters">
      Reset
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface FilterValues {
  status: string
  severity: string
  timeRange: string
}

const props = defineProps<{
  modelValue: FilterValues
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FilterValues]
}>()

const defaultFilter: FilterValues = {
  status: '',
  severity: '',
  timeRange: '24h'
}

const localFilter = ref<FilterValues>({ ...props.modelValue })

watch(() => props.modelValue, (newVal) => {
  localFilter.value = { ...newVal }
}, { deep: true })

const updateFilter = () => {
  emit('update:modelValue', { ...localFilter.value })
}

const resetFilters = () => {
  localFilter.value = { ...defaultFilter }
  updateFilter()
}
</script>

<style scoped>
.risk-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 150px;
}

.filter-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
}

.filter-group select {
  width: 100%;
}

@media (max-width: 768px) {
  .risk-filter-bar {
    flex-direction: column;
  }
  
  .filter-group {
    min-width: 100%;
  }
}
</style>