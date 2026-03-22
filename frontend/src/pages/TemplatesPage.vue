<template>
  <div>
    <PageHeader title="权限模板" desc="管理用户权限预设模板">
      <template #actions>
        <n-button type="primary" size="small" @click="showCreate = true">+ 新建模板</n-button>
      </template>
    </PageHeader>

    <LoadingState v-if="loading" />
    <n-empty v-else-if="templates.length === 0" description="创建模板后可在邀请用户时快速套用权限配置" />
    <div v-else class="template-grid">
      <n-card v-for="tpl in templates" :key="tpl.id" size="small">
        <template #header>
          <div style="display:flex;align-items:center;gap:6px">
            {{ tpl.name }}
            <n-tag v-if="tpl.is_default" type="info" size="tiny">默认</n-tag>
          </div>
        </template>
        <div v-if="tpl.description" style="font-size:13px;color:var(--text-muted);margin-bottom:8px">{{ tpl.description }}</div>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">
          {{ tpl.library_access?.length || 0 }} 个库 · {{ new Date(tpl.created_at).toLocaleDateString('zh-CN') }}
        </div>
        <n-button text size="tiny" type="error" @click="deleteTemplate(tpl.id)">删除</n-button>
      </n-card>
    </div>

    <n-modal v-model:show="showCreate" preset="card" title="新建权限模板" style="width: 400px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="模板名称">
          <n-input v-model:value="newTpl.name" placeholder="如：普通用户、VIP用户" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newTpl.description" placeholder="可选" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space justify="end">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :disabled="!newTpl.name" @click="handleCreate">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { NCard, NTag, NButton, NSpace, NModal, NForm, NFormItem, NInput, NEmpty, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { templatesApi, type PermissionTemplate } from '@/api/templates'

const msg = useMessage()
const templates = ref<PermissionTemplate[]>([])
const loading = ref(false)
const showCreate = ref(false)
const newTpl = reactive({ name: '', description: '' })

async function load() { loading.value = true; try { const res = await templatesApi.list(); templates.value = res.data?.items ?? [] } finally { loading.value = false } }
async function handleCreate() { await templatesApi.create({ name: newTpl.name, description: newTpl.description || null }); showCreate.value = false; newTpl.name = ''; newTpl.description = ''; msg.success('已创建'); await load() }
async function deleteTemplate(id: number) { await templatesApi.remove(id); msg.success('已删除'); await load() }

onMounted(load)
</script>

<style scoped>
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
</style>
