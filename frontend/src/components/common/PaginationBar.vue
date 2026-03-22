<template>
  <div class="pagination-bar" :class="{ disabled }">
    <div class="pagination-info">
      {{ startItem }}-{{ endItem }} / {{ total }}
    </div>
    <n-pagination
      :page="currentPage"
      :page-size="pageSize"
      :item-count="total"
      :disabled="disabled"
      @update:page="$emit('page-change', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  total: number
  currentPage: number
  pageSize: number
  disabled?: boolean
}>()

defineEmits<{
  'page-change': [page: number]
}>()

const startItem = computed(() => Math.min((props.currentPage - 1) * props.pageSize + 1, props.total))
const endItem = computed(() => Math.min(props.currentPage * props.pageSize, props.total))
</script>

<style scoped>
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.pagination-bar.disabled { opacity: 0.6; pointer-events: none; }
.pagination-info { font-size: 0.9rem; color: var(--text-muted); }
@media (max-width: 767px) {
  .pagination-bar { flex-direction: column; gap: 0.75rem; padding: 1rem; }
}
</style>
