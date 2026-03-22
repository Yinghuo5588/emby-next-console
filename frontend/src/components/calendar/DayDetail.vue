<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal card" style="max-width: 500px;">
      <div class="modal-head">
        <h3>{{ date }} 更新</h3>
        <button class="btn btn-ghost" @click="$emit('close')">✕</button>
      </div>
      <div v-if="entries.length === 0" class="muted" style="text-align:center; padding: 24px;">
        无更新内容
      </div>
      <div v-else class="dd-list">
        <div v-for="e in entries" :key="e.id" class="dd-item card">
          <div v-if="e.backdrop_url" class="dd-thumb">
            <img :src="e.backdrop_url" loading="lazy" />
          </div>
          <div class="dd-body">
            <div class="dd-series">{{ e.series_name }}</div>
            <div class="dd-ep">S{{ String(e.season_number).padStart(2, '0') }}E{{ String(e.episode_number).padStart(2, '0') }} {{ e.episode_title }}</div>
            <div v-if="e.overview" class="dd-overview">{{ e.overview }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CalendarEntry } from '@/api/calendar'

defineProps<{
  date: string
  entries: CalendarEntry[]
}>()

defineEmits<{ close: [] }>()
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.dd-list { display: flex; flex-direction: column; gap: 8px; }
.dd-item { display: flex; gap: 12px; padding: 12px; overflow: hidden; }
.dd-thumb { width: 80px; height: 45px; border-radius: 4px; overflow: hidden; flex-shrink: 0; }
.dd-thumb img { width: 100%; height: 100%; object-fit: cover; }
.dd-body { flex: 1; min-width: 0; }
.dd-series { font-weight: 600; font-size: 14px; }
.dd-ep { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.dd-overview { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>