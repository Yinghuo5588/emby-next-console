<template>
  <div>
    <div class="card" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
      <button class="btn btn-primary" @click="showCreate = true">+ 新建规则</button>
    </div>

    <div v-if="loading" class="muted" style="text-align: center; padding: 24px;">加载中...</div>
    <div v-else-if="rules.length === 0" class="muted" style="text-align: center; padding: 24px;">暂无规则</div>
    <div v-else class="rm-table">
      <div class="rm-header">
        <div>事件类型</div><div>通道</div><div>模板</div><div>状态</div><div>操作</div>
      </div>
      <div v-for="r in rules" :key="r.id" class="rm-row">
        <div><span class="tag">{{ r.event_type }}</span></div>
        <div>{{ channelName(r.channel_id) }}</div>
        <div>{{ templateName(r.template_id) || '—' }}</div>
        <div><span :class="r.is_active ? 'tag tag-green' : 'tag tag-gray'">{{ r.is_active ? '启用' : '禁用' }}</span></div>
        <div class="rm-actions">
          <button class="btn btn-ghost btn-sm" @click="editRule(r)">编辑</button>
          <button class="btn btn-ghost btn-sm" style="color: var(--danger);" @click="removeRule(r.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showCreate || editing" class="modal-overlay" @click.self="closeModal">
      <div class="modal card" style="max-width: 450px;">
        <div class="modal-head">
          <h3>{{ editing ? '编辑规则' : '新建规则' }}</h3>
          <button class="btn btn-ghost" @click="closeModal">✕</button>
        </div>
        <div class="form">
          <label>事件类型
            <select v-model="form.event_type">
              <option value="risk_high">风控-高危</option>
              <option value="risk_medium">风控-中危</option>
              <option value="new_episode">新剧集</option>
              <option value="new_movie">新电影</option>
              <option value="login_new_ip">登录-新IP</option>
              <option value="server_error">服务器错误</option>
              <option value="daily_report">每日报告</option>
            </select>
          </label>
          <label>通知通道
            <select v-model.number="form.channel_id">
              <option v-for="ch in channels" :key="ch.id" :value="ch.id">{{ ch.name }} ({{ ch.channel_type }})</option>
            </select>
          </label>
          <label>消息模板（可选）
            <select v-model.number="form.template_id">
              <option :value="0">不使用模板</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </label>
          <label class="check-label"><input type="checkbox" v-model="form.is_active" /> 启用</label>
          <button class="btn btn-primary" style="margin-top: 8px;" @click="saveRule">
            {{ editing ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationRule, NotificationChannel, NotificationTemplate } from '@/api/notifications-ext'

const rules = ref<NotificationRule[]>([])
const channels = ref<NotificationChannel[]>([])
const templates = ref<NotificationTemplate[]>([])
const loading = ref(true)
const showCreate = ref(false)
const editing = ref<NotificationRule | null>(null)
const form = ref({ event_type: 'new_episode', channel_id: 0, template_id: 0, is_active: true })

function closeModal() { showCreate.value = false; editing.value = null }

function channelName(id: number) { return channels.value.find(c => c.id === id)?.name || `#${id}` }
function templateName(id: number | null) { return templates.value.find(t => t.id === id)?.name || null }

function editRule(r: NotificationRule) {
  editing.value = r
  form.value = { event_type: r.event_type, channel_id: r.channel_id, template_id: r.template_id || 0, is_active: r.is_active }
}

async function saveRule() {
  const data: any = { event_type: form.value.event_type, channel_id: form.value.channel_id, template_id: form.value.template_id || null, is_active: form.value.is_active }
  if (editing.value) {
    await notificationsExtApi.updateRule(editing.value.id, data)
  } else {
    await notificationsExtApi.createRule(data)
  }
  closeModal()
  await loadRules()
}

async function removeRule(id: number) {
  if (!confirm('确定删除此规则？')) return
  await notificationsExtApi.deleteRule(id)
  await loadRules()
}

async function loadRules() {
  loading.value = true
  try {
    const [rulesRes, chRes, tplRes] = await Promise.all([
      notificationsExtApi.listRules(),
      notificationsExtApi.listChannels(),
      notificationsExtApi.listTemplates(),
    ])
    rules.value = rulesRes.data ?? []
    channels.value = chRes.data ?? []
    templates.value = tplRes.data ?? []
    if (channels.value.length && !form.value.channel_id) form.value.channel_id = channels.value[0].id
  } finally { loading.value = false }
}

onMounted(loadRules)
</script>

<style scoped>
.rm-table { width: 100%; }
.rm-header { display: grid; grid-template-columns: 1fr 1fr 1fr 80px 120px; gap: 8px; padding: 8px 12px; font-size: 12px; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--border); }
.rm-row { display: grid; grid-template-columns: 1fr 1fr 1fr 80px 120px; gap: 8px; padding: 8px 12px; font-size: 13px; border-bottom: 1px solid var(--border); align-items: center; }
.rm-actions { display: flex; gap: 4px; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: var(--bg-secondary); }
.tag-green { background: #d1fae5; color: #059669; }
.tag-gray { background: var(--bg-secondary); color: var(--text-muted); }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.form input, .form select { padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: var(--bg); color: var(--text); }
.check-label { flex-direction: row !important; align-items: center; gap: 8px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.btn-sm { padding: 4px 8px; font-size: 12px; }
@media (max-width: 767px) {
  .rm-header, .rm-row { grid-template-columns: 1fr 1fr; }
  .rm-header > div:nth-child(3), .rm-header > div:nth-child(4), .rm-row > div:nth-child(3), .rm-row > div:nth-child(4) { display: none; }
}
</style>