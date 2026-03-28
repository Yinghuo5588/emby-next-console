<template>
  <div class="api-page">
    <PageHeader title="API" desc="开放接口文档与密钥管理" />

    <!-- API Key 管理 -->
    <div class="section-card">
      <div class="section-head">
        <span class="section-title"><IosIcon name="link" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" /><span>API 密钥</span></span>
      </div>
      <div v-for="k in apiKeys" :key="k.id" class="key-item">
        <div class="key-info">
          <div class="key-name">{{ k.name }}</div>
          <div class="key-meta">
            <code class="key-prefix">{{ k.key_prefix }}•••</code>
            <span class="key-scope">{{ k.scopes }}</span>
            <span v-if="k.last_used_at" class="key-used">最近使用: {{ fmtTime(k.last_used_at) }}</span>
          </div>
        </div>
        <n-button size="tiny" type="error" quaternary @click="deleteKey(k.id)">删除</n-button>
      </div>
      <div v-if="apiKeys.length === 0" class="key-empty">暂无密钥</div>
      <div class="key-create">
        <n-input v-model:value="newKeyName" placeholder="密钥名称，如：我的项目" size="small" />
        <n-button type="primary" size="small" :disabled="!newKeyName.trim()" @click="createKey">创建密钥</n-button>
      </div>
      <div v-if="newKey" class="key-new">
        <div class="key-new-label">⚠️ 请立即复制，只显示一次</div>
        <code class="key-new-value">{{ newKey }}</code>
        <n-button size="tiny" @click="copyKey">复制</n-button>
      </div>
    </div>

    <!-- API 文档 -->
    <div class="section-card">
      <div class="section-head">
        <span class="section-title"><IosIcon name="tasks" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" /><span>接口文档</span></span>
      </div>
      <div class="api-intro">
        <p>所有接口支持两种鉴权方式（二选一）：</p>
        <div class="code-block"><code>Authorization: Bearer &lt;JWT Token&gt;</code></div>
        <div class="code-block"><code>X-API-Key: &lt;你的 API Key&gt;</code></div>
      </div>

      <div v-for="group in apiDocs" :key="group.title" class="api-group">
        <div class="api-group-title">{{ group.title }}</div>
        <div v-for="ep in group.endpoints" :key="ep.method + ep.path" class="api-endpoint">
          <span class="api-method" :class="'method-' + ep.method.toLowerCase()">{{ ep.method }}</span>
          <code class="api-path">{{ ep.path }}</code>
          <span class="api-desc">{{ ep.desc }}</span>
        </div>
      </div>

      <div class="api-example">
        <div class="api-group-title">调用示例</div>
        <div class="code-block"><code>curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/manage/users</code></div>
        <div class="code-block"><code>curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/risk/summary</code></div>
      </div>
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
const apiKeys = ref<any[]>([])
const newKeyName = ref('')
const newKey = ref('')

async function loadKeys() {
  try { apiKeys.value = (await apiClient.get('/api-keys')).data?.data ?? [] } catch { apiKeys.value = [] }
}
async function createKey() {
  if (!newKeyName.value.trim()) return
  try {
    const res = await apiClient.post('/api-keys', { name: newKeyName.value.trim(), scopes: 'read' })
    newKey.value = res.data?.data?.key ?? ''
    newKeyName.value = ''
    await loadKeys()
    msg.success('密钥已创建')
  } catch { msg.error('创建失败') }
}
async function deleteKey(id: number) {
  try { await apiClient.delete(`/api-keys/${id}`); await loadKeys(); msg.success('已删除') } catch { msg.error('失败') }
}
function copyKey() { navigator.clipboard.writeText(newKey.value).then(() => msg.success('已复制')) }
function fmtTime(iso: string) {
  const d = new Date(iso), diff = Date.now() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const apiDocs = [
  {
    title: '用户管理',
    endpoints: [
      { method: 'GET', path: '/api/v1/manage/users', desc: '获取用户列表' },
      { method: 'POST', path: '/api/v1/manage/users', desc: '创建用户' },
      { method: 'GET', path: '/api/v1/manage/users/{id}', desc: '获取用户详情' },
      { method: 'PUT', path: '/api/v1/manage/users/{id}', desc: '更新用户' },
      { method: 'DELETE', path: '/api/v1/manage/users/{id}', desc: '删除用户' },
      { method: 'POST', path: '/api/v1/manage/users/batch', desc: '批量操作' },
    ],
  },
  {
    title: '风控管控',
    endpoints: [
      { method: 'GET', path: '/api/v1/risk/summary', desc: '风控概览' },
      { method: 'GET', path: '/api/v1/risk/events', desc: '风控事件列表' },
      { method: 'POST', path: '/api/v1/risk/events/{id}/action', desc: '处理事件(解决/忽略)' },
      { method: 'GET', path: '/api/v1/risk/violations', desc: '违规记录' },
      { method: 'POST', path: '/api/v1/risk/ban', desc: '封禁用户' },
      { method: 'POST', path: '/api/v1/risk/unban', desc: '解封用户' },
      { method: 'POST', path: '/api/v1/risk/scan', desc: '手动扫描' },
      { method: 'GET', path: '/api/v1/risk/policy', desc: '获取策略' },
      { method: 'PUT', path: '/api/v1/risk/policy', desc: '更新策略' },
      { method: 'GET', path: '/api/v1/risk/blacklist', desc: '获取黑名单' },
    ],
  },
  {
    title: '统计分析',
    endpoints: [
      { method: 'GET', path: '/api/v1/stats/overview', desc: '总览数据' },
      { method: 'GET', path: '/api/v1/stats/trend', desc: '播放趋势' },
      { method: 'GET', path: '/api/v1/stats/top-content', desc: '热门内容' },
      { method: 'GET', path: '/api/v1/stats/top-users', desc: '活跃用户' },
      { method: 'GET', path: '/api/v1/stats/heatmap', desc: '观影热力图' },
      { method: 'GET', path: '/api/v1/stats/device-dist', desc: '设备分布' },
    ],
  },
  {
    title: '日历',
    endpoints: [
      { method: 'GET', path: '/api/v1/calendar/upcoming', desc: '获取周历' },
      { method: 'POST', path: '/api/v1/calendar/refresh', desc: '刷新日历' },
    ],
  },
  {
    title: '系统',
    endpoints: [
      { method: 'GET', path: '/api/v1/system/health', desc: '健康检查' },
      { method: 'GET', path: '/api/v1/system/settings', desc: '获取配置' },
      { method: 'GET', path: '/api/v1/system/sessions', desc: 'Emby 播放会话' },
    ],
  },
]

onMounted(loadKeys)
</script>

<style scoped>
.api-page { padding: 0.5rem 0 2rem; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.section-title { display: flex; align-items: center; font-size: 0.9rem; font-weight: 700; color: var(--text); }

/* Key items */
.key-item { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-bottom: 0.5px solid var(--border); }
.key-item:last-of-type { border-bottom: none; }
.key-name { font-size: 0.85rem; font-weight: 600; }
.key-meta { display: flex; align-items: center; gap: 8px; margin-top: 2px; flex-wrap: wrap; }
.key-prefix { font-size: 0.72rem; background: var(--bg); padding: 1px 6px; border-radius: 4px; font-family: monospace; }
.key-scope { font-size: 0.65rem; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(0,122,255,0.08); color: var(--brand); }
.key-used { font-size: 0.65rem; color: var(--text-muted); }
.key-empty { text-align: center; padding: 1rem; color: var(--text-muted); font-size: 0.8rem; }
.key-create { display: flex; gap: 8px; margin-top: 8px; }
.key-new { margin-top: 10px; padding: 10px; background: rgba(255,159,10,0.06); border-radius: 8px; border: 1px solid rgba(255,159,10,0.15); }
.key-new-label { font-size: 0.75rem; color: #E08600; font-weight: 600; margin-bottom: 6px; }
.key-new-value { display: block; font-size: 0.72rem; background: var(--bg); padding: 6px 8px; border-radius: 6px; word-break: break-all; font-family: monospace; margin-bottom: 6px; }

/* API docs */
.api-intro { margin-bottom: 1rem; }
.api-intro p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 8px; }
.code-block { background: var(--bg); padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; }
.code-block code { font-size: 0.72rem; font-family: 'SF Mono', Menlo, monospace; word-break: break-all; }
.api-group { margin-bottom: 1rem; }
.api-group-title { font-size: 0.8rem; font-weight: 700; color: var(--text); margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
.api-endpoint { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 0.8rem; flex-wrap: wrap; }
.api-method { font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; font-family: monospace; }
.method-get { background: rgba(52,199,89,0.12); color: #248A3D; }
.method-post { background: rgba(0,122,255,0.1); color: #007AFF; }
.method-put { background: rgba(255,159,10,0.12); color: #E08600; }
.method-delete { background: rgba(255,59,48,0.1); color: #FF3B30; }
.api-path { font-size: 0.75rem; font-family: monospace; }
.api-desc { font-size: 0.75rem; color: var(--text-muted); }
.api-example { margin-top: 1rem; }

@media (max-width: 767px) {
  .key-create { flex-direction: column; }
}
</style>
