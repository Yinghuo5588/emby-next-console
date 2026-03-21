<template>
 <div class="filter-bar card">
 <div class="filter-left">
 <div class="search-wrap">
 <input
 v-model="localSearch"
 class="search-input"
 placeholder="搜索用户名 / 显示名..."
 @keyup.enter="emitSearch"
 />
 <button class="btn btn-primary search-btn" @click="emitSearch">搜索</button>
 </div>
 </div>
 <div class="filter-right">
 <select
 :value="modelValue.status"
 class="filter-select"
 @change="emit('update:modelValue', { ...modelValue, status: ($event.target as HTMLSelectElement).value })"
 >
 <option value="">全部状态</option>
 <option value="active">活跃</option>
 <option value="disabled">禁用</option>
 <option value="expired">已过期</option>
 </select>
 <select
 :value="modelValue.is_vip"
 class="filter-select"
 @change="emit('update:modelValue', { ...modelValue, is_vip: ($event.target as HTMLSelectElement).value })"
 >
 <option value="">全部类型</option>
 <option value="true">VIP</option>
 <option value="false">普通</option>
 </select>
 <select
 :value="modelValue.role"
 class="filter-select"
 @change="emit('update:modelValue', { ...modelValue, role: ($event.target as HTMLSelectElement).value })"
 >
 <option value="">全部角色</option>
 <option value="admin">管理员</option>
 <option value="user">普通用户</option>
 </select>
 </div>
 </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export interface FilterValues {
 search: string
 status: string
 is_vip: string
 role: string
}

const props = defineProps<{
 modelValue: FilterValues
}>()

const emit = defineEmits<{
 'update:modelValue': [value: FilterValues]
 search: [value: string]
}>()

// 搜索框本地维护，回车 / 点击才触发查询
const localSearch = ref(props.modelValue.search)

watch(() => props.modelValue.search, (v) => {
 localSearch.value = v
})

function emitSearch() {
 emit('update:modelValue', { ...props.modelValue, search: localSearch.value })
 emit('search', localSearch.value)
}
</script>

<style scoped>
.filter-bar {
 display: flex;
 align-items: center;
 justify-content: space-between;
 gap: 16px;
 padding: 12px 16px;
 flex-wrap: wrap;
}

.filter-left,
.filter-right {
 display: flex;
 align-items: center;
 gap: 8px;
 flex-wrap: wrap;
}

.search-wrap {
 display: flex;
}

.search-input {
 width: 220px;
 padding: 7px 12px;
 background: var(--color-surface-2);
 border: 1px solid var(--color-border);
 border-right: none;
 border-radius: 6px 0 0 6px;
 color: var(--color-text);
 font-size: 13px;
 outline: none;
 transition: border-color 0.15s;
}

.search-input:focus {
 border-color: var(--color-primary);
}

.search-btn {
 border-radius: 0 6px 6px 0;
 padding: 7px 14px;
}

.filter-select {
 padding: 7px 10px;
 background: var(--color-surface-2);
 border: 1px solid var(--color-border);
 border-radius: 6px;
 color: var(--color-text);
 font-size: 13px;
 outline: none;
 cursor: pointer;
 transition: border-color 0.15s;
}

.filter-select:focus {
 border-color: var(--color-primary);
}
</style>