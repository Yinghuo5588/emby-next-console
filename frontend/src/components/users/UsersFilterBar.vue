<template>
  <div class="filter-bar card">
    <input v-model="localSearch" class="search-input" placeholder="搜索用户名..." @keyup.enter="emitSearch" />
    <select v-model="filters.status" @change="emit('update:modelValue', { ...filters })">
      <option value="">全部状态</option>
      <option value="active">活跃</option>
      <option value="disabled">禁用</option>
      <option value="expired">过期</option>
    </select>
    <select v-model="filters.is_vip" @change="emit('update:modelValue', { ...filters })">
      <option value="">全部类型</option>
      <option value="true">VIP</option>
      <option value="false">普通</option>
    </select>
    <select v-model="filters.role" @change="emit('update:modelValue', { ...filters })">
      <option value="">全部角色</option>
      <option value="admin">管理员</option>
      <option value="user">普通用户</option>
    </select>
    <button class="btn btn-primary" @click="emitSearch">搜索</button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'

export interface FilterValues { search: string; status: string; is_vip: string; role: string }

const props = defineProps<{ modelValue: FilterValues }>()
const emit = defineEmits<{ 'update:modelValue': [v: FilterValues]; search: [v: string] }>()

const localSearch = ref(props.modelValue.search)
const filters = reactive({ ...props.modelValue })

watch(() => props.modelValue, (v) => { Object.assign(filters, v); localSearch.value = v.search }, { deep: true })

function emitSearch() {
  filters.search = localSearch.value
  emit('update:modelValue', { ...filters })
  emit('search', localSearch.value)
}
</script>

<style scoped>
.filter-bar { display: flex; gap: 8px; padding: 12px 16px; flex-wrap: wrap; align-items: center; }
.search-input { flex: 1; min-width: 120px; }
select { min-width: 80px; flex-shrink: 0; }
@media (max-width: 768px) {
  .filter-bar { flex-direction: column; }
  .search-input, select, .btn { width: 100%; }
}
</style>
