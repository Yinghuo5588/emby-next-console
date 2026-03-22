<template>
  <div>
    <PageHeader title="创建邀请码" desc="生成新的用户邀请">
      <template #actions>
        <n-button quaternary size="small" @click="$router.push('/admin/users/invites')">← 返回列表</n-button>
      </template>
    </PageHeader>

    <n-card style="max-width: 600px;" size="small">
      <n-form label-placement="left" label-width="120" size="small">
        <n-form-item label="邀请码">
          <n-input v-model:value="form.custom_code" placeholder="留空自动生成" />
        </n-form-item>
        <n-form-item label="最大使用次数">
          <n-input-number v-model:value="form.max_uses" :min="1" :max="100" style="width:100%" />
        </n-form-item>
        <n-form-item label="有效期（天）">
          <n-input-number v-model:value="form.expires_days" :min="1" placeholder="留空永不过期" style="width:100%" />
        </n-form-item>
        <n-form-item label="并发限制">
          <n-input-number v-model:value="form.concurrent_limit" :min="1" placeholder="留空使用全局默认" style="width:100%" />
        </n-form-item>
        <n-form-item label="权限继承源">
          <n-select v-model:value="form.template_emby_user_id" :options="userOptions" clearable placeholder="不继承" style="width:100%" />
        </n-form-item>
        <n-form-item label="权限模板">
          <n-select v-model:value="form.permission_template_id" :options="templateOptions" clearable placeholder="不使用模板" style="width:100%" />
        </n-form-item>
      </n-form>
      <n-button type="primary" block :loading="creating" @click="handleCreate">创建邀请码</n-button>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NInputNumber, NSelect, NButton, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import { invitesApi } from '@/api/invites'
import { templatesApi, type PermissionTemplate } from '@/api/templates'
import { usersApi } from '@/api/users'

const router = useRouter()
const msg = useMessage()
const creating = ref(false)
const users = ref<any[]>([])
const templates = ref<PermissionTemplate[]>([])

const form = reactive({ custom_code: '', max_uses: 1, expires_days: null as number | null, concurrent_limit: null as number | null, template_emby_user_id: '', permission_template_id: null as number | null })

const userOptions = computed(() => users.value.map(u => ({ label: `${u.username}（${u.display_name || '无备注'}）`, value: u.emby_user_id })))
const templateOptions = computed(() => templates.value.map(t => ({ label: t.name, value: t.id })))

async function handleCreate() {
  creating.value = true
  try {
    await invitesApi.create({ custom_code: form.custom_code || null, max_uses: form.max_uses, expires_days: form.expires_days, concurrent_limit: form.concurrent_limit, template_emby_user_id: form.template_emby_user_id || null, permission_template_id: form.permission_template_id })
    msg.success('邀请码已创建')
    router.push('/admin/users/invites')
  } catch (e: any) { msg.error(e.response?.data?.detail || '创建失败') }
  finally { creating.value = false }
}

onMounted(async () => { const [uRes, tRes] = await Promise.all([usersApi.list({ page_size: 200 }), templatesApi.list()]); users.value = uRes.data?.items ?? []; templates.value = tRes.data?.items ?? [] })
</script>
