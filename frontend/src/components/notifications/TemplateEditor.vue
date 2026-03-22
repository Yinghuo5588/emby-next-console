<template>
  <div>
    <div class="card" style="margin-bottom: 12px; display: flex; gap: 8px; align-items: center;">
      <button class="btn btn-primary" @click="showCreate = true">+ 新建模板</button>
      <select v-model="filterType" style="margin-left: auto; padding: 6px; border-radius: 6px; font-size: 12px; background: var(--bg); border: 1px solid var(--border);">
        <option value="">全部类型</option>
        <option value="risk_alert">风控告警</option>
        <option value="new_content">新入库</option>
        <option value="system">系统通知</option>
        <option value="welcome">欢迎</option>
      </select>
    </div>

    <div v-if="loading" class="muted" style="text-align: center; padding: 24px;">加载中...</div>
    <div v-else-if="templates.length === 0" class="muted" style="text-align: center; padding: 24px;">暂无模板</div>
    <div v-else class="tpl-list">
      <div v-for="t in templates" :key="t.id" class="card tpl-card">
        <div class="tpl-head">
          <span class="tpl-name">{{ t.name }}</span>
          <span class="tag tag-sm">{{ t.template_type }}</span>
          <span v-if="t.is_default" class="tag tag-green">默认</span>
          <div class="tpl-actions">
            <button class="btn btn-ghost btn-sm" @click="editTpl(t)">编辑</button>
            <button class="btn btn-ghost btn-sm" style="color: var(--danger);" @click="removeTpl(t.id)">删除</button>
          </div>
        </div>
        <div class="tpl-body">
          <div class="tpl-title-preview muted">{{ t.title_template }}</div>
          <div class="tpl-body-preview muted">{{ t.body_template }}</div>
          <div v-if="t.variables?.length" class="tpl-vars">
            <span class="tag tag-gray tag-sm" v-for="v in t.variables" :key="v">{{ formatVar(v) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showCreate || editing" class="modal-overlay" @click.self="closeModal">
      <div class="modal card" style="max-width: 550px;">
        <div class="modal-head">
          <h3>{{ editing ? '编辑模板' : '新建模板' }}</h3>
          <button class="btn btn-ghost" @click="closeModal">✕</button>
        </div>
        <div class="form">
          <label>模板名称<input v-model="form.name" placeholder="如：新剧集入库通知" /></label>
          <label>类型
            <select v-model="form.template_type">
              <option value="risk_alert">风控告警</option>
              <option value="new_content">新入库</option>
              <option value="system">系统通知</option>
              <option value="welcome">欢迎</option>
            </select>
          </label>
          <label>标题模板<input v-model="form.title_template" placeholder="如：用变量名如 series_name" /></label>
          <label>正文模板<textarea v-model="form.body_template" rows="4" placeholder="如：username, series_name, episode_number" /></label>
          <label>变量（逗号分隔）<input v-model="form.variablesStr" placeholder="如：username, series_name, episode_number" /></label>
          <label class="check-label"><input type="checkbox" v-model="form.is_default" /> 设为默认模板</label>
          <button class="btn btn-primary" style="margin-top: 8px;" @click="saveTemplate">
            {{ editing ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { notificationsExtApi } from '@/api/notifications-ext'
import type { NotificationTemplate } from '@/api/notifications-ext'

const templates = ref<NotificationTemplate[]>([])
const loading = ref(true)
const filterType = ref('')
const showCreate = ref(false)
const editing = ref<NotificationTemplate | null>(null)
const form = ref({ name: '', template_type: 'new_content', title_template: '', body_template: '', variablesStr: '', is_default: false })

function closeModal() { showCreate.value = false; editing.value = null }

function editTpl(t: NotificationTemplate) {
  editing.value = t
  form.value = { name: t.name, template_type: t.template_type, title_template: t.title_template, body_template: t.body_template, variablesStr: t.variables?.join(', ') || '', is_default: t.is_default }
}

async function saveTemplate() {
  const data: any = {
    name: form.value.name, template_type: form.value.template_type,
    title_template: form.value.title_template, body_template: form.value.body_template,
    variables: form.value.variablesStr.split(',').map(s => s.trim()).filter(Boolean),
    is_default: form.value.is_default,
  }
  if (editing.value) {
    await notificationsExtApi.updateTemplate(editing.value.id, data)
  } else {
    await notificationsExtApi.createTemplate(data)
  }
  closeModal()
  await loadTemplates()
}

async function removeTpl(id: number) {
  if (!confirm('确定删除此模板？')) return
  await notificationsExtApi.deleteTemplate(id)
  await loadTemplates()
}

function formatVar(v: string) { return '{{' + v + '}}' }

async function loadTemplates() {
  loading.value = true
  try {
    const res = await notificationsExtApi.listTemplates(filterType.value || undefined)
    templates.value = res.data ?? []
  } finally { loading.value = false }
}

watch(filterType, loadTemplates)
onMounted(loadTemplates)
</script>

<style scoped>
.tpl-list { display: flex; flex-direction: column; gap: 8px; }
.tpl-card { padding: 12px; }
.tpl-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tpl-name { font-weight: 600; }
.tpl-actions { margin-left: auto; display: flex; gap: 4px; }
.tpl-body { font-size: 12px; }
.tpl-title-preview { font-weight: 500; }
.tpl-body-preview { margin-top: 4px; white-space: pre-wrap; }
.tpl-vars { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.tag-sm { font-size: 10px; padding: 2px 6px; }
.tag-green { background: #d1fae5; color: #059669; }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.form input, .form select, .form textarea { padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: var(--bg); color: var(--text); font-family: inherit; }
.form textarea { resize: vertical; }
.check-label { flex-direction: row !important; align-items: center; gap: 8px; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.btn-sm { padding: 4px 8px; font-size: 12px; }
</style>