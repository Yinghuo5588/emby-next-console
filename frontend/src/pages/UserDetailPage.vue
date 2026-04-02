<template>
  <div class="detail-page">
    <div class="detail-header">
      <n-button quaternary circle size="small" @click="router.back()">
        <n-icon size="20"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg></n-icon>
      </n-button>
      <span class="header-title">ç¨æ·è¯¦æ</span>
      <n-button size="small" type="error" quaternary @click="handleDelete">å é¤</n-button>
    </div>

    <div v-if="loading" class="loading-state">å è½½ä¸­...</div>
    <template v-else-if="user">
      <!-- ç¨æ·å¤´é¨ -->
      <div class="user-hero">
        <div class="hero-avatar">
          <img :src="usersApi.avatarUrl(user.user_id)" :alt="user.name" />
          <label class="avatar-upload" title="æ´æ¢å¤´å">
            <input type="file" accept="image/*" @change="onAvatarChange" hidden />
            <span class="upload-icon">ð·</span>
          </label>
        </div>
        <div class="hero-info">
          <h2 class="hero-name">{{ user.name }}</h2>
          <div class="hero-tags">
            <span v-if="user.is_admin" class="role-tag admin">ç®¡çå</span>
            <span v-if="user.is_disabled" class="role-tag disabled">å·²ç¦ç¨</span>
            <span v-if="user.is_vip" class="role-tag vip">VIP</span>
          </div>
          <div class="hero-meta">
            åå»º: {{ formatDate(user.create_date) }}
            <span v-if="user.last_login_date"> Â· æåç»å½: {{ formatDate(user.last_login_date) }}</span>
          </div>
        </div>
      </div>

      <!-- Tab -->
      <n-tabs v-model:value="activeTab" type="segment" class="detail-tabs">
        <n-tab-pane name="overview" tab="æ¦è§">
          <div class="info-section">
            <div class="info-row">
              <span class="info-label">ç¶æ</span>
              <n-button size="small" :type="user.is_disabled ? 'success' : 'warning'" quaternary @click="toggleDisabled">
                {{ user.is_disabled ? 'å¯ç¨' : 'ç¦ç¨' }}
              </n-button>
            </div>
            <div class="info-row">
              <span class="info-label">è¿ææ¶é´</span>
              <n-date-picker v-model:value="expireValue" type="date" clearable size="small" class="date-picker" @update:value="saveField('expire_date', $event)" />
            </div>
            <div class="info-row">
              <span class="info-label">å¹¶åéå¶</span>
              <n-input-number v-model:value="editForm.max_concurrent" :min="1" :max="10" size="small" style="width: 80px" @update:value="saveField('max_concurrent', $event)" />
            </div>
            <div class="info-row">
              <span class="info-label">VIP</span>
              <n-switch v-model:value="editForm.is_vip" @update:value="saveField('is_vip', $event)" />
            </div>
            <div class="info-row">
              <span class="info-label">å¤æ³¨</span>
              <n-input v-model:value="editForm.note" placeholder="ç®¡çåå¤æ³¨" size="small" @blur="saveField('note', editForm.note)" />
            </div>
            <div class="info-row">
              <span class="info-label">å¯ç </span>
              <n-button size="small" @click="showPasswordModal = true">éç½®å¯ç </n-button>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="permissions" tab="æé">
          <div class="info-section">
            <div class="info-row">
              <span class="pr-label">è¿ç¨è®¿é®</span>
              <n-switch v-model:value="permForm.enable_remote_access" @update:value="savePerm" />
            </div>
            <div class="info-row">
              <span class="pr-label">åå®¹ä¸è½½</span>
              <n-switch v-model:value="permForm.enable_content_downloading" @update:value="savePerm" />
            </div>
            <div class="info-row">
              <span class="pr-label">è§é¢è½¬ç </span>
              <n-switch v-model:value="permForm.enable_video_transcoding" @update:value="savePerm" />
            </div>
            <div class="info-row">
              <span class="pr-label">å®¶é¿åçº§</span>
              <n-select v-model:value="permForm.max_parental_rating" :options="ratingOptions" clearable size="small" style="width: 160px" @update:value="savePerm" />
            </div>
            <div class="info-row">
              <span class="pr-label">åªä½åºè®¿é®</span>
              <n-switch v-model:value="permForm.enable_all_folders" @update:value="savePerm" />
            </div>
            <div v-if="!permForm.enable_all_folders" class="info-row">
              <span class="pr-label">åè®¸çåªä½åº</span>
              <n-select v-model:value="permForm.enabled_folders" :options="folderOptions" multiple size="small" style="width: 240px" @update:value="savePerm" />
            </div>
            <div class="info-row">
              <span class="pr-label">ç¦æ­¢æªè¯çº§åå®¹</span>
              <n-select v-model:value="permForm.block_unrated_items" :options="unratedOptions" multiple size="small" style="width: 240px" @update:value="savePerm" />
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </template>

    <!-- éç½®å¯ç å¼¹çª -->
    <n-modal v-model:show="showPasswordModal" preset="dialog" title="éç½®å¯ç " positive-text="ç¡®è®¤" negative-text="åæ¶" @positive-click="resetPassword">
      <n-form-item label="æ°å¯ç ">
        <n-input v-model:value="newPassword" type="password" show-password-on="click" placeholder="è¾å¥æ°å¯ç " />
      </n-form-item>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NButton, NIcon, NTabs, NTabPane, NSwitch, NInput, NInputNumber, NSelect, NDatePicker, NModal, NFormItem, useMessage, useDialog } from 'naive-ui'
import { usersApi, type UserInfo, type UpdateUserRequest } from '@/api/users'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const userId = route.params.id as string
const user = ref<UserInfo | null>(null)
const loading = ref(true)
const activeTab = ref('overview')
const showPasswordModal = ref(false)
const newPassword = ref('')

const editForm = ref<UpdateUserRequest>({})
const permForm = ref({
  enable_remote_access: true,
  enable_content_downloading: true,
  enable_video_transcoding: true,
  max_parental_rating: null as number | null,
  enable_all_folders: true,
  enabled_folders: [] as string[],
  block_unrated_items: [] as string[],
})

const expireValue = computed({
  get: () => user.value?.expire_date ? new Date(user.value.expire_date).getTime() : null,
  set: (v: number | null) => {
    if (user.value) {
      user.value.expire_date = v ? new Date(v).toISOString() : null
    }
  },
})

const ratingOptions = [
  { label: 'æ éå¶', value: null },
  { label: 'G (å¨å¹´é¾)', value: 1 },
  { label: 'PG (å®¶é¿æå¯¼)', value: 3 },
  { label: 'PG-13', value: 4 },
  { label: 'R (éå¶çº§)', value: 5 },
  { label: 'NC-17', value: 6 },
]
const folderOptions = ref<{ label: string; value: string }[]>([])
const unratedOptions = [
  { label: 'çµå½±', value: 'Movie' },
  { label: 'å§é', value: 'Series' },
  { label: 'é³ä¹', value: 'Music' },
  { label: 'ä¹¦ç±', value: 'Book' },
  { label: 'æ¸¸æ', value: 'Game' },
  { label: 'ç´æ­çµè§', value: 'LiveTvChannel' },
]

function formatDate(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

async function loadUser() {
  loading.value = true
  try {
    const { data } = await usersApi.get(userId)
    user.value = data.data ?? data
    if (user.value) {
      editForm.value = {
        max_concurrent: user.value.max_concurrent,
        is_vip: user.value.is_vip,
        note: user.value.note,
      }
      permForm.value = {
        enable_remote_access: user.value.policy?.enable_remote_access ?? true,
        enable_content_downloading: user.value.policy?.enable_content_downloading ?? true,
        enable_video_transcoding: user.value.policy?.enable_video_transcoding ?? true,
        max_parental_rating: user.value.policy?.max_parental_rating ?? null,
        enable_all_folders: user.value.policy?.enable_all_folders ?? true,
        enabled_folders: user.value.policy?.enabled_folders ?? [],
        block_unrated_items: user.value.policy?.block_unrated_items ?? [],
      }
    }
  } catch (e: any) {
    message.error('å è½½å¤±è´¥')
  } finally {
    loading.value = false
  }
}

async function saveField(key: string, value: any) {
  try {
    const payload: UpdateUserRequest = {}
    if (key === 'expire_date') {
      payload.expire_date = value ? new Date(value).toISOString() : null
    } else {
      (payload as any)[key] = value
    }
    await usersApi.update(userId, payload)
    message.success('å·²ä¿å­', { duration: 1000 })
  } catch {
    message.error('ä¿å­å¤±è´¥')
  }
}

async function savePerm() {
  try {
    await usersApi.update(userId, {
      enable_remote_access: permForm.value.enable_remote_access,
      enable_content_downloading: permForm.value.enable_content_downloading,
      enable_video_transcoding: permForm.value.enable_video_transcoding,
      max_parental_rating: permForm.value.max_parental_rating ?? 0,
      enable_all_folders: permForm.value.enable_all_folders,
      enabled_folders: permForm.value.enabled_folders,
      block_unrated_items: permForm.value.block_unrated_items,
    })
    message.success('å·²ä¿å­', { duration: 1000 })
  } catch {
    message.error('ä¿å­å¤±è´¥')
  }
}

async function toggleDisabled() {
  if (!user.value) return
  try {
    await usersApi.update(userId, { is_disabled: !user.value.is_disabled })
    user.value.is_disabled = !user.value.is_disabled
    message.success(user.value.is_disabled ? 'å·²ç¦ç¨' : 'å·²å¯ç¨')
  } catch {
    message.error('æä½å¤±è´¥')
  }
}

async function resetPassword() {
  if (!newPassword.value) return
  try {
    await usersApi.update(userId, { password: newPassword.value })
    message.success('å¯ç å·²éç½®')
    showPasswordModal.value = false
    newPassword.value = ''
  } catch {
    message.error('éç½®å¤±è´¥')
  }
}

function handleDelete() {
  dialog.warning({
    title: 'ç¡®è®¤å é¤',
    content: `ç¡®å®å é¤ç¨æ·ã${user.value?.name}ãï¼æ­¤æä½ä¸å¯æ¤éã`,
    positiveText: 'å é¤',
    negativeText: 'åæ¶',
    onPositiveClick: async () => {
      try {
        await usersApi.delete(userId)
        message.success('å·²å é¤')
        router.replace('/users')
      } catch {
        message.error('å é¤å¤±è´¥')
      }
    },
  })
}

async function onAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  message.info('å¤´åä¸ä¼ åè½å¼åä¸­')
}

onMounted(async () => {
  await loadUser()
  try { const r = await usersApi.libraryFolders(); folderOptions.value = r.data.data ?? [] } catch {}
})
</script>

<style scoped>
.detail-page { padding: 0.5rem 0; }
.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.header-title { font-size: 1rem; font-weight: 600; }
.loading-state { text-align: center; padding: 3rem 1rem; color: var(--text-muted); }
.user-hero { display: flex; align-items: center; gap: 1rem; padding: 1rem; background: var(--surface); border-radius: 16px; border: 1px solid var(--border); margin-bottom: 1rem; }
.hero-avatar { width: 64px; height: 64px; border-radius: 16px; overflow: hidden; flex-shrink: 0; position: relative; background: var(--bg-secondary); }
.hero-avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar-upload { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.4); opacity: 0; cursor: pointer; transition: opacity 0.2s; }
.hero-avatar:hover .avatar-upload { opacity: 1; }
.upload-icon { font-size: 1.2rem; }
.hero-info { flex: 1; min-width: 0; }
.hero-name { font-size: 1.1rem; font-weight: 700; margin: 0; }
.hero-tags { display: flex; gap: 6px; margin-top: 4px; }
.role-tag { font-size: 0.65rem; font-weight: 600; padding: 2px 8px; border-radius: 6px; }
.role-tag.admin { background: var(--brand-light); color: var(--brand); }
.role-tag.disabled { background: var(--danger-light); color: var(--danger); }
.role-tag.vip { background: linear-gradient(135deg, #FFD700, #FFA500); color: #fff; }
.hero-meta { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }
.detail-tabs { margin-top: 0.5rem; }
.detail-tabs :deep(.n-tabs-nav) { border-radius: 12px; }
.info-section { background: var(--surface); border-radius: 16px; border: 1px solid var(--border); overflow: hidden; }
.info-row { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 0.85rem; color: var(--text); font-weight: 500; }
.info-value { font-size: 0.85rem; color: var(--text-muted); }
.date-picker { width: 160px; }

@media (max-width: 767px) {
  .user-hero { flex-direction: column; text-align: center; }
  .hero-tags { justify-content: center; }
}
</style>
