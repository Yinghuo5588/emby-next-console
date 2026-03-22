<template>
  <div>
    <n-space size="small" style="margin-bottom:12px">
      <n-button type="primary" size="small" @click="showCreate = true">+ 新建模板</n-button>
      <n-select v-model:value="filterType" :options="typeOptions" clearable placeholder="全部类型" size="small" style="width:140px;margin-left:auto" />
    </n-space>

    <LoadingState v-if="loading" compact />
    <n-empty v-else-if="templates.length === 0" description="暂无模板" />
    <n-card v-for="t in templates" :key="t.id" size="small" style="margin-bottom:8px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-weight:600">{{ t.name }}</span>
        <n-tag size="tiny">{{ t.template_type }}</n-tag>
        <n-tag v-if="t.is_default" type="success" size="tiny">默认</n-tag>
        <n-space size="small" style="margin-left:auto">
          <n-button text size="tiny" @click="editTpl(t)">编辑</n-button>
          <n-button text size="tiny" type="error" @click="removeTpl(t.id)">删除</n-button>
        </n-space>
      </div>
      <div style="font-size:12px">
        <div style="font-weight:500">{{ t.title_template }}</div>
        <div style="color:var(--text-muted);margin-top:4px;white-space:pre-wrap">{{ t.body_template }}</div>
        <n-space v-if="t.variables?.length" size="small" style="margin-top:6px">
          <n-tag v-for="v in t.variables" :key="v" size="tiny" round>{{ '{{' + v + '}}' }}</n-tag>
        </n-space>
      </div>
    </n-card>

    <n-modal v-model:show="showEdit" preset="card" :title="editing ? '编辑模板' : '新建模板'" style="max-width:550px">
      <n-form label-placement="top" size="small">
        <n-form-item label="模板名称"><n-input v-model="form.name" placeholder="如：新剧集入库通知" /></n-form-item>
        <n-form-item label="类型"><n-select v-model="form.template_type" :options="typeOptions" /></n-form-item>
        <n-form-item label="标题模板"><n-input v-model="form.title_template" /></n-form-item>
        <n-form-item label="正文模板"><n-input v-model="form.body_template" type="textarea" :rows="4" /></n-form-item>
        <n-form-item label="变量（逗号分隔）"><n-input v-model="form.variablesStr" placeholder="如：username, series_name" /></n-form-item>
        <n-form-item label="设为默认"><n-switch v-model="form.is_default" /></n-form-item>
      </n-form>
      <template #action><n-button type="primary" block @click="saveTemplate">{{ editing ? '保存' : '创建' }}</n-button></template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { NCard, NTag, NButton, NSpace, NSelect, NModal, NForm, NFormItem, NInput, NSwitch, NEmpty, useMessage, useDialog } from 'naive-ui'
import LoadingState from '@/components/common/LoadingState.vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationTemplate } from '@/api/notifications-ext'

const msg = useMessage()
const dialog = useDialog()
const templates = ref<NotificationTemplate[]>([])
const loading = ref(true)
const filterType = ref<string | null>(null)
const showEdit = ref(false)
const editing = ref<NotificationTemplate | null>(null)
const form = reactive({ name: '', template_type: 'new_content', title_template: '', body_template: '', variablesStr: '', is_default: false })

const typeOptions = [
  { label: '风控告警', value: 'risk_alert' },
  { label: '新入库', value: 'new_content' },
  { label: '系统通知', value: 'system' },
  { label: '欢迎', value: 'welcome' },
]

function editTpl(t: NotificationTemplate) { editing.value = t; Object.assign(form, { name: t.name, template_type: t.template_type, title_template: t.title_template, body_template: t.body_template, variablesStr: t.variables?.join(', ') || '', is_default: t.is_default }); showEdit.value = true }
async function saveTemplate() { const data = { ...form, variables: form.variablesStr.split(',').map(s => s.trim()).filter(Boolean) }; if (editing.value) await notificationsExtApi.updateTemplate(editing.value.id, data); else await notificationsExtApi.createTemplate(data); showEdit.value = false; msg.success('已保存'); await loadTemplates() }
async function removeTpl(id: number) { dialog.warning({ title: '确认', content: '确定删除此模板？', positiveText: '删除', onPositiveClick: async () => { await notificationsExtApi.deleteTemplate(id); msg.success('已删除'); await loadTemplates() } }) }
async function loadTemplates() { loading.value = true; try { templates.value = (await notificationsExtApi.listTemplates(filterType.value || undefined)).data ?? [] } finally { loading.value = false } }

watch(filterType, loadTemplates)
onMounted(loadTemplates)
</script>
