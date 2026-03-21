<template>
 <div v-if="user">
 <PageHeader :title="user.display_name || user.username">
 <template #actions>
 <button class="btn btn-primary" @click="editing = !editing">
 {{ editing ? '取消' : '编辑' }}
 </button>
 </template>
 </PageHeader>

 <div class="grid-2">
 <!-- 基础信息 -->
 <div class="card">
 <div class="section-title">基础信息</div>
 <div class="info-grid">
 <span class="info-label">用户名</span><span>{{ user.username }}</span>
 <span class="info-label">显示名</span><span>{{ user.display_name || '—' }}</span>
 <span class="info-label">角色</span><span class="tag tag-purple">{{ user.role }}</span>
 <span class="info-label">状态</span>
 <span class="tag" :class="statusClass(user.status)">{{ user.status }}</span>
 <span class="info-label">Emby ID</span><span>{{ user.emby_user_id || '—' }}</span>
 </div>
 </div>

 <!-- 账户配置 -->
 <div class="card">
 <div class="section-title">账户配置</div>
 <div class="info-grid">
 <span class="info-label">VIP</span><span>{{ user.is_vip ? '⭐ 是' : '否' }}</span>
 <span class="info-label">到期时间</span><span>{{ user.expire_at ? formatDate(user.expire_at) : '永久' }}</span>
 <span class="info-label">最大并发</span><span>{{ user.max_concurrent ?? '不限' }}</span>
 <span class="info-label">备注</span><span>{{ user.note || '—' }}</span>
 </div>
 </div>
 </div>

 <!-- 编辑表单 -->
 <div v-if="editing" class="card edit-form">
 <div class="section-title">编辑用户</div>
 <div class="form-grid">
 <label>显示名<input v-model="form.display_name" /></label>
 <label>
 状态
 <select v-model="form.status">
 <option value="active">活跃</option>
 <option value="disabled">禁用</option>
 <option value="expired">已过期</option>
 </select>
 </label>
 <label>备注<input v-model="form.note" /></label>
 <label>最大并发<input v-model.number="form.max_concurrent" type="number" /></label>
 </div>
 <div style="margin-top:16px; display:flex; gap:10px;">
 <button class="btn btn-primary" @click="saveUser">保存</button>
 <button class="btn btn-ghost" @click="editing = false">取消</button>
 </div>
 </div>

 <!-- 近期播放区域 -->
 <div class="card" style="margin-top:16px;">
 <div class="section-title">近期播放记录</div>
 <p style="color:var(--color-text-muted);padding:20px 0;text-align:center;">TODO: 接入 /stats/users/:id</p>
 </div>
 </div>

 <div v-else-if="loading" style="color:var(--color-text-muted);text-align:center;padding:60px;">加载中...</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import { usersApi } from '@/api/users'
import type { UserDetail } from '@/types/user'

const route = useRoute()
const user = ref<UserDetail | null>(null)
const loading = ref(false)
const editing = ref(false)
const form = reactive({
 display_name: '',
 status: 'active' as 'active',
 note: '',
 max_concurrent: null as number | null,
})

function statusClass(s: string) {
 return { active: 'tag-green', disabled: 'tag-gray', expired: 'tag-yellow' }[s] ?? 'tag-gray'
}
function formatDate(iso: string) { return new Date(iso).toLocaleDateString('zh-CN') }

async function saveUser() {
 if (!user.value) return
 user.value = await usersApi.update(user.value.user_id, form)
 editing.value = false
}

onMounted(async () => {
 loading.value = true
 try {
 user.value = await usersApi.detail(route.params.id as string)
 Object.assign(form, {
 display_name: user.value.display_name ?? '',
 status: user.value.status,
 note: user.value.note ?? '',
 max_concurrent: user.value.max_concurrent,
 })
 } finally { loading.value = false }
})
</script>

<style scoped>
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.section-title { font-weight: 600; margin-bottom: 14px; }
.info-grid { display: grid; grid-template-columns: 100px 1fr; gap: 8px 12px; align-items: center; }
.info-label { color: var(--color-text-muted); font-size: 13px; }
.edit-form { margin-top: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-grid label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--color-text-muted); }
.form-grid input, .form-grid select {
 padding: 7px 10px; background: var(--color-surface-2);
 border: 1px solid var(--color-border); border-radius: 6px;
 color: var(--color-text); font-size: 14px; outline: none;
}
</style>