<template>
 <div class="pagination-bar">
 <span class="page-info">
 共 <strong>{{ total }}</strong> 条，第
 <strong>{{ currentPage }}</strong> /
 <strong>{{ totalPages }}</strong> 页
 </span>

 <div class="page-btns">
 <button
 class="btn btn-ghost pg-btn"
 :disabled="currentPage <= 1 || disabled"
 @click="emit('change', currentPage - 1)"
 >
 ‹ 上一页
 </button>

 <!-- 页码按钮 -->
 <template v-for="p in visiblePages" :key="p">
 <!-- 省略号 -->
 <span v-if="p === -1" class="pg-ellipsis">…</span>
 <button
 v-else
 class="btn pg-num"
 :class="{ 'pg-active': p === currentPage }"
 :disabled="disabled"
 @click="emit('change', p)"
 >
 {{ p }}
 </button>
 </template>

 <button
 class="btn btn-ghost pg-btn"
 :disabled="currentPage >= totalPages || disabled"
 @click="emit('change', currentPage + 1)"
 >
 下一页 ›
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

const emit = defineEmits<{ change: [page: number] }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

/**
 * 生成带省略号的页码序列。
 * -1 表示省略号占位。
 */
const visiblePages = computed<number[]>(() => {
 const total = totalPages.value
 const cur = props.currentPage

 if (total <= 7) {
 return Array.from({ length: total }, (_, i) => i + 1)
 }

 const pages: number[] = []

 // 始终显示首页
 pages.push(1)

 const left = Math.max(2, cur - 1)
 const right = Math.min(total - 1, cur + 1)

 if (left > 2) pages.push(-1) // 左省略
 for (let i = left; i <= right; i++) pages.push(i)
 if (right < total - 1) pages.push(-1) // 右省略

 // 始终显示末页
 pages.push(total)

 return pages
})
</script>

<style scoped>
.pagination-bar {
 display: flex;
 align-items: center;
 justify-content: space-between;
 padding: 12px 18px;
 border-top: 1px solid var(--color-border);
 flex-wrap: wrap;
 gap: 10px;
}

.page-info {
 font-size: 12px;
 color: var(--color-text-muted);
}

.page-info strong {
 color: var(--color-text);
 font-weight: 600;
}

.page-btns {
 display: flex;
 align-items: center;
 gap: 4px;
}

.pg-btn {
 padding: 4px 10px;
 font-size: 12px;
}

.pg-num {
 min-width: 32px;
 padding: 4px 6px;
 font-size: 13px;
 background: var(--color-surface-2);
 border: 1px solid var(--color-border);
 border-radius: 4px;
 color: var(--color-text-muted);
 transition: all 0.15s;
}

.pg-num:hover:not(:disabled):not(.pg-active) {
 color: var(--color-text);
 border-color: var(--color-text-muted);
}

.pg-active {
 background: var(--color-primary) !important;
 color: #fff !important;
 border-color: var(--color-primary) !important;
}

.pg-ellipsis {
 padding: 0 4px;
 color: var(--color-text-muted);
 font-size: 13px;
 line-height: 1;
 user-select: none;
}
</style>