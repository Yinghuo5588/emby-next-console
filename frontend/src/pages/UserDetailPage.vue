<template>
  <div>
    <PageHeader title="用户详情" desc="">
      <template #actions><button class="btn btn-ghost" @click="$router.back()">返回</button></template>
    </PageHeader>
    <LoadingState v-if="loading" height="200px" />
    <ErrorState v-else-if="error" :message="error" @retry="loadUser" />
    <template v-else-if="user">
      <div class="info-grid">
        <div class="card">
          <div class="info-row"><span class="label">用户名</span><span>{{ user.username }}</span></div>
          <div class="info-row"><span class="label">显示名</span><span>{{ user.display_name || '—' }}</span></div>
          <div class="info-row"><span class="label">状态</span><span class="tag" :class="user.status === 'active' ? 'tag-green' : 'tag-gray'">{{ user.status }}</span></div>
          <div class="info-row"><span class="label">角色</span><span>{{ user.role }}</span></div>
          <div class="info-row"><span class="label">VIP</span><span>{{ user.is_vip ? '是' : '否' }}</span></div>
          <div class="info-row"><span class="label">到期时间</span><span>{{ user.expire_at || '永久' }}</span></div>
          <div class="info-row"><span class="label">注册时间</span><span>{{ user.created_at }}</span></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { usersApi } from '@/api/users'

const route = useRoute()
const user = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function loadUser() {
  loading.value = true; error.value = null
  try { user.value = (await usersApi.get(route.params.id as string)).data }
  catch { error.value = '获取用户信息失败' }
  finally { loading.value = false }
}

onMounted(loadUser)
</script>

<style scoped>
.info-grid { max-width: 600px; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.info-row:last-child { border-bottom: none; }
.label { color: var(--text-muted); }
</style>
