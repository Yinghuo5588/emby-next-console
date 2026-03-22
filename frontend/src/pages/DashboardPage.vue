<template>
  <div>
    <PageHeader title="仪表盘" desc="系统实时总览">
      <template #actions>
        <n-button quaternary size="small" :loading="loading" @click="refresh">刷新</n-button>
      </template>
    </PageHeader>

    <div class="stat-grid">
      <StatCard label="总用户" :value="summary?.overview?.total_users ?? 0" />
      <StatCard label="今日活跃" :value="summary?.overview?.active_users_today ?? 0" />
      <StatCard label="在线会话" :value="summary?.overview?.current_active_sessions ?? 0" :highlight="(summary?.overview?.current_active_sessions ?? 0) > 0" />
      <StatCard label="媒体总量" :value="summary?.overview?.total_media_count ?? 0" />
      <StatCard label="今日播放" :value="summary?.playback?.today_play_count ?? 0" />
      <StatCard label="未读通知" :value="summary?.notifications?.unread_count ?? 0" :danger="(summary?.notifications?.unread_count ?? 0) > 0" />
    </div>

    <div class="body-grid">
      <div class="left">
        <n-card title="播放趋势" size="small">
          <template #header-extra>
            <n-button-group size="small">
              <n-button v-for="d in [7, 14, 30]" :key="d" :type="trendDays === d ? 'primary' : 'default'" @click="trendDays = d; fetchTrends()">{{ d }}天</n-button>
            </n-button-group>
          </template>
          <LoadingState v-if="trendsLoading" height="200px" />
          <TrendChart v-else-if="trends.length > 0" :x-data="trends.map((t: any) => (t.date || '').slice(5))" :series="[{ name: '播放', data: trends.map((t: any) => t.play_count ?? 0) }, { name: '活跃', data: trends.map((t: any) => t.active_users ?? 0), color: '#34c759' }]" />
          <n-empty v-else description="暂无趋势数据" />
        </n-card>

        <n-card title="当前播放" size="small">
          <template #header-extra>
            <n-tag type="success" size="small">{{ sessions.length }} 活跃</n-tag>
          </template>
          <LoadingState v-if="sessionsLoading && sessions.length === 0" compact />
          <n-empty v-else-if="sessions.length === 0" description="暂无活跃会话" />
          <n-list v-else>
            <n-list-item v-for="s in sessions" :key="s.session_id">
              <template #prefix>
                <n-badge dot type="success" />
              </template>
              <div>
                <div style="font-size:13px;font-weight:500">{{ s.username }}</div>
                <div style="font-size:12px;color:var(--text-muted)">{{ s.media_name }}</div>
              </div>
            </n-list-item>
          </n-list>
        </n-card>
      </div>

      <div class="right">
        <n-card title="风控" size="small">
          <template #header-extra>
            <router-link to="/risk" style="font-size:12px;color:var(--brand)">详情 →</router-link>
          </template>
          <div class="summary-row"><span>待处理</span><n-tag :type="(summary?.risk?.open_risk_count ?? 0) > 0 ? 'warning' : 'success'" size="small">{{ summary?.risk?.open_risk_count ?? 0 }}</n-tag></div>
          <div class="summary-row"><span>高危</span><n-tag :type="(summary?.risk?.high_risk_count ?? 0) > 0 ? 'error' : 'success'" size="small">{{ summary?.risk?.high_risk_count ?? 0 }}</n-tag></div>
        </n-card>
        <n-card title="今日播放" size="small">
          <template #header-extra>
            <router-link to="/stats" style="font-size:12px;color:var(--brand)">统计 →</router-link>
          </template>
          <div class="summary-row"><span>播放次数</span><span>{{ summary?.playback?.today_play_count ?? 0 }}</span></div>
          <div class="summary-row"><span>峰值并发</span><span>{{ summary?.playback?.peak_concurrent_today ?? 0 }}</span></div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NButton, NButtonGroup, NTag, NList, NListItem, NBadge, NEmpty } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { dashboardApi } from '@/api/dashboard'
import { statsApi } from '@/api/stats'

const summary = ref<any>(null)
const sessions = ref<any[]>([])
const trends = ref<any[]>([])
const trendsLoading = ref(false)
const sessionsLoading = ref(false)
const trendDays = ref(7)
const loading = ref(false)

async function fetchSummary() {
  try {
    const res = await dashboardApi.summary()
    if (res.success && res.data) {
      summary.value = res.data
      sessions.value = res.data.sessions ?? []
    }
  } catch (e) { console.error('获取仪表盘数据失败:', e) }
}

async function fetchTrends() {
  trendsLoading.value = true
  try {
    const res = await statsApi.trends(trendDays.value)
    trends.value = res.data ?? []
  } catch { trends.value = [] }
  finally { trendsLoading.value = false }
}

async function refresh() {
  loading.value = true
  await Promise.all([fetchSummary(), fetchTrends()])
  loading.value = false
}

onMounted(refresh)
</script>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
.body-grid { display: grid; grid-template-columns: 1fr 280px; gap: 16px; align-items: start; }
.left, .right { display: flex; flex-direction: column; gap: 16px; }
.summary-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.summary-row:last-child { border-bottom: none; }
@media (max-width: 768px) { .body-grid { grid-template-columns: 1fr; } }
</style>
