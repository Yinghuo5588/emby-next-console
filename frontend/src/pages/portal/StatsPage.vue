<template>
  <div>
    <h3 class="page-title">观看统计</h3>

    <LoadingState v-if="loading" height="120px" />
    <div v-else>
      <div class="stat-grid">
        <StatCard label="活跃设备" :value="stats?.active_sessions ?? 0" />
      </div>

      <div v-if="stats?.now_playing?.length" class="section">
        <div class="section-title">正在播放</div>
        <div v-for="(item, i) in stats.now_playing" :key="i" class="card np-card">
          <div class="np-item">{{ item.item }}</div>
          <div class="np-device muted">{{ item.device }}</div>
        </div>
      </div>

      <EmptyState v-if="!stats?.now_playing?.length" title="暂无播放记录" desc="当前没有活跃的播放会话" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import StatCard from '@/components/common/StatCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { portalApi, type PortalStats } from '@/api/portal'

const loading = ref(true)
const stats = ref<PortalStats | null>(null)

onMounted(async () => {
  try {
    const res = await portalApi.stats()
    stats.value = res.data ?? null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 18px; margin-bottom: 16px; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
.section { margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.np-card { padding: 12px; margin-bottom: 8px; }
.np-item { font-weight: 500; }
.np-device { font-size: 12px; margin-top: 4px; }
.muted { color: var(--text-muted); }
</style>