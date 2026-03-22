<template>
  <div>
    <n-button type="primary" size="small" @click="showCreate = true" style="margin-bottom:12px">+ 新建规则</n-button>

    <LoadingState v-if="loading" compact />
    <n-empty v-else-if="rules.length === 0" description="暂无规则" />
    <n-card v-else size="small">
      <n-data-table :columns="columns" :data="rules" size="small" :bordered="false" />
    </n-card>

    <n-modal v-model:show="showEdit" preset="card" :title="editing ? '编辑规则' : '新建规则'" style="max-width:450px">
      <n-form label-placement="top" size="small">
        <n-form-item label="事件类型">
          <n-select v-model="form.event_type" :options="eventOptions" />
        </n-form-item>
        <n-form-item label="通知通道">
          <n-select v-model.number="form.channel_id" :options="channels.map(c => ({ label: `${c.name} (${c.channel_type})`, value: c.id }))" />
        </n-form-item>
        <n-form-item label="消息模板（可选）">
          <n-select v-model.number="form.template_id" :options="[{ label: '不使用模板', value: 0 }, ...templates.map(t => ({ label: t.name, value: t.id }))]" />
        </n-form-item>
        <n-form-item label="启用"><n-switch v-model="form.is_active" /></n-form-item>
      </n-form>
      <template #action><n-button type="primary" block @click="saveRule">{{ editing ? '保存' : '创建' }}</n-button></template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NCard, NTag, NButton, NModal, NForm, NFormItem, NSelect, NSwitch, NEmpty, NDataTable, useMessage, useDialog } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationRule, NotificationChannel, NotificationTemplate } from '@/api/notifications-ext'

const msg = useMessage()
const dialog = useDialog()
const rules = ref<NotificationRule[]>([])
const channels = ref<NotificationChannel[]>([])
const templates = ref<NotificationTemplate[]>([])
const loading = ref(true)
const showEdit = ref(false)
const editing = ref<NotificationRule | null>(null)
const form = reactive({ event_type: 'new_episode', channel_id: 0, template_id: 0, is_active: true })

const eventOptions = [
  { label: '风控-高危', value: 'risk_high' },
  { label: '风控-中危', value: 'risk_medium' },
  { label: '新剧集', value: 'new_episode' },
  { label: '新电影', value: 'new_movie' },
  { label: '登录-新IP', value: 'login_new_ip' },
  { label: '服务器错误', value: 'server_error' },
  { label: '每日报告', value: 'daily_report' },
]

const columns: DataTableColumns = [
  { title: '事件类型', key: 'event_type', render: (r: any) => h(NTag, { size: 'tiny' }, { default: () => r.event_type }) },
  { title: '通道', key: 'channel_id', render: (r: any) => channels.value.find(c => c.id === r.channel_id)?.name || `#${r.channel_id}` },
  { title: '模板', key: 'template_id', render: (r: any) => r.template_id ? (templates.value.find(t => t.id === r.template_id)?.name || '—') : '—' },
  { title: '状态', key: 'is_active', width: 80, render: (r: any) => h(NTag, { type: r.is_active ? 'success' : 'default', size: 'tiny' }, { default: () => r.is_active ? '启用' : '禁用' }) },
  { title: '', key: 'actions', width: 120, render: (r: any) => h('div', { style: 'display:flex;gap:4px' }, [
    h(NButton, { text: true, size: 'tiny', onClick: () => editRule(r) }, { default: () => '编辑' }),
    h(NButton, { text: true, size: 'tiny', type: 'error', onClick: () => removeRule(r.id) }, { default: () => '删除' }),
  ]) },
]

function editRule(r: NotificationRule) { editing.value = r; Object.assign(form, { event_type: r.event_type, channel_id: r.channel_id, template_id: r.template_id || 0, is_active: r.is_active }); showEdit.value = true }
async function saveRule() { const data = { ...form, template_id: form.template_id || null }; if (editing.value) await notificationsExtApi.updateRule(editing.value.id, data); else await notificationsExtApi.createRule(data); showEdit.value = false; msg.success('已保存'); await loadRules() }
async function removeRule(id: number) { dialog.warning({ title: '确认', content: '确定删除此规则？', positiveText: '删除', onPositiveClick: async () => { await notificationsExtApi.deleteRule(id); msg.success('已删除'); await loadRules() } }) }

async function loadRules() {
  loading.value = true
  try {
    const [r, c, t] = await Promise.all([notificationsExtApi.listRules(), notificationsExtApi.listChannels(), notificationsExtApi.listTemplates()])
    rules.value = r.data ?? []; channels.value = c.data ?? []; templates.value = t.data ?? []
    if (channels.value.length && !form.channel_id) form.channel_id = channels.value[0].id
  } finally { loading.value = false }
}

onMounted(loadRules)
</script>
