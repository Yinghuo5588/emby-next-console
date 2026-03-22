<template>
  <div>
    <PageHeader title="海报工坊" desc="自动生成媒体海报">
      <template #actions>
        <n-button type="primary" size="small" @click="showGenerate = true">🖼️ 生成海报</n-button>
      </template>
    </PageHeader>

    <n-tabs v-model:value="tab" type="segment" size="small" style="margin-bottom: 16px;">
      <n-tab-pane name="generated" tab="📸 已生成">
        <LoadingState v-if="posterLoading" compact />
        <n-empty v-else-if="posters.length === 0" description="点击生成按钮创建你的第一张海报" />
        <div v-else class="poster-grid">
          <n-card v-for="p in posters" :key="p.id" size="small" class="poster-card" @click="previewPoster(p.id)">
            <div style="font-weight:600;font-size:15px">{{ p.title }}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">{{ p.item_ids?.length || 0 }} 个媒体 · {{ p.status }}</div>
          </n-card>
        </div>
      </n-tab-pane>

      <n-tab-pane name="templates" tab="🎨 模板">
        <n-button type="primary" size="small" @click="showCreateTemplate = true" style="margin-bottom:12px">+ 新建模板</n-button>
        <n-empty v-if="templates.length === 0" description="暂无模板" />
        <div v-else class="tpl-grid">
          <n-card v-for="t in templates" :key="t.id" size="small" style="padding:0;overflow:hidden">
            <div style="height:6px" :style="{ background: t.accent_color }"></div>
            <div style="padding:12px">
              <div style="font-weight:600">{{ t.name }}</div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:4px">{{ t.description || `${t.layout} · ${t.columns}列` }}</div>
              <div style="display:flex;gap:4px;margin-top:8px">
                <span v-for="c in [t.background_color, t.text_color, t.accent_color]" :key="c" style="width:16px;height:16px;border-radius:50%;border:1px solid var(--border)" :style="{ background: c }"></span>
              </div>
            </div>
          </n-card>
        </div>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="showGenerate" preset="card" title="生成海报" style="max-width:450px">
      <n-form label-placement="top" size="small">
        <n-form-item label="标题"><n-input v-model:value="genForm.title" placeholder="如：本周精选" /></n-form-item>
        <n-form-item label="模板">
          <n-select v-model:value="genForm.template_id" :options="[{ label: '默认样式', value: 0 }, ...templates.map(t => ({ label: t.name, value: t.id }))]" />
        </n-form-item>
        <n-form-item label="Emby Item IDs（逗号分隔，留空自动取最新）"><n-input v-model:value="genForm.itemIdsStr" placeholder="如：abc123, def456" /></n-form-item>
      </n-form>
      <template #action><n-button type="primary" block :loading="generating" @click="doGenerate">生成</n-button></template>
    </n-modal>

    <n-modal v-model:show="showCreateTemplate" preset="card" title="新建模板" style="max-width:450px">
      <n-form label-placement="top" size="small">
        <n-form-item label="名称"><n-input v-model:value="tplForm.name" placeholder="如：深色风格" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="tplForm.description" /></n-form-item>
        <n-form-item label="列数"><n-input-number v-model:value="tplForm.columns" :min="1" :max="8" style="width:100%" /></n-form-item>
        <n-form-item label="布局"><n-select v-model:value="tplForm.layout" :options="[{label:'竖排',value:'vertical'},{label:'横排',value:'horizontal'},{label:'网格',value:'grid'}]" /></n-form-item>
      </n-form>
      <template #action><n-button type="primary" block @click="doCreateTemplate">创建</n-button></template>
    </n-modal>

    <n-modal v-model:show="showPreview" style="width:90vw;max-width:800px;height:80vh;padding:0;overflow:hidden;border-radius:12px">
      <iframe v-if="previewHtml" :srcdoc="previewHtml" style="width:100%;height:100%;border:none"></iframe>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NTabs, NTabPane, NCard, NButton, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NEmpty } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { posterApi } from '@/api/poster'
import type { PosterTemplate, GeneratedPoster } from '@/api/poster'

const tab = ref('generated')
const posters = ref<GeneratedPoster[]>([])
const templates = ref<PosterTemplate[]>([])
const posterLoading = ref(true)
const generating = ref(false)
const showGenerate = ref(false)
const showCreateTemplate = ref(false)
const showPreview = ref(false)
const previewHtml = ref('')
const genForm = ref({ title: 'Emby 合集', template_id: 0, itemIdsStr: '' })
const tplForm = ref({ name: '', description: '', columns: 3, layout: 'vertical', background_color: '#1a1a2e', text_color: '#ffffff', accent_color: '#e94560' })

async function loadPosters() { posterLoading.value = true; try { posters.value = (await posterApi.listGenerated()).data?.items ?? [] } finally { posterLoading.value = false } }
async function loadTemplates() { try { templates.value = (await posterApi.listTemplates()).data ?? [] } catch {} }
async function doGenerate() { generating.value = true; try { const item_ids = genForm.value.itemIdsStr.split(',').map(s => s.trim()).filter(Boolean); await posterApi.generate({ title: genForm.value.title, template_id: genForm.value.template_id || undefined, item_ids: item_ids.length ? item_ids : undefined }); showGenerate.value = false; await loadPosters() } finally { generating.value = false } }
async function previewPoster(id: number) { previewHtml.value = (await posterApi.getHtml(id)).data?.html || ''; showPreview.value = true }
async function doCreateTemplate() { await posterApi.createTemplate(tplForm.value); showCreateTemplate.value = false; await loadTemplates() }

onMounted(() => { loadPosters(); loadTemplates() })
</script>

<style scoped>
.poster-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.poster-card { cursor: pointer; transition: transform 0.15s; }
.poster-card:hover { transform: translateY(-2px); }
.tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
</style>
