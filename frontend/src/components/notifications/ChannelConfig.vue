<template>
  <div>
    <div class="card" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
      <button class="btn btn-primary" @click="showCreate = true">+ 新建通道</button>
    </div>

    <div v-if="loading" class="muted" style="text-align: center; padding: 24px;">加载中...</div>
    <div v-else-if="channels.length === 0" class="muted" style="text-align: center; padding: 24px;">暂无通知通道</div>
    <div v-else class="ch-list">
      <div v-for="ch in channels" :key="ch.id" class="card ch-card">
        <div class="ch-head">
          <div>
            <span class="ch-type tag" :class="`tag-${ch.channel_type}`">{{ ch.channel_type }}</span>
            <span class="ch-name">{{ ch.name }}</span>
            <span v-if="!ch.is_active" class="tag tag-gray">已禁用</span>
          </div>
          <div class="ch-actions">
            <button class="btn btn-ghost btn-sm" @click="testChannel(ch)">测试</button>
            <button class="btn btn-ghost btn-sm" @click="editChannel(ch)">编辑</button>
            <button class="btn btn-ghost btn-sm" style="color: var(--danger);" @click="removeChannel(ch.id)">删除</button>
          </div>
        </div>
        <div v-if="ch.config" class="ch-config muted">
          <span v-if="ch.config.url">{{ ch.config.url }}</span>
          <span v-if="ch.config.token"> • token: ***</span>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div v-if="showCreate || editing" class="modal-overlay" @click.self="closeModal">
      <div class="modal card" style="max-width: 450px;">
        <div class="modal-head">
          <h3>{{ editing ? '编辑通道' : '新建通道' }}</h3>
          <button class="btn btn-ghost" @click="closeModal">✕</button>
        </div>
        <div class="form">
          <label>名称<input v-model="form.name" placeholder="如：企业微信告警" /></label>
          <label>类型
            <select v-model="form.channel_type">
              <option value="webhook">Webhook</option>
              <option value="email">Email</option>
              <option value="bark">Bark</option>
              <option value="dingtalk">钉钉</option>
              <option value="telegram">Telegram</option>
            </select>
          </label>
          <label>URL / Key<input v-model="form.configUrl" placeholder="Webhook URL 或 Bark key" /></label>
          <label class="check-label"><input type="checkbox" v-model="form.is_active" /> 启用</label>
          <button class="btn btn-primary" style="margin-top: 8px;" @click="saveChannel">
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
import type { NotificationChannel } from '@/api/notifications-ext'

const channels = ref<NotificationChannel[]>([])
const loading = ref(true)
const showCreate = ref(false)
const editing = ref<NotificationChannel | null>(null)
const form = ref({ name: '', channel_type: 'webhook', configUrl: '', is_active: true })

function closeModal() { showCreate.value = false; editing.value = null }

function editChannel(ch: NotificationChannel) {
  editing.value = ch
  form.value = { name: ch.name, channel_type: ch.channel_type, configUrl: ch.config?.url || '', is_active: ch.is_active }
}

async function saveChannel() {
  const data: any = { name: form.value.name, channel_type: form.value.channel_type, is_active: form.value.is_active, config: { url: form.value.configUrl } }
  if (editing.value) {
    await notificationsExtApi.updateChannel(editing.value.id, data)
  } else {
    await notificationsExtApi.createChannel(data)
  }
  closeModal()
  await loadChannels()
}

async function testChannel(ch: NotificationChannel) {
  const res = await notificationsExtApi.testChannel(ch.id)
  alert(res.data?.success ? '测试成功 ✅' : `测试失败: ${res.data?.error || res.data?.message || '未知错误'}`)
}

async function removeChannel(id: number) {
  if (!confirm('确定删除此通道？')) return
  await notificationsExtApi.deleteChannel(id)
  await loadChannels()
}

async function loadChannels() {
  loading.value = true
  try {
    const res = await notificationsExtApi.listChannels()
    channels.value = res.data ?? []
  } finally { loading.value = false }
}

onMounted(loadChannels)
</script>

<style scoped>
.ch-list { display: flex; flex-direction: column; gap: 8px; }
.ch-card { padding: 12px; }
.ch-head { display: flex; justify-content: space-between; align-items: center; }
.ch-name { font-weight: 600; margin-left: 8px; }
.ch-type { font-size: 11px; }
.ch-actions { display: flex; gap: 4px; }
.ch-config { font-size: 12px; margin-top: 6px; }
.tag-webhook { background: #dbeafe; color: #2563eb; }
.tag-email { background: #fef3c7; color: #d97706; }
.tag-bark { background: #ede9fe; color: #7c3aed; }
.tag-dingtalk { background: #d1fae5; color: #059669; }
.tag-telegram { background: #e0f2fe; color: #0284c7; }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.form input, .form select { padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: var(--bg); color: var(--text); }
.check-label { flex-direction: row !important; align-items: center; gap: 8px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.btn-sm { padding: 4px 8px; font-size: 12px; }
</style>