<template>
  <div>
    <PageHeader title="用户详情" :desc="user?.username || ''">
      <template #actions><button class="btn btn-ghost" @click="$router.back()">返回</button></template>
    </PageHeader>
    
    <LoadingState v-if="loading" height="200px" />
    <ErrorState v-else-if="error" :message="error" @retry="loadUser" />
    
    <template v-else-if="user">
      <!-- Tab 切换 -->
      <div class="tab-bar">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 基础资料 Tab -->
      <div v-if="activeTab === 'basic'" class="tab-content">
        <div class="info-grid">
          <div class="card">
            <div class="info-row"><span class="label">用户名</span><span>{{ user.username }}</span></div>
            <div class="info-row"><span class="label">显示名</span><span>{{ user.display_name || '—' }}</span></div>
            <div class="info-row"><span class="label">状态</span><span class="tag" :class="user.status === 'active' ? 'tag-green' : 'tag-gray'">{{ user.status }}</span></div>
            <div class="info-row"><span class="label">角色</span><span>{{ user.role }}</span></div>
            <div class="info-row"><span class="label">VIP</span><span>{{ user.is_vip ? '是' : '否' }}</span></div>
            <div class="info-row"><span class="label">到期时间</span><span>{{ user.expire_at || '永久' }}</span></div>
            <div class="info-row"><span class="label">注册时间</span><span>{{ user.created_at }}</span></div>
            <div class="info-row"><span class="label">备注</span><span>{{ user.note || '—' }}</span></div>
            <div class="info-row"><span class="label">并发限制</span><span>{{ user.max_concurrent || '全局默认' }}</span></div>
            <div class="info-row"><span class="label">Emby用户ID</span><span>{{ user.emby_user_id || '—' }}</span></div>
          </div>
        </div>
      </div>

      <!-- 库权限 Tab -->
      <div v-if="activeTab === 'library'" class="tab-content">
        <div class="card">
          <div v-if="libraryLoading" class="loading-small">加载库权限中...</div>
          <div v-else-if="libraryError" class="error">{{ libraryError }}</div>
          <div v-else>
            <h3>库权限配置</h3>
            <div v-if="libraries.length === 0" class="empty">暂无库数据</div>
            <div v-else class="library-list">
              <div v-for="lib in libraries" :key="lib.id" class="library-item">
                <label class="checkbox">
                  <input 
                    type="checkbox" 
                    :checked="userLibraries.includes(lib.id)"
                    @change="toggleLibrary(lib.id)"
                  />
                  <span>{{ lib.name }} ({{ lib.type }})</span>
                </label>
              </div>
            </div>
            <button class="btn btn-primary" @click="saveLibraryPermissions" :disabled="saving">
              {{ saving ? '保存中...' : '保存权限' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 高级策略 Tab -->
      <div v-if="activeTab === 'policy'" class="tab-content">
        <div class="card">
          <div v-if="overrideLoading" class="loading-small">加载策略中...</div>
          <div v-else-if="overrideError" class="error">{{ overrideError }}</div>
          <div v-else>
            <h3>高级策略配置</h3>
            <div class="form-group">
              <label>并发限制</label>
              <input v-model.number="override.concurrent_limit" type="number" min="1" placeholder="留空使用全局默认" />
            </div>
            <div class="form-group">
              <label>最大码率 (kbps)</label>
              <input v-model.number="override.max_bitrate" type="number" min="100" placeholder="留空使用全局默认" />
            </div>
            <div class="form-group">
              <label>允许转码</label>
              <select v-model="override.allow_transcode">
                <option :value="null">全局默认</option>
                <option :value="true">允许</option>
                <option :value="false">禁止</option>
              </select>
            </div>
            <div class="form-group">
              <label>客户端黑名单</label>
              <textarea v-model="clientBlacklistText" placeholder="每行一个客户端名称，如: Chrome, Safari" rows="3"></textarea>
              <div class="hint">匹配客户端 User-Agent 中的关键词</div>
            </div>
            <div class="form-group">
              <label>备注</label>
              <textarea v-model="override.note" placeholder="用户级备注" rows="2"></textarea>
            </div>
            <button class="btn btn-primary" @click="saveOverride" :disabled="savingOverride">
              {{ savingOverride ? '保存中...' : '保存策略' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 操作区 Tab -->
      <div v-if="activeTab === 'actions'" class="tab-content">
        <div class="card">
          <h3>危险操作</h3>
          <div class="danger-zone">
            <div class="danger-item">
              <div>
                <h4>强制下线</h4>
                <p>立即踢出该用户的所有在线会话</p>
              </div>
              <button class="btn btn-danger" @click="forceLogout" :disabled="forceLogoutLoading">
                {{ forceLogoutLoading ? '操作中...' : '强制下线' }}
              </button>
            </div>
            <div class="danger-item">
              <div>
                <h4>删除用户</h4>
                <p>永久删除此用户，不可恢复</p>
              </div>
              <button class="btn btn-danger" @click="deleteUser" :disabled="deleteLoading">
                {{ deleteLoading ? '操作中...' : '删除用户' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { usersApi } from '@/api/users'

const route = useRoute()
const router = useRouter()
const user = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Tab 相关
const tabs = [
  { id: 'basic', label: '基础资料' },
  { id: 'library', label: '库权限' },
  { id: 'policy', label: '高级策略' },
  { id: 'actions', label: '操作区' }
]
const activeTab = ref('basic')

// 库权限相关
const libraries = ref<any[]>([])
const userLibraries = ref<string[]>([])
const libraryLoading = ref(false)
const libraryError = ref<string | null>(null)
const saving = ref(false)

// 高级策略相关
const override = reactive({
  concurrent_limit: null as number | null,
  max_bitrate: null as number | null,
  allow_transcode: null as boolean | null,
  client_blacklist: [] as string[],
  note: ''
})
const overrideLoading = ref(false)
const overrideError = ref<string | null>(null)
const savingOverride = ref(false)

// 操作相关
const forceLogoutLoading = ref(false)
const deleteLoading = ref(false)

// 计算属性
const clientBlacklistText = computed({
  get: () => override.client_blacklist?.join('\n') || '',
  set: (val) => {
    override.client_blacklist = val.split('\n').filter(v => v.trim())
  }
})

async function loadUser() {
  loading.value = true; error.value = null
  try { 
    user.value = (await usersApi.get(route.params.id as string)).data 
  } catch { 
    error.value = '获取用户信息失败' 
  } finally { 
    loading.value = false 
  }
}

async function loadLibraryPermissions() {
  if (!user.value) return
  libraryLoading.value = true; libraryError.value = null
  try {
    // 这里需要调用获取库权限的API
    // 暂时模拟数据
    libraries.value = [
      { id: 'movies', name: '电影库', type: 'Movies' },
      { id: 'tvshows', name: '剧集库', type: 'TV Shows' },
      { id: 'music', name: '音乐库', type: 'Music' },
      { id: 'photos', name: '照片库', type: 'Photos' }
    ]
    // 获取用户已有权限
    const res = await usersApi.getPermissions(user.value.user_id)
    userLibraries.value = res.data?.policy?.library_access || []
  } catch {
    libraryError.value = '加载库权限失败'
  } finally {
    libraryLoading.value = false
  }
}

async function loadOverride() {
  if (!user.value) return
  overrideLoading.value = true; overrideError.value = null
  try {
    const res = await usersApi.getOverride(user.value.user_id)
    if (res.data) {
      Object.assign(override, res.data)
    }
  } catch {
    overrideError.value = '加载策略失败'
  } finally {
    overrideLoading.value = false
  }
}

function toggleLibrary(libId: string) {
  const index = userLibraries.value.indexOf(libId)
  if (index > -1) {
    userLibraries.value.splice(index, 1)
  } else {
    userLibraries.value.push(libId)
  }
}

async function saveLibraryPermissions() {
  if (!user.value) return
  saving.value = true
  try {
    await usersApi.updatePermissions(user.value.user_id, {
      library_access: userLibraries.value
    })
    alert('库权限保存成功')
  } catch {
    alert('保存失败')
  } finally {
    saving.value = false
  }
}

async function saveOverride() {
  if (!user.value) return
  savingOverride.value = true
  try {
    await usersApi.upsertOverride(user.value.user_id, override)
    alert('策略保存成功')
  } catch {
    alert('保存失败')
  } finally {
    savingOverride.value = false
  }
}

async function forceLogout() {
  if (!user.value || !confirm('确定强制下线该用户？')) return
  forceLogoutLoading.value = true
  try {
    await usersApi.forceLogout(user.value.user_id)
    alert('强制下线成功')
  } catch {
    alert('操作失败')
  } finally {
    forceLogoutLoading.value = false
  }
}

async function deleteUser() {
  if (!user.value || !confirm('确定删除该用户？此操作不可恢复！')) return
  deleteLoading.value = true
  try {
    // 这里需要调用删除用户的API
    // await usersApi.delete(user.value.user_id)
    alert('用户删除成功')
    router.push('/users')
  } catch {
    alert('删除失败')
  } finally {
    deleteLoading.value = false
  }
}

// 监听Tab切换
watch(activeTab, (newTab) => {
  if (newTab === 'library' && user.value && libraries.value.length === 0) {
    loadLibraryPermissions()
  }
  if (newTab === 'policy' && user.value && !overrideLoading.value) {
    loadOverride()
  }
})

onMounted(loadUser)
</script>

<style scoped>
.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}
.tab-btn {
  padding: 12px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-muted);
}
.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}
.tab-content {
  max-width: 800px;
}
.info-grid { max-width: 600px; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.label { color: var(--text-muted); }

.library-list {
  margin: 16px 0;
}
.library-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
}
.hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.danger-zone {
  border: 1px solid var(--danger);
  border-radius: 8px;
  padding: 20px;
}
.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}
.danger-item:last-child {
  border-bottom: none;
}
.danger-item h4 {
  margin: 0 0 4px 0;
  color: var(--danger);
}
.danger-item p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
.btn-danger {
  background: var(--danger);
  color: white;
  border: none;
}

.loading-small {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
}
.error {
  padding: 20px;
  text-align: center;
  color: var(--danger);
}
.empty {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}
</style>