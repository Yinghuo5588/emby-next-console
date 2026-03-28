<template>
  <div class="apikey-page">
    <PageHeader title="API 密钥" desc="管理外部调用密钥" />

    <div class="section-card">
      <div v-for="k in apiKeys" :key="k.id" class="key-item" style="--i:0">
        <div class="key-info">
          <div class="key-name">{{ k.name }}</div>
          <div class="key-meta">
            <code class="key-prefix">{{ k.key_prefix }}•••</code>
            <span class="key-scope">{{ k.scopes }}</span>
            <span v-if="k.last_used_at" class="key-used">最近: {{ fmtTime(k.last_used_at) }}</span>
          </div>
        </div>
        <n-button size="tiny" type="error" quaternary @click="deleteKey(k.id)">删除</n-button>
      </div>
      <div v-if="!loading && apiKeys.length === 0" class="key-empty">
        <IosIcon name="link" :size="28" color="var(--text-muted)" :stroke-width="1.5" />
        <span>暂无密钥</span>
      </div>

      <div class="key-create">
        <n-input v-model:value="newName" placeholder="密钥名称，如：我的项目" size="small" />
        <n-button type="primary" size="small" :disabled="!newName.trim()" @click="createKey">创建</n-button>
      </div>

      <div v-if="newKey" class="key-new">
        <div class="key-new-label">⚠️ 请立即复制，只显示一次</div>
        <code class="key-new-value">{{ newKey }}</code>
        <n-button size="tiny" @click="copy">复制</n-button>
      </div>
    </div>

    <div class="hint">
      调用方式：<code>X-API-Key: enc_xxx</code><br/>
      详细接口文档见项目根目录 <code>API.md</code>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NInput, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import apiClient from '@/api/client'

const msg = useMessage()
const loading = ref(true)
const apiKeys = ref<any[]>([])
const newName = ref('')
const newKey = ref('')

async function load() {
  try { apiKeys.value = (await apiClient.get('/api-keys')).data?.data ?? [] } catch { apiKeys.value = [] }
  loading.value = false
}
async function createKey() {
  if (!newName.value.trim()) return
  try {
    const res = await apiClient.post('/api-keys', { name: newName.value.trim(), scopes: 'read' })
    newKey.value = res.data?.data?.key ?? ''
    newName.value = ''
    await load()
    msg.success('密钥已创建')
  } catch(e: any) { msg.error(e?.response?.data?.detail || '创建失败') }
}
async function deleteKey(id: number) {
  try { await apiClient.delete(`/api-keys/${id}`); await load(); msg.success('已删除') } catch { msg.error('失败') }
}
function copy() { navigator.clipboard.writeText(newKey.value).then(() => msg.success('已复制')) }
function fmtTime(iso: string) {
  const d = new Date(iso), diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.apikey-page { padding: 0.5rem 0 2rem; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; }
.key-item { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-bottom: 0.5px solid var(--border); }
.key-item:last-of-type { border-bottom: none; }
.key-name { font-size: 0.85rem; font-weight: 600; }
.key-meta { display: flex; align-items: center; gap: 8px; margin-top: 2px; flex-wrap: wrap; }
.key-prefix { font-size: 0.72rem; background: var(--bg); padding: 1px 6px; border-radius: 4px; font-family: monospace; }
.key-scope { font-size: 0.65rem; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(0,122,255,0.08); color: var(--brand); }
.key-used { font-size: 0.65rem; color: var(--text-muted); }
.key-empty { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; padding: 1.5rem; color: var(--text-muted); font-size: 0.8rem; }
.key-create { display: flex; gap: 8px; margin-top: 10px; }
.key-new { margin-top: 10px; padding: 10px; background: rgba(255,159,10,0.06); border-radius: 8px; border: 1px solid rgba(255,159,10,0.15); }
.key-new-label { font-size: 0.75rem; color: #E08600; font-weight: 600; margin-bottom: 6px; }
.key-new-value { display: block; font-size: 0.72rem; background: var(--bg); padding: 6px 8px; border-radius: 6px; word-break: break-all; font-family: monospace; margin-bottom: 6px; }
.hint { margin-top: 1rem; font-size: 0.78rem; color: var(--text-muted); padding: 0 0.25rem; line-height: 1.6; }
.hint code { background: var(--bg); padding: 1px 5px; border-radius: 4px; font-size: 0.72rem; }
@media (max-width: 767px) { .key-create { flex-direction: column; } }
</style>
