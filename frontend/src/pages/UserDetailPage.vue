<template>
  <div>
    <PageHeader title="用户详情" :desc="user?.username || ''">
      <template #actions><n-button quaternary size="small" @click="$router.back()">返回</n-button></template>
    </PageHeader>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadUser" />

    <template v-else-if="user">
      <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
        <!-- 基础资料 -->
        <n-tab-pane name="basic" tab="基础资料">
          <n-card size="small" style="max-width: 600px;">
            <n-descriptions :column="1" label-placement="left" size="small" bordered>
              <n-descriptions-item label="用户名">{{ user.username }}</n-descriptions-item>
              <n-descriptions-item label="显示名">{{ user.display_name || '—' }}</n-descriptions-item>
              <n-descriptions-item label="状态">
                <n-tag :type="user.status === 'active' ? 'success' : 'default'" size="small">{{ user.status }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="角色">{{ user.role }}</n-descriptions-item>
              <n-descriptions-item label="VIP">{{ user.is_vip ? '是' : '否' }}</n-descriptions-item>
              <n-descriptions-item label="到期时间">{{ user.expire_at || '永久' }}</n-descriptions-item>
              <n-descriptions-item label="注册时间">{{ user.created_at }}</n-descriptions-item>
              <n-descriptions-item label="备注">{{ user.note || '—' }}</n-descriptions-item>
              <n-descriptions-item label="并发限制">{{ user.max_concurrent || '全局默认' }}</n-descriptions-item>
              <n-descriptions-item label="Emby用户ID">{{ user.emby_user_id || '—' }}</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-tab-pane>

        <!-- 库权限 -->
        <n-tab-pane name="library" tab="库权限">
          <n-card size="small" style="max-width: 600px;">
            <LoadingState v-if="libraryLoading" compact />
            <n-alert v-else-if="libraryError" type="error" :title="libraryError" />
            <template v-else>
              <n-checkbox-group v-model:value="userLibraries">
                <n-space vertical>
                  <n-checkbox v-for="lib in libraries" :key="lib.id" :value="lib.id" :label="`${lib.name} (${lib.type})`" />
                </n-space>
              </n-checkbox-group>
              <n-button type="primary" size="small" style="margin-top: 12px" :loading="saving" @click="saveLibraryPermissions">保存权限</n-button>
            </template>
          </n-card>
        </n-tab-pane>

        <!-- 高级策略 -->
        <n-tab-pane name="policy" tab="高级策略">
          <n-card size="small" style="max-width: 600px;">
            <LoadingState v-if="overrideLoading" compact />
            <n-alert v-else-if="overrideError" type="error" :title="overrideError" />
            <template v-else>
              <n-form label-placement="left" label-width="120" size="small">
                <n-form-item label="并发限制">
                  <n-input-number v-model:value="override.concurrent_limit" :min="1" placeholder="留空使用全局默认" style="width: 100%" />
                </n-form-item>
                <n-form-item label="最大码率 (kbps)">
                  <n-input-number v-model:value="override.max_bitrate" :min="100" placeholder="留空使用全局默认" style="width: 100%" />
                </n-form-item>
                <n-form-item label="允许转码">
                  <n-select v-model:value="override.allow_transcode" :options="transcodeOptions" style="width: 100%" />
                </n-form-item>
                <n-form-item label="客户端黑名单">
                  <n-input v-model:value="clientBlacklistText" type="textarea" :rows="3" placeholder="每行一个客户端名称" />
                </n-form-item>
                <n-form-item label="备注">
                  <n-input v-model:value="override.note" type="textarea" :rows="2" placeholder="用户级备注" />
                </n-form-item>
              </n-form>
              <n-button type="primary" size="small" :loading="savingOverride" @click="saveOverride">保存策略</n-button>
            </template>
          </n-card>
        </n-tab-pane>

        <!-- 操作区 -->
        <n-tab-pane name="actions" tab="操作区">
          <n-card title="危险操作" size="small" style="max-width: 600px;">
            <n-space vertical>
              <div class="danger-item">
                <div><strong>强制下线</strong><div style="font-size:12px;color:var(--text-muted)">立即踢出该用户的所有在线会话</div></div>
                <n-button type="error" size="small" :loading="forceLogoutLoading" @click="forceLogout">强制下线</n-button>
              </div>
              <n-divider style="margin:8px 0" />
              <div class="danger-item">
                <div><strong>删除用户</strong><div style="font-size:12px;color:var(--text-muted)">永久删除此用户，不可恢复</div></div>
                <n-button type="error" size="small" :loading="deleteLoading" @click="deleteUser">删除用户</n-button>
              </div>
            </n-space>
          </n-card>
        </n-tab-pane>
      </n-tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NTabs, NTabPane, NCard, NButton, NTag, NDescriptions, NDescriptionsItem, NCheckboxGroup, NCheckbox, NSpace, NForm, NFormItem, NInput, NInputNumber, NSelect, NAlert, NDivider, useMessage, useDialog } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { usersApi } from '@/api/users'

const route = useRoute()
const router = useRouter()
const msg = useMessage()
const dialog = useDialog()

const user = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref('basic')

const libraries = ref<any[]>([])
const userLibraries = ref<string[]>([])
const libraryLoading = ref(false)
const libraryError = ref<string | null>(null)
const saving = ref(false)

const override = reactive({ concurrent_limit: null as number | null, max_bitrate: null as number | null, allow_transcode: null as boolean | null, client_blacklist: [] as string[], note: '' })
const overrideLoading = ref(false)
const overrideError = ref<string | null>(null)
const savingOverride = ref(false)
const forceLogoutLoading = ref(false)
const deleteLoading = ref(false)

const transcodeOptions = [
  { label: '全局默认', value: null },
  { label: '允许', value: true },
  { label: '禁止', value: false },
]

const clientBlacklistText = computed({
  get: () => override.client_blacklist?.join('\n') || '',
  set: (val) => { override.client_blacklist = val.split('\n').filter(v => v.trim()) },
})

async function loadUser() { loading.value = true; error.value = null; try { user.value = (await usersApi.get(route.params.id as string)).data } catch { error.value = '获取用户信息失败' } finally { loading.value = false } }
async function loadLibraryPermissions() { if (!user.value) return; libraryLoading.value = true; libraryError.value = null; try { const res = await usersApi.getPermissions(user.value.user_id); libraries.value = res.data?.libraries ?? []; userLibraries.value = res.data?.policy?.library_access ?? [] } catch { libraryError.value = '加载库权限失败' } finally { libraryLoading.value = false } }
async function loadOverride() { if (!user.value) return; overrideLoading.value = true; overrideError.value = null; try { const res = await usersApi.getOverride(user.value.user_id); if (res.data) Object.assign(override, res.data) } catch { overrideError.value = '加载策略失败' } finally { overrideLoading.value = false } }

async function saveLibraryPermissions() { if (!user.value) return; saving.value = true; try { await usersApi.updatePermissions(user.value.user_id, { library_access: userLibraries.value }); msg.success('库权限已保存') } catch { msg.error('保存失败') } finally { saving.value = false } }
async function saveOverride() { if (!user.value) return; savingOverride.value = true; try { await usersApi.upsertOverride(user.value.user_id, override); msg.success('策略已保存') } catch { msg.error('保存失败') } finally { savingOverride.value = false } }

async function forceLogout() {
  if (!user.value) return
  dialog.warning({ title: '确认', content: '确定强制下线该用户？', positiveText: '确认', negativeText: '取消', onPositiveClick: async () => {
    forceLogoutLoading.value = true; try { await usersApi.forceLogout(user.value.user_id); msg.success('已强制下线') } catch { msg.error('操作失败') } finally { forceLogoutLoading.value = false }
  }})
}

async function deleteUser() {
  if (!user.value) return
  dialog.error({ title: '确认删除', content: '确定删除该用户？此操作不可恢复！', positiveText: '确认删除', negativeText: '取消', onPositiveClick: async () => {
    deleteLoading.value = true; try { await usersApi.delete(user.value.user_id); msg.success('用户已删除'); router.push('/users') } catch { msg.error('删除失败') } finally { deleteLoading.value = false }
  }})
}

watch(activeTab, (tab) => { if (tab === 'library' && user.value && libraries.value.length === 0) loadLibraryPermissions(); if (tab === 'policy' && user.value) loadOverride() })
onMounted(loadUser)
</script>

<style scoped>
.danger-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
</style>
