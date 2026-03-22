<template>
  <div>
    <PageHeader title="权限模板" desc="管理用户权限预设模板">
      <template #actions>
        <button class="btn btn-primary" @click="showCreate = true">+ 新建模板</button>
      </template>
    </PageHeader>

    <LoadingState v-if="loading" height="120px" />
    <EmptyState v-else-if="templates.length === 0" title="暂无模板" desc="创建模板后可在邀请用户时快速套用权限配置" />

    <div v-else class="template-grid">
      <div v-for="tpl in templates" :key="tpl.id" class="card template-card">
        <div class="tc-head">
          <div class="tc-name">{{ tpl.name }}</div>
          <span v-if="tpl.is_default" class="tag tag-blue" style="font-size:10px">默认</span>
        </div>
        <div v-if="tpl.description" class="tc-desc">{{ tpl.description }}</div>
        <div class="tc-meta">
          <span>{{ tpl.library_access?.length || 0 }} 个库</span>
          <span>{{ new Date(tpl.created_at).toLocaleDateString('zh-CN') }}</span>
        </div>
        <div class="tc-actions">
          <button class="btn btn-ghost btn-sm" @click="deleteTemplate(tpl.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal card">
        <div class="modal-title">新建权限模板</div>
        <div class="form-group">
          <label>模板名称</label>
          <input v-model="newTpl.name" placeholder="如：普通用户、VIP用户" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="newTpl.description" placeholder="可选" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate" :disabled="!newTpl.name">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { templatesApi, type PermissionTemplate } from '@/api/templates'

const templates = ref<PermissionTemplate[]>([])
const loading = ref(false)
const showCreate = ref(false)
const newTpl = reactive({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    const res = await templatesApi.list()
    templates.value = res.data?.items ?? []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  await templatesApi.create({ name: newTpl.name, description: newTpl.description || null })
  showCreate.value = false
  newTpl.name = ''; newTpl.description = ''
  await load()
}

async function deleteTemplate(id: number) {
  if (!confirm('确定删除此模板？')) return
  await templatesApi.remove(id)
  await load()
}

onMounted(load)
</script>

<style scoped>
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.template-card { padding: 16px; }
.tc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tc-name { font-weight: 600; font-size: 15px; }
.tc-desc { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }
.tc-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.tc-actions { display: flex; gap: 8px; }
.btn-sm { padding: 3px 8px; font-size: 12px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200; display: flex; align-items: center; justify-content: center; }
.modal { width: 400px; max-width: 90vw; padding: 24px; }
.modal-title { font-weight: 600; font-size: 16px; margin-bottom: 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.form-group input { width: 100%; }
</style>