<template>
  <div>
    <PageHeader title="创建邀请码" desc="生成新的用户邀请">
      <template #actions>
        <RouterLink to="/admin/users/invites" class="btn btn-ghost">← 返回列表</RouterLink>
      </template>
    </PageHeader>

    <div class="card" style="max-width: 600px;">
      <form @submit.prevent="handleCreate">
        <div class="form-group">
          <label>邀请码</label>
          <input v-model="form.custom_code" placeholder="留空自动生成" />
          <div class="hint">8位大写字母+数字，也可自定义</div>
        </div>

        <div class="form-group">
          <label>最大使用次数</label>
          <input v-model.number="form.max_uses" type="number" min="1" max="100" />
        </div>

        <div class="form-group">
          <label>有效期（天）</label>
          <input v-model.number="form.expires_days" type="number" min="1" placeholder="留空永不过期" />
        </div>

        <div class="form-group">
          <label>并发限制</label>
          <input v-model.number="form.concurrent_limit" type="number" min="1" placeholder="留空使用全局默认" />
        </div>

        <div class="form-group">
          <label>权限继承源</label>
          <select v-model="form.template_emby_user_id">
            <option value="">不继承</option>
            <option v-for="u in users" :key="u.emby_user_id" :value="u.emby_user_id">
              {{ u.username }}（{{ u.display_name || '无备注' }}）
            </option>
          </select>
          <div class="hint">选择一个已有用户，注册后将复制其库权限和策略</div>
        </div>

        <div class="form-group">
          <label>权限模板</label>
          <select v-model="form.permission_template_id">
            <option :value="null">不使用模板</option>
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>

        <button type="submit" class="btn btn-primary" :disabled="creating">
          {{ creating ? '创建中...' : '创建邀请码' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import { invitesApi } from '@/api/invites'
import { templatesApi, type PermissionTemplate } from '@/api/templates'
import { usersApi } from '@/api/users'

const router = useRouter()
const creating = ref(false)
const users = ref<any[]>([])
const templates = ref<PermissionTemplate[]>([])

const form = reactive({
  custom_code: '',
  max_uses: 1,
  expires_days: null as number | null,
  concurrent_limit: null as number | null,
  template_emby_user_id: '',
  permission_template_id: null as number | null,
})

async function handleCreate() {
  creating.value = true
  try {
    await invitesApi.create({
      custom_code: form.custom_code || null,
      max_uses: form.max_uses,
      expires_days: form.expires_days,
      concurrent_limit: form.concurrent_limit,
      template_emby_user_id: form.template_emby_user_id || null,
      permission_template_id: form.permission_template_id,
    })
    router.push('/admin/users/invites')
  } catch (e: any) {
    alert(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  const [uRes, tRes] = await Promise.all([usersApi.list({ page_size: 200 }), templatesApi.list()])
  users.value = uRes.data?.items ?? []
  templates.value = tRes.data?.items ?? []
})
</script>

<style scoped>
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text); }
.form-group input, .form-group select { width: 100%; }
.hint { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
</style>