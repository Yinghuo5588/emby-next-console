<template>
  <n-card size="small">
    <n-space size="small" wrap>
      <n-input v-model:value="localSearch" placeholder="搜索用户名..." size="small" style="width: 200px" clearable @keyup.enter="emitSearch" />
      <n-select v-model:value="filters.status" :options="statusOptions" placeholder="全部状态" size="small" style="width: 120px" clearable @update:value="emitUpdate" />
      <n-select v-model:value="filters.is_vip" :options="vipOptions" placeholder="全部类型" size="small" style="width: 120px" clearable @update:value="emitUpdate" />
      <n-select v-model:value="filters.role" :options="roleOptions" placeholder="全部角色" size="small" style="width: 120px" clearable @update:value="emitUpdate" />
      <n-button type="primary" size="small" @click="emitSearch">搜索</n-button>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { NCard, NSpace, NInput, NSelect, NButton } from 'naive-ui'

export interface FilterValues { search: string; status: string; is_vip: string; role: string }

const props = defineProps<{ modelValue: FilterValues }>()
const emit = defineEmits<{ 'update:modelValue': [v: FilterValues]; search: [v: string] }>()

const localSearch = ref(props.modelValue.search)
const filters = reactive({ ...props.modelValue })

watch(() => props.modelValue, (v) => { Object.assign(filters, v); localSearch.value = v.search }, { deep: true })

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '活跃', value: 'active' },
  { label: '禁用', value: 'disabled' },
  { label: '过期', value: 'expired' },
]
const vipOptions = [
  { label: '全部类型', value: '' },
  { label: 'VIP', value: 'true' },
  { label: '普通', value: 'false' },
]
const roleOptions = [
  { label: '全部角色', value: '' },
  { label: '管理员', value: 'admin' },
  { label: '普通用户', value: 'user' },
]

function emitUpdate() { emit('update:modelValue', { ...filters }) }
function emitSearch() { filters.search = localSearch.value; emitUpdate(); emit('search', localSearch.value) }
</script>
