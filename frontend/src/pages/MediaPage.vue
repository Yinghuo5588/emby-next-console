<template>
  <div>
    <PageHeader title="媒体管理" desc="媒体库管理与 TMDB 发现" />

    <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
      <n-tab-pane name="libraries" tab="📁 媒体库">
        <LoadingState v-if="libsLoading" compact />
        <div v-else class="lib-grid">
          <n-card v-for="lib in libraries" :key="lib.id" size="small" style="text-align:center">
            <div style="font-size:28px;margin-bottom:6px">{{ libIcon(lib.type) }}</div>
            <div style="font-weight:600">{{ lib.name }}</div>
            <div style="font-size:12px;color:var(--text-muted)">{{ lib.type || '未知' }}</div>
          </n-card>
        </div>
      </n-tab-pane>

      <n-tab-pane name="missing" tab="📋 缺集">
        <n-button type="primary" size="small" :loading="scanning" @click="scanMissing" style="margin-bottom:12px">🔍 扫描缺集</n-button>
        <LoadingState v-if="scanning" compact />
        <n-card v-for="m in missingList" :key="m.series_name" size="small" style="margin-bottom:8px">
          <div style="font-weight:600">{{ m.series_name }}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:4px">{{ m.seasons }} 季 / 已找到 {{ m.episodes_found }} 集</div>
        </n-card>
        <n-empty v-if="!scanning && !missingList.length" description="点击扫描按钮检查剧集完整性" />
      </n-tab-pane>

      <n-tab-pane name="duplicates" tab="🔁 去重">
        <n-button type="primary" size="small" :loading="dupScanning" @click="scanDuplicates" style="margin-bottom:12px">🔍 检测重复</n-button>
        <LoadingState v-if="dupScanning" compact />
        <n-card v-for="d in dupList" :key="d.name" size="small" style="margin-bottom:8px">
          <div style="font-weight:600">{{ d.name }} <n-tag type="warning" size="tiny">{{ d.count }}份</n-tag></div>
          <div v-for="item in d.items" :key="item.id" style="font-size:12px;color:var(--text-muted);margin-top:4px;padding-left:8px">
            {{ item.size_mb }} MB — {{ truncatePath(item.path) }}
          </div>
        </n-card>
        <n-empty v-if="!dupScanning && !dupList.length" description="点击检测按钮查找重复媒体" />
      </n-tab-pane>

      <n-tab-pane name="discover" tab="🔍 发现">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap">
          <n-button-group size="small">
            <n-button :type="tmdbType === 'movie' ? 'primary' : 'default'" @click="tmdbType = 'movie'; loadUpcoming()">🎬 电影</n-button>
            <n-button :type="tmdbType === 'tv' ? 'primary' : 'default'" @click="tmdbType = 'tv'; loadUpcoming()">📺 剧集</n-button>
          </n-button-group>
          <n-input v-model:value="searchQuery" placeholder="搜索 TMDB..." size="small" style="width:200px" @keyup.enter="doSearch" />
        </div>
        <LoadingState v-if="tmdbLoading" compact />
        <template v-else>
          <div style="font-size:14px;font-weight:600;margin-bottom:8px">{{ searchResults ? '搜索结果' : '即将上映' }}</div>
          <div class="media-grid">
            <n-card v-for="item in displayItems" :key="item.tmdb_id" size="small" class="media-card" @click="showDetail(item.tmdb_id)">
              <div class="mc-poster" v-if="item.poster"><img :src="item.poster" :alt="item.title" loading="lazy" /></div>
              <div class="mc-placeholder" v-else>{{ item.title?.[0] }}</div>
              <div class="mc-info">
                <div class="mc-title">{{ item.title }}</div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:2px">
                  <span v-if="item.vote_average">⭐ {{ item.vote_average.toFixed(1) }}</span>
                  <span v-if="item.release_date"> · {{ item.release_date }}</span>
                </div>
              </div>
            </n-card>
          </div>
          <n-empty v-if="!displayItems.length" description="暂无数据" />
        </template>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="showDetailModal" preset="card" :title="detailItem?.title" style="max-width:500px">
      <img v-if="detailItem?.backdrop" :src="detailItem.backdrop" style="width:100%;border-radius:8px;margin-bottom:12px" />
      <n-space v-if="detailItem?.genres?.length" size="small" style="margin-bottom:8px">
        <n-tag v-for="g in detailItem.genres" :key="g" size="tiny">{{ g }}</n-tag>
      </n-space>
      <p v-if="detailItem?.overview" style="font-size:13px;line-height:1.6;color:var(--text-muted)">{{ detailItem.overview }}</p>
      <div v-if="detailItem?.seasons?.length" style="margin-top:12px">
        <div style="font-weight:600;margin-bottom:4px">季列表</div>
        <div v-for="s in detailItem.seasons" :key="s.number" style="font-size:12px;color:var(--text-muted)">{{ s.name }} — {{ s.episodes }} 集</div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NTabs, NTabPane, NCard, NButton, NButtonGroup, NTag, NInput, NSpace, NModal, NEmpty } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { mediaApi } from '@/api/media'
import type { Library, MissingEpisode, DuplicateItem, TMDBSearchResult, TMDBDetail } from '@/api/media'

const activeTab = ref('libraries')
const libraries = ref<Library[]>([])
const libsLoading = ref(true)
const missingList = ref<MissingEpisode[]>([])
const scanning = ref(false)
const dupList = ref<DuplicateItem[]>([])
const dupScanning = ref(false)
const tmdbType = ref('movie')
const tmdbLoading = ref(false)
const upcomingItems = ref<TMDBSearchResult[]>([])
const searchResults = ref<TMDBSearchResult[] | null>(null)
const searchQuery = ref('')
const detailItem = ref<TMDBDetail | null>(null)
const showDetailModal = ref(false)

const displayItems = computed(() => searchResults.value ?? upcomingItems.value)

function libIcon(type: string) { return { movies: '🎬', tvshows: '📺', music: '🎵', books: '📚' }[type] || '📁' }
function truncatePath(p: string) { return p.length > 60 ? '...' + p.slice(-57) : p }

async function scanMissing() { scanning.value = true; try { missingList.value = (await mediaApi.missingEpisodes()).data ?? [] } finally { scanning.value = false } }
async function scanDuplicates() { dupScanning.value = true; try { dupList.value = (await mediaApi.duplicates()).data ?? [] } finally { dupScanning.value = false } }
async function loadUpcoming() { tmdbLoading.value = true; searchResults.value = null; try { upcomingItems.value = (await mediaApi.tmdbUpcoming(tmdbType.value)).data?.results ?? [] } finally { tmdbLoading.value = false } }
async function doSearch() { if (!searchQuery.value.trim()) return; tmdbLoading.value = true; try { searchResults.value = (await mediaApi.tmdbSearch(searchQuery.value.trim(), tmdbType.value)).data?.results ?? [] } finally { tmdbLoading.value = false } }
async function showDetail(tmdbId: number) { detailItem.value = (await mediaApi.tmdbDetail(tmdbId, tmdbType.value)).data ?? null; showDetailModal.value = true }

onMounted(async () => { libraries.value = (await mediaApi.libraries()).data ?? []; libsLoading.value = false; loadUpcoming() })
</script>

<style scoped>
.lib-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.media-card { padding: 0; overflow: hidden; cursor: pointer; transition: transform 0.15s; }
.media-card:hover { transform: translateY(-2px); }
.mc-poster { aspect-ratio: 2/3; overflow: hidden; background: var(--bg-secondary); }
.mc-poster img { width: 100%; height: 100%; object-fit: cover; }
.mc-placeholder { aspect-ratio: 2/3; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 700; color: var(--text-muted); background: var(--bg-secondary); }
.mc-info { padding: 8px 10px; }
.mc-title { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
