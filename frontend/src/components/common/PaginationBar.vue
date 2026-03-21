<template>
  <div class="pagination-bar" :class="{ disabled }">
    <div class="pagination-info">
      Showing {{ startItem }}-{{ endItem }} of {{ total }} items
    </div>
    
    <div class="pagination-controls">
      <button 
        class="pagination-button prev-button" 
        :disabled="disabled || currentPage === 1"
        @click="$emit('page-change', currentPage - 1)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Previous</span>
      </button>
      
      <div class="page-numbers">
        <template v-for="page in visiblePages" :key="page">
          <button 
            v-if="page === 'ellipsis'"
            class="page-button ellipsis"
            disabled
          >
            ...
          </button>
          <button 
            v-else
            class="page-button"
            :class="{ active: page === currentPage }"
            :disabled="disabled"
            @click="$emit('page-change', page)"
          >
            {{ page }}
          </button>
        </template>
      </div>
      
      <button 
        class="pagination-button next-button" 
        :disabled="disabled || currentPage === totalPages"
        @click="$emit('page-change', currentPage + 1)"
      >
        <span>Next</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
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

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))
const startItem = computed(() => Math.min((props.currentPage - 1) * props.pageSize + 1, props.total))
const endItem = computed(() => Math.min(props.currentPage * props.pageSize, props.total))

const visiblePages = computed(() => {
  const pages: (number | 'ellipsis')[] = []
  const maxVisible = 5
  
  if (totalPages.value <= maxVisible) {
    // Show all pages
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // Always show first page
    pages.push(1)
    
    // Calculate start and end of middle pages
    let start = Math.max(2, props.currentPage - 1)
    let end = Math.min(totalPages.value - 1, props.currentPage + 1)
    
    // Adjust if we're near the start
    if (props.currentPage <= 3) {
      end = 4
    }
    
    // Adjust if we're near the end
    if (props.currentPage >= totalPages.value - 2) {
      start = totalPages.value - 3
    }
    
    // Add ellipsis after first page if needed
    if (start > 2) {
      pages.push('ellipsis')
    }
    
    // Add middle pages
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    
    // Add ellipsis before last page if needed
    if (end < totalPages.value - 1) {
      pages.push('ellipsis')
    }
    
    // Always show last page
    if (totalPages.value > 1) {
      pages.push(totalPages.value)
    }
  }
  
  return pages
})
</script>

<style scoped>
.pagination-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 16px;
}

.pagination-bar.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.pagination-info {
  font-size: 0.95rem;
  color: var(--text-muted);
  font-weight: 500;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.625rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 100px;
  justify-content: center;
}

.pagination-button:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--brand);
  color: var(--brand);
}

.pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 0.5rem;
}

.page-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-button:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--brand);
}

.page-button.active {
  background: var(--brand);
  color: white;
  border-color: var(--brand);
}

.page-button.ellipsis {
  border: none;
  background: transparent;
  cursor: default;
  width: 32px;
}

.page-button.ellipsis:hover {
  background: transparent;
  border: none;
}

/* Responsive */
@media (max-width: 767px) {
  .pagination-bar {
    padding: 1.25rem;
    border-radius: 12px;
    gap: 1rem;
  }
  
  .pagination-controls {
    gap: 0.75rem;
  }
  
  .pagination-button {
    min-width: 80px;
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }
  
  .page-button {
    width: 36px;
    height: 36px;
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .page-numbers {
    display: none;
  }
}
</style>