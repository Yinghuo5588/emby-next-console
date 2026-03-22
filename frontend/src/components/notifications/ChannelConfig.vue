<template>
  <div>
    <n-button type="primary" size="small" @click="showCreate = true" style="margin-bottom:12px">+ 新建通道</n-button>

    <LoadingState v-if="loading" compact />
    <n-empty v-else-if="channels.length === 0" description="暂无通知通道" />
    <div v-else class="ch-list">
      <n-card v-for="ch in channels" :key="ch.id" size="small" style="margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;align-items:center;gap:8px">
            <n-tag :type="channelTypeColor(ch.channel_type)" size="tiny">{{ ch.channel_type }}</n-tag>
            <span style="font-weight:600">{{ ch.name }}</span>
            <n-tag v-if="!ch.is_active" size="tiny">已禁用</n-tag>
          </div>
          <n-space size="small">
            <n-button text size="tiny" @click="testChannel(ch)">测试</n-button>
            <n-button text size="tiny" @click="editChannel(ch)">编辑</n-button>
            <n-button text size="tiny" type="error" @click="removeChannel(ch.id)">删除</n-button>
          </n-space>
        </div>
        <div v-if="ch.config" style="font-size:12px;color:var(--text-muted);margin-top:6px">
          <span v-if="ch.config.url">{{ ch.config.url }}</span>
          <span v-if="ch.config.token"> · token: ***</span>
        </div>
      </n-card>
    </div>

    <n-modal v-model:show="showEdit" preset="card" :title="editing ? '编辑通道' : '新建通道'" style="max-width:450px">
      <n-form label-placement="top" size="small">
        <n-form-item label="名称"><n-input v-model="form.name" placeholder="如：企业微信告警" /></n-form-item>
        <n-form-item label="类型">
          <n-select v-model="form.channel_type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="URL / Key"><n-input v-model="form.configUrl" placeholder="Webhook URL 或 Bark key" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model="form.is_active" /></n-form-item>
      </n-form>
      <template #action><n-button type="primary" block @click="saveChannel">{{ editing ? '保存' : '创建' }}</n-button></template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { NCard, NTag, NButton, NSpace, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NEmpty, useMessage, useDialog } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationChannel } from '@/api/notifications-ext'

const msg = useMessage()
const dialog = useDialog()
const channels = ref<NotificationChannel[]>([])
const loading = ref(true)
const showEdit = ref(false)
const editing = ref<NotificationChannel | null>(null)
const form = reactive({ name: '', channel_type: 'webhook', configUrl: '', is_active: true })

const typeOptions = [
  { label: 'Webhook', value: 'webhook' },
  { label: 'Email', value: 'email' },
  { label: 'Bark', value: 'bark' },
  { label: '钉钉', value: 'dingtalk' },
  { label: 'Telegram', value: 'telegram' },
]

function channelTypeColor(t: string) { return { webhook: 'info', email: 'warning', bark: 'default', dingtalk: 'success', telegram: 'info' }[t] as any ?? 'default' }

function editChannel(ch: NotificationChannel) { editing.value = ch; Object.assign(form, { name: ch.name, channel_type: ch.channel_type, configUrl: ch.config?.url || '', is_active: ch.is_active }); showEdit.value = true }
async function saveChannel() { const data = { name: form.name, channel_type: form.channel_type, is_active: form.is_active, config: { url: form.configUrl } }; if (editing.value) await notificationsExtApi.updateChannel(editing.value.id, data); else await notificationsExtApi.createChannel(data); showEdit.value = false; msg.success('已保存'); await loadChannels() }
async function testChannel(ch: NotificationChannel) { const res = await notificationsExtApi.testChannel(ch.id); msg[res.data?.success ? 'success' : 'error'](res.data?.success ? '测试成功 ✅' : `测试失败: ${res.data?.error || '未知错误'}`) }
async function removeChannel(id: number) { dialog.warning({ title: '确认', content: '确定删除此通道？', positiveText: '删除', negativeText: '取消', onPositiveClick: async () => { await notificationsExtApi.deleteChannel(id); msg.success('已删除'); await loadChannels() } }) }
async function loadChannels() { loading.value = true; try { channels.value = (await notificationsExtApi.listChannels()).data ?? [] } finally { loading.value = false } }

onMounted(loadChannels)
</script>

<style scoped>
.ch-list { display: flex; flex-direction: column; gap: 4px; }
</style>
