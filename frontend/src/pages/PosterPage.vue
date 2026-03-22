<template>
  <div>
    <PageHeader title="海报工坊" desc="自动生成媒体海报">
      <template #actions>
        <button class="btn btn-primary" @click="showGenerate = true">🖼️ 生成海报</button>
      </template>
    </PageHeader>

    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: tab === 'generated' }" @click="tab = 'generated'">📸 已生成</button>
      <button class="tab-btn" :class="{ active: tab === 'templates' }" @click="tab = 'templates'">🎨 模板</button>
    </div>

    <div v-show="tab === 'generated'">
      <LoadingState v-if="posterLoading" height="120px" />
      <EmptyState v-else-if="posters.length === 0" title="暂无海报" desc="点击生成按钮创建你的第一张海报" />
      <div v-else class="poster-grid">
        <div v-for="p in posters" :key="p.id" class="card poster-card" @click="previewPoster(p.id)">
          <div class="poster-title">{{ p.title }}</div>
          <div class="poster-meta muted">{{ p.item_ids?.length || 0 }} 个媒体 · {{ p.status }}</div>
        </div>
      </div>
    </div>

    <div v-show="tab === 'templates'">
      <div class="card" style="margin-bottom: 12px;">
        <button class="btn btn-primary" @click="showCreateTemplate = true">+ 新建模板</button>
      </div>
      <div v-if="templates.length === 0" class="muted" style="text-align: center; padding: 24px;">暂无模板</div>
      <div v-else class="tpl-grid">
        <div v-for="t in templates" :key="t.id" class="card tpl-card">
          <div class="tpl-color-bar" :style="{ background: t.accent_color }"></div>
          <div class="tpl-info">
            <div class="tpl-name">{{ t.name }}</div>
            <div class="tpl-desc muted">{{ t.description || `${t.layout} · ${t.columns}列` }}</div>
            <div class="tpl-colors">
              <span class="color-dot" :style="{ background: t.background_color }"></span>
              <span class="color-dot" :style="{ background: t.text_color }"></span>
              <span class="color-dot" :style="{ background: t.accent_color }"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showGenerate" class="modal-overlay" @click.self="showGenerate = false">
      <div class="modal card" style="max-width: 450px;">
        <div class="modal-head">
          <h3>生成海报</h3>
          <button class="btn btn-ghost" @click="showGenerate = false">✕</button>
        </div>
        <div class="form">
          <label>标题<input v-model="genForm.title" placeholder="如：本周精选" /></label>
          <label>模板
            <select v-model.number="genForm.template_id">
              <option :value="0">默认样式</option>
              <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </label>
          <label>Emby Item IDs（逗号分隔，留空自动取最新）<input v-model="genForm.itemIdsStr" placeholder="如：abc123, def456" /></label>
          <button class="btn btn-primary" style="margin-top: 8px;" @click="doGenerate" :disabled="generating">
            {{ generating ? '生成中...' : '生成' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="previewHtml" class="modal-overlay" @click.self="previewHtml = ''">
      <div class="modal" style="width: 90vw; max-width: 800px; height: 80vh; padding: 0; overflow: hidden; border-radius: 12px;">
        <iframe :srcdoc="previewHtml" style="width:100%; height:100%; border:none;"></iframe>
      </div>
    </div>

    <div v-if="showCreateTemplate" class="modal-overlay" @click.self="showCreateTemplate = false">
      <div class="modal card" style="max-width: 450px;">
        <div class="modal-head">
          <h3>新建模板</h3>
          <button class="btn btn-ghost" @click="showCreateTemplate = false">✕</button>
        </div>
        <div class="form">
          <label>名称<input v-model="tplForm.name" placeholder="如：深色风格" /></label>
          <label>描述<input v-model="tplForm.description" placeholder="模板描述（可选）" /></label>
          <label>列数<input v-model.number="tplForm.columns" type="number" min="1" max="8" /></label>
          <label>布局
            <select v-model="tplForm.layout">
              <option value="vertical">竖排</option>
              <option value="horizontal">横排</option>
              <option value="grid">网格</option>
            </select>
          </label>
          <div class="color-row">
            <label>背景<input v-model="tplForm.background_color" type="color" /></label>
            <label>文字<input v-model="tplForm.text_color" type="color" /></label>
            <label>强调<input v-model="tplForm.accent_color" type="color" /></label>
          </div>
          <button class="btn btn-primary" style="margin-top: 8px;" @click="doCreateTemplate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { posterApi } from '@/api/poster'
import type { PosterTemplate, GeneratedPoster } from '@/api/poster'

const tab = ref('generated')
const posters = ref<GeneratedPoster[]>([])
const templates = ref<PosterTemplate[]>([])
const posterLoading = ref(true)
const generating = ref(false)
const showGenerate = ref(false)
const showCreateTemplate = ref(false)
const previewHtml = ref('')

const genForm = ref({ title: 'Emby 合集', template_id: 0, itemIdsStr: '' })
const tplForm = ref({ name: '', description: '', columns: 3, layout: 'vertical', background_color: '#1a1a2e', text_color: '#ffffff', accent_color: '#e94560' })

async function loadPosters() {
  posterLoading.value = true
  try {
    const res = await posterApi.listGenerated()
    posters.value = res.data?.items ?? []
  } finally { posterLoading.value = false }
}

async function loadTemplates() {
  try {
    const res = await posterApi.listTemplates()
    templates.value = res.data ?? []
  } catch {}
}

async function doGenerate() {
  generating.value = true
  try {
    const item_ids = genForm.value.itemIdsStr.split(',').map(s => s.trim()).filter(Boolean)
    const res = await posterApi.generate({
      title: genForm.value.title,
      template_id: genForm.value.template_id || undefined,
      item_ids: item_ids.length ? item_ids : undefined,
    })
    showGenerate.value = false
    await loadPosters()
    if (res.data?.id) await previewPoster(res.data.id)
  } finally { generating.value = false }
}

async function previewPoster(id: number) {
  const res = await posterApi.getHtml(id)
  previewHtml.value = res.data?.html || ''
}

async function doCreateTemplate() {
  await posterApi.createTemplate(tplForm.value)
  showCreateTemplate.value = false
  await loadTemplates()
}

onMounted(() => { loadPosters(); loadTemplates() })
</script>

<style scoped>
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; }
.tab-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text-muted); cursor: pointer; font-size: 13px; }
.tab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.poster-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.poster-card { padding: 16px; cursor: pointer; transition: transform 0.15s; }
.poster-card:hover { transform: translateY(-2px); }
.poster-title { font-weight: 600; font-size: 15px; }
.poster-meta { font-size: 12px; margin-top: 4px; }
.tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.tpl-card { padding: 0; overflow: hidden; }
.tpl-color-bar { height: 6px; }
.tpl-info { padding: 12px; }
.tpl-name { font-weight: 600; }
.tpl-desc { font-size: 12px; margin-top: 4px; }
.tpl-colors { display: flex; gap: 4px; margin-top: 8px; }
.color-dot { width: 16px; height: 16px; border-radius: 50%; border: 1px solid var(--border); }
.form { display: flex; flex-direction: column; gap: 10px; }
.form label { display: flex; flex-direction: column; font-size: 13px; gap: 4px; }
.form input, .form select { padding: 8px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; background: var(--bg); color: var(--text); }
.color-row { display: flex; gap: 12px; }
.color-row label { flex-direction: row; align-items: center; gap: 6px; }
.color-row input[type=color] { width: 36px; height: 30px; padding: 2px; border-radius: 4px; cursor: pointer; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.muted { color: var(--text-muted); }
</style>
