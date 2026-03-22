<template>
  <div>
    <PageHeader title="媒体管理" desc="媒体库管理与 TMDB 发现" />

    <!-- Tab 栏 -->
    <div class="tab-bar">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.icon }} {{ t.label }}
      </button>
    </div>

    <!-- Tab 1: 媒体库 -->
    <div v-show="activeTab === 'libraries'">
      <LoadingState v-if="libsLoading" height="80px" />
      <div v-else class="lib-grid">
        <div v-for="lib in libraries" :key="lib.id" class="card lib-card">
          <div class="lib-icon">{{ libIcon(lib.type) }}</div>
          <div class="lib-name">{{ lib.name }}</div>
          <div class="lib-type muted">{{ lib.type || '未知' }}</div>
        </div>
      </div>
    </div>

    <!-- Tab 2: 缺集检测 -->
    <div v-show="activeTab === 'missing'">
      <div class="card" style="margin-bottom: 12px;">
        <button class="btn btn-primary" @click="scanMissing" :disabled="scanning">
          {{ scanning ? '扫描中...' : '🔍 扫描缺集' }}
        </button>
      </div>
      <LoadingState v-if="scanning" height="80px" />
      <div v-else-if="missingList.length">
        <div v-for="m in missingList" :key="m.series_name" class="card" style="padding: 12px; margin-bottom: 8px;">
          <div style="font-weight: 600;">{{ m.series_name }}</div>
          <div class="muted" style="font-size: 12px; margin-top: 4px;">
            {{ m.seasons }} 季 / 已找到 {{ m.episodes_found }} 集
          </div>
        </div>
      </div>
      <EmptyState v-else-if="!scanning" title="暂无缺集" desc="点击扫描按钮检查剧集完整性" />
    </div>

    <!-- Tab 3: 去重 -->
    <div v-show="activeTab === 'duplicates'">
      <div class="card" style="margin-bottom: 12px;">
        <button class="btn btn-primary" @click="scanDuplicates" :disabled="dupScanning">
          {{ dupScanning ? '扫描中...' : '🔍 检测重复' }}
        </button>
      </div>
      <LoadingState v-if="dupScanning" height="80px" />
      <div v-else-if="dupList.length">
        <div v-for="d in dupList" :key="d.name" class="card" style="padding: 12px; margin-bottom: 8px;">
          <div style="font-weight: 600;">{{ d.name }} <span class="tag tag-yellow">{{ d.count }}份</span></div>
          <div v-for="item in d.items" :key="item.id" class="muted" style="font-size: 12px; margin-top: 4px; padding-left: 8px;">
            {{ item.size_mb }} MB — {{ truncatePath(item.path) }}
          </div>
        </div>
      </div>
      <EmptyState v-else-if="!dupScanning" title="未发现重复" desc="点击检测按钮查找重复媒体" />
    </div>

    <!-- Tab 4: TMDB 发现 -->
    <div v-show="activeTab === 'discover'">
      <div class="discover-header">
        <div class="tab-bar" style="margin-bottom: 0;">
          <button class="tab-btn btn-sm" :class="{ active: tmdbType === 'movie' }" @click="tmdbType = 'movie'; loadUpcoming()">🎬 电影</button>
          <button class="tab-btn btn-sm" :class="{ active: tmdbType === 'tv' }" @click="tmdbType = 'tv'; loadUpcoming()">📺 剧集</button>
        </div>
        <input v-model="searchQuery" placeholder="搜索 TMDB..." @keyup.enter="doSearch" style="width: 200px;" />
      </div>

      <LoadingState v-if="tmdbLoading" height="120px" />
      <div v-else>
        <div class="section-title">{{ searchResults ? '搜索结果' : '即将上映' }}</div>
        <div class="media-grid">
          <div v-for="item in displayItems" :key="item.tmdb_id" class="card media-card" @click="showDetail(item.tmdb_id)">
            <div class="mc-poster" v-if="item.poster">
              <img :src="item.poster" :alt="item.title" loading="lazy" />
            </div>
            <div class="mc-poster mc-placeholder" v-else>{{ item.title?.[0] }}</div>
            <div class="mc-info">
              <div class="mc-title">{{ item.title }}</div>
              <div class="mc-meta">
                <span v-if="item.vote_average" class="mc-rating">⭐ {{ item.vote_average.toFixed(1) }}</span>
                <span v-if="item.release_date" class="muted">{{ item.release_date }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="displayItems.length === 0" class="muted" style="text-align:center; padding: 32px;">暂无数据</div>
      </div>
    </div>

    <!-- TMDB 详情弹窗 -->
    <div v-if="detailItem" class="modal-overlay" @click.self="detailItem = null">
      <div class="modal card" style="max-width: 500px;">
        <div class="modal-head">
          <h3>{{ detailItem.title }}</h3>
          <button class="btn btn-ghost" @click="detailItem = null">✕</button>
        </div>
        <div v-if="detailItem.backdrop" class="detail-backdrop">
          <img :src="detailItem.backdrop" />
        </div>
        <div v-if="detailItem.genres?.length" style="margin-bottom: 8px;">
          <span v-for="g in detailItem.genres" :key="g" class="tag tag-gray" style="margin-right: 4px;">{{ g }}</span>
        </div>
        <p v-if="detailItem.overview" class="muted" style="font-size: 13px; line-height: 1.6;">{{ detailItem.overview }}</p>
        <div v-if="detailItem.seasons?.length" style="margin-top: 12px;">
          <div class="section-title">季列表</div>
          <div v-for="s in detailItem.seasons" :key="s.number" class="muted" style="font-size: 12px;">
            {{ s.name }} — {{ s.episodes }} 集
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { mediaApi } from '@/api/media'
import type { Library, MissingEpisode, DuplicateItem, TMDBSearchResult, TMDBDetail } from '@/api/media'

const activeTab = ref('libraries')

const tabs = [
  { key: 'libraries', icon: '📁', label: '媒体库' },
  { key: 'missing', icon: '📋', label: '缺集' },
  { key: 'duplicates', icon: '🔁', label: '去重' },
  { key: 'discover', icon: '🔍', label: '发现' },
]

// 媒体库
const libraries = ref<Library[]>([])
const libsLoading = ref(true)

// 缺集
const missingList = ref<MissingEpisode[]>([])
const scanning = ref(false)

// 去重
const dupList = ref<DuplicateItem[]>([])
const dupScanning = ref(false)

// TMDB
const tmdbType = ref('movie')
const tmdbLoading = ref(false)
const upcomingItems = ref<TMDBSearchResult[]>([])
const searchResults = ref<TMDBSearchResult[] | null>(null)
const searchQuery = ref('')
const detailItem = ref<TMDBDetail | null>(null)

const displayItems = computed(() => searchResults.value ?? upcomingItems.value)

function libIcon(type: string) {
  return { movies: '🎬', tvshows: '📺', music: '🎵', books: '📚' }[type] || '📁'
}

function truncatePath(p: string) {
  return p.length > 60 ? '...' + p.slice(-57) : p
}

async function scanMissing() {
  scanning.value = true
  try {
    const res = await mediaApi.missingEpisodes()
    missingList.value = res.data ?? []
  } finally { scanning.value = false }
}

async function scanDuplicates() {
  dupScanning.value = true
  try {
    const res = await mediaApi.duplicates()
    dupList.value = res.data ?? []
  } finally { dupScanning.value = false }
}

async function loadUpcoming() {
  tmdbLoading.value = true
  searchResults.value = null
  try {
    const res = await mediaApi.tmdbUpcoming(tmdbType.value)
    upcomingItems.value = res.data?.results ?? []
  } finally { tmdbLoading.value = false }
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  tmdbLoading.value = true
  try {
    const res = await mediaApi.tmdbSearch(searchQuery.value.trim(), tmdbType.value)
    searchResults.value = res.data?.results ?? []
  } finally { tmdbLoading.value = false }
}

async function showDetail(tmdbId: number) {
  const res = await mediaApi.tmdbDetail(tmdbId, tmdbType.value)
  detailItem.value = res.data ?? null
}

onMounted(async () => {
  const res = await mediaApi.libraries()
  libraries.value = res.data ?? []
  libsLoading.value = false
  loadUpcoming()
})
</script>

<style scoped>
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; overflow-x: auto; }
.tab-btn { padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); color: var(--text-muted); cursor: pointer; font-size: 13px; white-space: nowrap; }
.tab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.lib-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.lib-card { text-align: center; padding: 20px; cursor: default; }
.lib-icon { font-size: 32px; margin-bottom: 8px; }
.lib-name { font-weight: 600; font-size: 14px; }
.lib-type { font-size: 12px; margin-top: 4px; }
.muted { color: var(--text-muted); }
.discover-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 8px; flex-wrap: wrap; }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.media-card { padding: 0; overflow: hidden; cursor: pointer; transition: transform 0.15s; }
.media-card:hover { transform: translateY(-2px); }
.mc-poster { aspect-ratio: 2/3; overflow: hidden; background: var(--bg-secondary); }
.mc-poster img { width: 100%; height: 100%; object-fit: cover; }
.mc-placeholder { display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 700; color: var(--text-muted); }
.mc-info { padding: 8px 10px; }
.mc-title { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mc-meta { display: flex; gap: 6px; margin-top: 4px; font-size: 11px; }
.mc-rating { color: #f59e0b; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 16px; }
.modal { width: 100%; max-height: 80vh; overflow-y: auto; padding: 20px; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.modal-head h3 { margin: 0; }
.detail-backdrop { margin-bottom: 12px; border-radius: 8px; overflow: hidden; }
.detail-backdrop img { width: 100%; }
</style>