<template>
 <div class="filter-bar card">
 <span class="filter-label">筛选：</span>
 <select
 :value="modelValue.status"
 class="filter-select"
 @change="update('status', ($event.target as HTMLSelectElement).value)"
 >
 <option value="">全部状态</option>
 <option value="open">待处理</option>
 <option value="ignored">已忽略</option>
 <option value="resolved">已解决</option>
 </select>
 <select
 :value="modelValue.severity"
 class="filter-select"
 @change="update('severity', ($event.target as HTMLSelectElement).value)"
 >
 <option value="">全部等级</option>
 <option value="high">高危</option>
 <option value="medium">中危</option>
 <option value="low">低危</option>
 </select>
 <button
 v-if="modelValue.status || modelValue.severity"
 class="btn btn-ghost reset-btn"
 @click="emit('update:modelValue', { status: '', severity: '' })"
 >
 × 清除筛选
 </button>
 </div>
</template>

<script setup lang="ts">
export interface RiskFilterValues {
 status: string
 severity: string
}

const props = defineProps<{ modelValue: RiskFilterValues }>()
const emit = defineEmits<{ 'update:modelValue': [v: RiskFilterValues] }>()

function update(key: keyof RiskFilterValues, value: string) {
 emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<style scoped>
.filter-bar {
 display: flex;
 align-items: center;
 gap: 10px;
 padding: 12px 16px;
 flex-wrap: wrap;
}

.filter-label {
 font-size: 13px;
 color: var(--color-text-muted);
 flex-shrink: 0;
}

.filter-select {
 padding: 6px 10px;
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

.reset-btn {
 padding: 5px 10px;
 font-size: 12px;
 color: var(--color-text-muted);
}

.reset-btn:hover {
 color: var(--color-text);
}
</style>