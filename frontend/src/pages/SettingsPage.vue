<template>
  <div>
    <PageHeader title="系统设置" desc="健康状态与配置管理" />

    <section style="margin-bottom: 24px;">
      <div class="section-label">系统健康</div>
      <LoadingState v-if="healthLoading && !health" height="80px" />
      <div v-else-if="health" class="health-grid">
        <div class="card health-card" :class="`h-${health.status}`">
          <div class="h-icon">{{ health.status === 'ok' ? '✓' : '⚠' }}</div>
          <div><div class="h-name">整体</div><div class="h-val">{{ health.status === 'ok' ? '正常' : '异常' }}</div></div>
        </div>
        <div class="card health-card" :class="`h-${health.db}`">
          <div class="h-icon">{{ health.db === 'ok' ? '✓' : '✗' }}</div>
          <div><div class="h-name">数据库</div><div class="h-val">{{ health.db === 'ok' ? '正常' : '异常' }}</div></div>
        </div>
        <div class="card health-card" :class="`h-${health.redis}`">
          <div class="h-icon">{{ health.redis === 'ok' ? '✓' : '✗' }}</div>
          <div><div class="h-name">Redis</div><div class="h-val">{{ health.redis === 'ok' ? '正常' : '异常' }}</div></div>
        </div>
        <div v-if="health.version" class="card health-card h-neutral">
          <div class="h-icon">◈</div>
          <div><div class="h-name">版本</div><div class="h-val">{{ health.version }}</div></div>
        </div>
      </div>
    </section>

    <section style="margin-bottom: 24px;">
      <div class="section-header">
        <div class="section-label">配置项</div>
        <button class="btn btn-ghost btn-sm" :disabled="settingsLoading" @click="loadSettings">刷新</button>
      </div>
      <LoadingState v-if="settingsLoading && settings.length === 0" height="120px" />
      <template v-else>
        <div v-for="group in settingGroups" :key="group.name" class="settings-group">
          <div class="group-name">{{ group.name }}</div>
          <div class="card" style="padding: 0;">
            <div v-for="item in group.items" :key="item.setting_key" class="setting-row">
              <div class="setting-meta">
                <div class="setting-key">{{ item.setting_key }}</div>
                <div v-if="item.description" class="setting-desc">{{ item.description }}</div>
              </div>
              <div class="setting-val">
                <template v-if="editingKey === item.setting_key">
                  <input v-model="editingValue" class="edit-input" @keyup.enter="saveSetting(item.setting_key)" @keyup.escape="cancelEdit" />
                </template>
                <span v-else>{{ displayValue(item.value) }}</span>
              </div>
              <div class="setting-actions">
                <template v-if="editingKey === item.setting_key">
                  <button class="btn btn-primary btn-sm" :disabled="savingKey === item.setting_key" @click="saveSetting(item.setting_key)">保存</button>
                  <button class="btn btn-ghost btn-sm" @click="cancelEdit">取消</button>
                </template>
                <button v-else class="btn btn-ghost btn-sm" @click="startEdit(item)">编辑</button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </section>

    <section>
      <div class="section-header">
        <div class="section-label">后台任务</div>
        <button class="btn btn-ghost btn-sm" :disabled="jobsLoading" @click="loadJobs">刷新</button>
      </div>
      <div class="card" style="padding: 0;">
        <LoadingState v-if="jobsLoading && jobs.length === 0" height="120px" />
        <table v-else>
          <thead><tr><th>任务</th><th>状态</th><th>开始</th><th>耗时</th></tr></thead>
          <tbody>
            <tr v-if="jobs.length === 0"><td colspan="4" class="empty">暂无任务记录</td></tr>
            <tr v-for="job in jobs" :key="(job as any).job_id">
              <td>{{ (job as any).job_type ?? '—' }}</td>
              <td><span class="tag" :class="jobStatusClass((job as any).status)">{{ (job as any).status }}</span></td>
              <td class="muted">{{ (job as any).started_at ? fmtTime((job as any).started_at) : '—' }}</td>
              <td class="muted">{{ calcDuration((job as any).started_at, (job as any).finished_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <Transition name="toast"><div v-if="toast" class="toast" :class="`toast-${toast.type}`">{{ toast.message }}</div></Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { systemApi } from '@/api/system'

const health = ref<any>(null)
const healthLoading = ref(false)
const settings = ref<any[]>([])
const settingsLoading = ref(false)
const jobs = ref<any[]>([])
const jobsLoading = ref(false)
const editingKey = ref<string | null>(null)
const editingValue = ref('')
const savingKey = ref<string | null>(null)
const toast = ref<{ message: string; type: string } | null>(null)

const settingGroups = computed(() => {
  const map = new Map<string, any[]>()
  for (const item of settings.value) {
    const g = item.setting_group ?? 'general'
    if (!map.has(g)) map.set(g, [])
    map.get(g)!.push(item)
  }
  return Array.from(map.entries()).map(([name, items]) => ({ name, items }))
})

async function loadHealth() { healthLoading.value = true; try { health.value = (await systemApi.health()).data } finally { healthLoading.value = false } }
async function loadSettings() { settingsLoading.value = true; try { settings.value = (await systemApi.settings()).data ?? [] } finally { settingsLoading.value = false } }
async function loadJobs() { jobsLoading.value = true; try { jobs.value = (await systemApi.jobs()).data ?? [] } finally { jobsLoading.value = false } }

function startEdit(item: any) { editingKey.value = item.setting_key; editingValue.value = typeof item.value === 'string' ? item.value : JSON.stringify(item.value); nextTick(() => { (document.querySelector('.edit-input') as HTMLInputElement)?.focus() }) }
function cancelEdit() { editingKey.value = null; editingValue.value = '' }
async function saveSetting(key: string) {
  savingKey.value = key
  try {
    let parsed: any = editingValue.value
    try { parsed = JSON.parse(editingValue.value) } catch {}
    await systemApi.updateSetting(key, parsed)
    const idx = settings.value.findIndex((s: any) => s.setting_key === key)
    if (idx >= 0) settings.value[idx].value = parsed
    cancelEdit(); showToast('已保存', 'success')
  } catch { showToast('保存失败', 'error') }
  finally { savingKey.value = null }
}

function displayValue(v: any) { if (v == null) return '—'; if (typeof v === 'string') return v || '（空）'; return JSON.stringify(v) }
function jobStatusClass(s: string) { return { success: 'tag-green', failed: 'tag-red', running: 'tag-yellow' }[s] ?? 'tag-gray' }
function fmtTime(iso: string) { return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
function calcDuration(s: string | null, e: string | null) { if (!s || !e) return '—'; const ms = new Date(e).getTime() - new Date(s).getTime(); if (ms < 1000) return `${ms}ms`; return `${(ms / 1000).toFixed(1)}s` }
function showToast(message: string, type: string) { toast.value = { message, type }; setTimeout(() => { toast.value = null }, 2500) }

onMounted(() => { loadHealth(); loadSettings(); loadJobs() })
</script>

<style scoped>
.section-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header .section-label { margin-bottom: 0; }
.health-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.health-card { display: flex; align-items: center; gap: 12px; padding: 14px 18px; min-width: 140px; flex: 1; }
.h-ok { border-color: var(--success); } .h-error { border-color: var(--danger); } .h-degraded { border-color: var(--warning); } .h-neutral {}
.h-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: var(--bg-secondary); font-size: 16px; }
.h-ok .h-icon { color: var(--success); background: var(--success-light); } .h-error .h-icon { color: var(--danger); background: var(--danger-light); }
.h-name { font-size: 12px; color: var(--text-muted); } .h-val { font-size: 14px; font-weight: 600; }
.h-ok .h-val { color: var(--success); } .h-error .h-val { color: var(--danger); }
.settings-group { margin-bottom: 16px; }
.group-name { font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; }
.setting-row { display: flex; align-items: center; gap: 16px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.setting-row:last-child { border-bottom: none; }
.setting-meta { width: 200px; flex-shrink: 0; }
.setting-key { font-size: 13px; font-weight: 500; font-family: monospace; }
.setting-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.setting-val { flex: 1; min-width: 0; font-size: 13px; color: var(--text-muted); font-family: monospace; }
.edit-input { width: 100%; font-family: monospace; }
.setting-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.muted { color: var(--text-muted); font-size: 12px; }
.empty { text-align: center; padding: 40px !important; color: var(--text-muted); }
.toast { position: fixed; bottom: 32px; right: 32px; padding: 10px 18px; border-radius: 8px; font-size: 13px; z-index: 9999; box-shadow: var(--shadow-lg); }
.toast-success { background: var(--success-light); border: 1px solid var(--success); color: var(--success); }
.toast-error { background: var(--danger-light); border: 1px solid var(--danger); color: var(--danger); }
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
