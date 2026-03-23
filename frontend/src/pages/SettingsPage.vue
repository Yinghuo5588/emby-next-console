<template>
  <div>
    <PageHeader title="系统设置" desc="健康状态与配置管理" />

    <section style="margin-bottom: 24px;">
      <div class="section-label">系统健康</div>
      <LoadingState v-if="healthLoading && !health" compact />
      <div v-else-if="health" class="health-grid">
        <n-card v-for="item in healthItems" :key="item.key" size="small" :bordered="true" class="health-card">
          <div class="health-inner">
            <span class="health-icon">{{ item.ok ? '✓' : '✗' }}</span>
            <div>
              <div style="font-size:12px;color:var(--text-muted)">{{ item.label }}</div>
              <n-tag :type="item.ok ? 'success' : 'error'" size="small">{{ item.ok ? '正常' : '异常' }}</n-tag>
            </div>
          </div>
        </n-card>
        <n-card v-if="health.version" size="small" class="health-card">
          <div class="health-inner">
            <span class="health-icon">◈</span>
            <div>
              <div style="font-size:12px;color:var(--text-muted)">版本</div>
              <div style="font-size:14px;font-weight:600">{{ health.version }}</div>
            </div>
          </div>
        </n-card>
      </div>
    </section>

    <section style="margin-bottom: 24px;">
      <div class="section-header">
        <div class="section-label">配置项</div>
        <n-button quaternary size="small" :loading="settingsLoading" @click="loadSettings">刷新</n-button>
      </div>
      <LoadingState v-if="settingsLoading && settings.length === 0" />
      <template v-else>
        <n-card v-for="group in settingGroups" :key="group.name" size="small" style="margin-bottom: 12px;">
          <template #header><span style="font-size:13px">{{ group.name }}</span></template>
          <div v-for="item in group.items" :key="item.setting_key" class="setting-row">
            <div class="setting-meta">
              <div class="setting-key">{{ item.setting_key }}</div>
              <div v-if="item.description" class="setting-desc">{{ item.description }}</div>
            </div>
            <div class="setting-val">
              <template v-if="editingKey === item.setting_key">
                <n-input v-model:value="editingValue" size="small" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" @keyup.ctrl.enter="saveSetting(item.setting_key)" @keyup.escape="cancelEdit" />
              </template>
              <span v-else class="setting-value-text">{{ displayValue(item.value) }}</span>
            </div>
            <div class="setting-actions">
              <template v-if="editingKey === item.setting_key">
                <n-button size="tiny" type="primary" :loading="savingKey === item.setting_key" @click="saveSetting(item.setting_key)">保存</n-button>
                <n-button size="tiny" quaternary @click="cancelEdit">取消</n-button>
              </template>
              <n-button v-else size="tiny" quaternary @click="startEdit(item)">编辑</n-button>
            </div>
          </div>
        </n-card>
      </template>
    </section>

    <section>
      <div class="section-header">
        <div class="section-label">后台任务</div>
        <n-button quaternary size="small" :loading="jobsLoading" @click="loadJobs">刷新</n-button>
      </div>
      <n-card size="small">
        <LoadingState v-if="jobsLoading && jobs.length === 0" />
        <n-empty v-else-if="jobs.length === 0" description="暂无任务记录" />
        <n-data-table v-else :columns="jobColumns" :data="jobs" size="small" :bordered="false" />
      </n-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NCard, NButton, NTag, NInput, NEmpty, NDataTable, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { systemApi } from '@/api/system'

const msg = useMessage()

const health = ref<any>(null)
const healthLoading = ref(false)
const settings = ref<any[]>([])
const settingsLoading = ref(false)
const jobs = ref<any[]>([])
const jobsLoading = ref(false)
const editingKey = ref<string | null>(null)
const editingValue = ref('')
const savingKey = ref<string | null>(null)

const healthItems = computed(() => {
  if (!health.value) return []
  return [
    { key: 'overall', label: '整体', ok: health.value.status === 'ok' },
    { key: 'db', label: '数据库', ok: health.value.db === 'ok' },
    { key: 'redis', label: 'Redis', ok: health.value.redis === 'ok' },
  ]
})

const settingGroups = computed(() => {
  const map = new Map<string, any[]>()
  for (const item of settings.value) {
    const g = item.setting_group ?? 'general'
    if (!map.has(g)) map.set(g, [])
    map.get(g)!.push(item)
  }
  return Array.from(map.entries()).map(([name, items]) => ({ name, items }))
})

const jobColumns: DataTableColumns = [
  { title: '任务', key: 'job_type', ellipsis: true },
  { title: '状态', key: 'status', render: (row: any) => {
    const type = row.status === 'success' ? 'success' : row.status === 'failed' ? 'error' : row.status === 'running' ? 'warning' : 'default'
    return h(NTag, { type, size: 'small' }, { default: () => row.status })
  }},
  { title: '开始', key: 'started_at', render: (row: any) => row.started_at ? fmtTime(row.started_at) : '—' },
  { title: '耗时', key: 'duration', render: (row: any) => calcDuration(row.started_at, row.finished_at) },
]

async function loadHealth() { healthLoading.value = true; try { health.value = (await systemApi.health()).data } finally { healthLoading.value = false } }
async function loadSettings() { settingsLoading.value = true; try { settings.value = (await systemApi.settings()).data ?? [] } finally { settingsLoading.value = false } }
async function loadJobs() { jobsLoading.value = true; try { jobs.value = (await systemApi.jobs()).data ?? [] } finally { jobsLoading.value = false } }

function startEdit(item: any) { editingKey.value = item.setting_key; editingValue.value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value) }
function cancelEdit() { editingKey.value = null; editingValue.value = '' }
async function saveSetting(key: string) {
  savingKey.value = key
  try {
    let parsed: any = editingValue.value
    try { parsed = JSON.parse(editingValue.value) } catch {}
    await systemApi.updateSetting(key, parsed)
    const idx = settings.value.findIndex((s: any) => s.setting_key === key)
    if (idx >= 0) settings.value[idx].value = parsed
    cancelEdit(); msg.success('已保存')
  } catch { msg.error('保存失败') }
  finally { savingKey.value = null }
}

function displayValue(v: any) { if (v == null) return '—'; if (typeof v === 'string') return v || '（空）'; return JSON.stringify(v) }
function fmtTime(iso: string) { return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
function calcDuration(s: string | null, e: string | null) { if (!s || !e) return '—'; const ms = new Date(e).getTime() - new Date(s).getTime(); if (ms < 1000) return `${ms}ms`; return `${(ms / 1000).toFixed(1)}s` }

onMounted(() => { loadHealth(); loadSettings(); loadJobs() })
</script>

<style scoped>
.section-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header .section-label { margin-bottom: 0; }
.health-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.health-card { flex: 1; min-width: 140px; }
.health-inner { display: flex; align-items: center; gap: 10px; }
.health-icon { font-size: 16px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 6px; background: var(--bg-secondary); }
.setting-row { display: flex; align-items: flex-start; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.setting-row:last-child { border-bottom: none; }
.setting-meta { width: 140px; flex-shrink: 0; }
.setting-key { font-size: 13px; font-weight: 500; font-family: monospace; }
.setting-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.setting-val { flex: 1; min-width: 0; font-size: 13px; color: var(--text-muted); font-family: monospace; }
.setting-value-text { word-break: break-all; }
.setting-actions { display: flex; gap: 6px; flex-shrink: 0; }

@media (max-width: 640px) {
  .setting-row { flex-wrap: wrap; }
  .setting-meta { width: 100%; }
  .setting-val { width: 100%; }
  .setting-actions { width: 100%; justify-content: flex-end; margin-top: 6px; }
  .health-grid { flex-direction: column; }
}
</style>
