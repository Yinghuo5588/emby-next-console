<template>
  <div class="page">
    <PageHeader title="质量盘点" :subtitle="lastScanTime ? `上次扫描: ${lastScanTime}` : undefined">
      <template #actions>
        <n-button size="small" :type="scanRunning ? 'warning' : 'primary'" :loading="scanRunning" @click="startScan">
          {{ scanRunning ? `扫描中 ${scanStatus.scanned}/${scanStatus.total}` : '开始扫描' }}
        </n-button>
      </template>
    </PageHeader>

    <div class="body">
      <!-- 空状态 -->
      <div v-if="!scanRunning && overview.total === 0 && !overview.scan?.finished_at" class="empty-state">
        <div class="empty-icon">🎬</div>
        <div class="empty-title">还没有扫描数据</div>
        <div class="empty-desc">点击「开始扫描」获取媒体库质量信息</div>
        <n-button type="primary" size="large" @click="startScan">开始扫描</n-button>
      </div>

      <template v-else>
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">分辨率分布</div>
            <div class="stat-bars">
              <div v-for="(count, key) in overview.resolution" :key="key" class="stat-bar">
                <span class="bar-label">{{ key }}</span>
                <div class="bar-track"><div class="bar-fill" :style="{ width: barWidth(count) + '%' }" :class="'bar-' + key.toLowerCase()" /></div>
                <span class="bar-value">{{ count }}</span>
              </div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-label">动态范围</div>
            <div class="stat-bars">
              <div v-for="(count, key) in overview.video_range" :key="key" class="stat-bar">
                <span class="bar-label">{{ key }}</span>
                <div class="bar-track"><div class="bar-fill" :style="{ width: barWidth(count) + '%' }" :class="'bar-vr-' + key.toLowerCase()" /></div>
                <span class="bar-value">{{ count }}</span>
              </div>
            </div>
          </div>
          <div class="stat-total">
            共 <strong>{{ overview.total }}</strong> 个媒体项
          </div>
        </div>

        <!-- 筛选 Tab -->
        <div class="filter-tabs">
          <button v-for="f in filterOptions" :key="f.value" class="filter-tab" :class="{ active: activeFilter === f.value }" @click="activeFilter = f.value; loadItems()">
            {{ f.label }}
            <span v-if="f.count != null" class="filter-count">{{ f.count }}</span>
          </button>
        </div>

        <!-- 媒体列表 -->
        <div class="media-list">
          <div v-for="item in items" :key="item.item_id" class="media-item">
            <img :src="item.poster_url" :alt="item.name" class="media-poster" loading="lazy" />
            <div class="media-info">
              <div class="media-name">{{ item.name }}</div>
              <div class="media-meta">
                <span class="badge" :class="'badge-' + item.resolution.toLowerCase()">{{ item.resolution }}</span>
                <span class="badge" :class="'badge-vr-' + item.video_range.toLowerCase()">{{ item.video_range }}</span>
                <span class="media-type">{{ item.item_type === 'Movie' ? '电影' : '剧集' }}</span>
              </div>
              <div class="media-path" :title="item.path">{{ item.path }}</div>
            </div>
            <button class="ignore-btn" :class="{ ignored: item.is_ignored }" @click="toggleIgnore(item)">
              {{ item.is_ignored ? '↩' : '✕' }}
            </button>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <n-button size="small" :disabled="page <= 1" @click="page--; loadItems()">上一页</n-button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <n-button size="small" :disabled="page >= totalPages" @click="page++; loadItems()">下一页</n-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { NButton, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import { qualityApi } from '@/api/quality'

const message = useMessage()

const overview = ref<any>({ resolution: {}, video_range: {}, total: 0, scan: {} })
const scanStatus = ref<any>({ running: false, total: 0, scanned: 0 })
const scanRunning = computed(() => scanStatus.value.running)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const activeFilter = ref('all')
const pageSize = 25
const totalPages = computed(() => Math.ceil(total.value / pageSize))
let pollTimer: ReturnType<typeof setInterval> | null = null

const filterOptions = computed(() => {
  const r = overview.value.resolution || {}
  return [
    { label: '全部', value: 'all', count: overview.value.total },
    { label: '4K', value: '4K', count: r['4K'] || 0 },
    { label: '1080P', value: '1080P', count: r['1080P'] || 0 },
    { label: '720P', value: '720P', count: r['720P'] || 0 },
    { label: '标清', value: 'SD', count: r['SD'] || 0 },
    { label: '已忽略', value: 'ignored', count: null },
  ]
})

const lastScanTime = computed(() => {
  const t = overview.value.scan?.finished_at
  if (!t) return ''
  return new Date(t).toLocaleString()
})

function barWidth(count: number) {
  const total = overview.value.total || 1
  return Math.max(5, (count / total) * 100)
}

async function loadOverview() {
  try {
    const { data } = await qualityApi.overview()
    overview.value = data.data ?? data
  } catch {}
}

async function loadItems() {
  try {
    const params: any = { page: page.value, size: pageSize }
    if (activeFilter.value === 'ignored') params.is_ignored = true
    else if (activeFilter.value !== 'all') params.resolution = activeFilter.value
    const { data } = await qualityApi.items(params)
    const result = data.data ?? data
    items.value = result.items ?? []
    total.value = result.total ?? 0
  } catch {}
}

async function pollScanStatus() {
  try {
    const { data } = await qualityApi.scanStatus()
    scanStatus.value = data.data ?? data
    if (!scanStatus.value.running) {
      await loadOverview()
      await loadItems()
    }
  } catch {}
}

async function startScan() {
  try {
    await qualityApi.startScan()
    message.success('扫描已启动')
    startPolling()
  } catch {
    message.error('启动扫描失败')
  }
}

async function toggleIgnore(item: any) {
  try {
    if (item.is_ignored) {
      await qualityApi.unignore(item.item_id)
      message.success('已取消忽略')
    } else {
      await qualityApi.ignore(item.item_id)
      message.success('已忽略')
    }
    item.is_ignored = !item.is_ignored
  } catch {
    message.error('操作失败')
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(pollScanStatus, 3000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onMounted(async () => {
  await loadOverview()
  await loadItems()
  if (overview.value.scan?.running) startPolling()
})
onUnmounted(stopPolling)
</script>

<style scoped>
.page { padding-bottom: calc(var(--tab-height) + 16px); }
.body { padding: 16px; }

/* 空状态 */
.empty-state { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.empty-desc { color: var(--text-muted); margin-bottom: 24px; }

/* 统计 */
.stats-grid { margin-bottom: 20px; }
.stat-card { background: var(--surface-grouped); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; }
.stat-label { font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-bars { display: flex; flex-direction: column; gap: 10px; }
.stat-bar { display: flex; align-items: center; gap: 8px; }
.bar-label { font-size: 13px; font-weight: 600; width: 48px; text-align: right; flex-shrink: 0; }
.bar-track { flex: 1; height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; min-width: 4px; }
.bar-4k { background: linear-gradient(90deg, #6366f1, #818cf8); }
.bar-1080p { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.bar-720p { background: linear-gradient(90deg, #10b981, #34d399); }
.bar-sd { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }
.bar-vr-dv { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bar-vr-hdr10 { background: linear-gradient(90deg, #ef4444, #f87171); }
.bar-vr-sdr { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }
.bar-value { font-size: 13px; font-weight: 600; width: 40px; text-align: right; flex-shrink: 0; }
.stat-total { text-align: center; font-size: 13px; color: var(--text-muted); margin-top: 4px; }

/* 筛选 */
.filter-tabs { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 12px; -webkit-overflow-scrolling: touch; }
.filter-tab { flex-shrink: 0; display: flex; align-items: center; gap: 4px; padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-grouped); color: var(--text); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.filter-tab.active { background: var(--brand); color: #fff; border-color: var(--brand); }
.filter-count { font-size: 11px; opacity: 0.7; }
.filter-tab.active .filter-count { opacity: 1; }

/* 媒体列表 */
.media-list { display: flex; flex-direction: column; gap: 1px; }
.media-item { display: flex; gap: 12px; padding: 12px; background: var(--surface-grouped); border-radius: var(--radius); align-items: center; }
.media-item + .media-item { margin-top: 8px; }
.media-poster { width: 48px; height: 68px; border-radius: 6px; object-fit: cover; background: var(--bg-secondary); flex-shrink: 0; }
.media-info { flex: 1; min-width: 0; }
.media-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.media-meta { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 4px; }
.media-type { font-size: 11px; color: var(--text-muted); }
.media-path { font-size: 11px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* 徽章 */
.badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.badge-4k { background: #eef2ff; color: #4f46e5; }
.badge-1080p { background: #eff6ff; color: #2563eb; }
.badge-720p { background: #ecfdf5; color: #059669; }
.badge-sd { background: #f1f5f9; color: #64748b; }
.badge-vr-dv { background: #fffbeb; color: #d97706; }
.badge-vr-hdr10 { background: #fef2f2; color: #dc2626; }
.badge-vr-sdr { background: #f1f5f9; color: #64748b; }

/* 忽略按钮 */
.ignore-btn { width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--border); background: var(--surface-grouped); color: var(--text-muted); font-size: 14px; cursor: pointer; flex-shrink: 0; transition: all 0.2s; }
.ignore-btn:hover { border-color: var(--danger); color: var(--danger); }
.ignore-btn.ignored { border-color: var(--brand); color: var(--brand); }

/* 分页 */
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 16px 0; }
.page-info { font-size: 13px; color: var(--text-muted); }

/* 桌面端 */
@media (min-width: 769px) {
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-total { grid-column: 1 / -1; }
  .media-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 8px; }
  .media-item + .media-item { margin-top: 0; }
}
</style>
