<template>
  <div class="notify-page">
    <PageHeader title="通知" desc="管理 Webhook 推送目标" />

    <!-- 推送目标列表 -->
    <template v-if="!loading">
      <div v-for="dest in destinations" :key="dest.id" class="dest-card anim-in" :style="{ '--i': 0 }" @click="editDest(dest)">
        <div class="dest-left">
          <div class="dest-icon" :class="{ active: dest.is_active }">
            <IosIcon name="bell" :size="18" color="#fff" :stroke-width="2" />
          </div>
          <div class="dest-body">
            <div class="dest-name">{{ dest.name }}</div>
            <div class="dest-url">{{ dest.url }}</div>
            <div class="dest-events">
              <span v-for="ev in dest.events.slice(0, 3)" :key="ev" class="event-tag">{{ eventLabel(ev) }}</span>
              <span v-if="dest.events.length > 3" class="more-tag">+{{ dest.events.length - 3 }}</span>
            </div>
            <div v-if="dest.last_error" class="dest-error">最近错误: {{ dest.last_error }}</div>
          </div>
        </div>
        <span class="status-tag" :class="dest.is_active ? 'status-on' : 'status-off'">{{ dest.is_active ? '活跃' : '停用' }}</span>
      </div>

      <div v-if="destinations.length === 0" class="empty-state">
        <IosIcon name="bell" :size="36" color="var(--text-muted)" :stroke-width="1.5" />
        <div class="empty-title">暂无推送目标</div>
        <div class="empty-desc">添加一个 Webhook URL 接收系统通知</div>
      </div>
    </template>

    <div v-else class="loading-wrap">
      <div v-for="i in 2" :key="i" class="skel-dest">
        <div class="skel-icon" />
        <div class="skel-body"><div class="skel-line w60" /><div class="skel-line w80" /></div>
      </div>
    </div>

    <!-- 添加 FAB -->
    <n-button class="fab-notify" type="primary" circle size="large" @click="openCreate">
      <IosIcon name="link" :size="20" color="#fff" :stroke-width="2.5" />
    </n-button>

    <!-- 编辑/创建弹窗 -->
    <n-modal v-model:show="showModal" preset="card" :title="editing ? '编辑推送目标' : '添加推送目标'" :style="{ maxWidth: '440px' }" class="modal-card">
      <n-form :model="form" label-placement="top">
        <n-form-item label="名称"><n-input v-model:value="form.name" placeholder="如：企业微信机器人" /></n-form-item>
        <n-form-item label="URL"><n-input v-model:value="form.url" placeholder="https://..." /></n-form-item>
        <n-form-item label="签名密钥（可选）"><n-input v-model:value="form.secret" placeholder="HMAC-SHA256 签名密钥" /></n-form-item>
        <n-form-item label="订阅事件">
          <n-checkbox-group v-model:value="form.events">
            <div style="display:flex;flex-direction:column;gap:6px">
              <n-checkbox v-for="ev in events" :key="ev.key" :value="ev.key" :label="ev.label" />
            </div>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="form.is_active" />
          <span style="margin-left:8px;font-size:13px;color:var(--text-muted)">{{ form.is_active ? '活跃' : '停用' }}</span>
        </n-form-item>
      </n-form>
      <template #action>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <n-button v-if="editing" size="small" @click="sendTest" :loading="testing">发送测试</n-button>
          <n-button v-if="editing" size="small" type="error" quaternary @click="deleteDest">删除</n-button>
          <div style="flex:1" />
          <n-button size="small" @click="showModal = false">取消</n-button>
          <n-button size="small" type="primary" @click="saveDest" :loading="saving">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NModal, NForm, NFormItem, NInput, NSwitch, NCheckbox, NCheckboxGroup, useMessage, useDialog } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import { notifyApi } from '@/api/notify'

const msg = useMessage()
const dialog = useDialog()

const loading = ref(true)
const destinations = ref<any[]>([])
const events = ref<{ key: string; label: string }[]>([])
const showModal = ref(false)
const editing = ref<any>(null)
const saving = ref(false)
const testing = ref(false)

const form = ref({ name: '', url: '', secret: '', events: [] as string[], is_active: true })

function eventLabel(key: string) {
  return events.value.find(e => e.key === key)?.label || key
}

function openCreate() {
  editing.value = null
  form.value = { name: '', url: '', secret: '', events: [], is_active: true }
  showModal.value = true
}

function editDest(dest: any) {
  editing.value = dest
  form.value = { name: dest.name, url: dest.url, secret: '', events: [...dest.events], is_active: dest.is_active }
  showModal.value = true
}

async function saveDest() {
  if (!form.value.name || !form.value.url) { msg.warning('请填写名称和URL'); return }
  saving.value = true
  try {
    if (editing.value) {
      await notifyApi.update(editing.value.id, form.value)
    } else {
      await notifyApi.create(form.value)
    }
    msg.success('已保存')
    showModal.value = false
    editing.value = null
    await loadDests()
  } catch { msg.error('保存失败') }
  finally { saving.value = false }
}

async function deleteDest() {
  if (!editing.value) return
  dialog.warning({
    title: '删除', content: `确定删除「${editing.value.name}」？`, positiveText: '删除', negativeText: '取消',
    onPositiveClick: async () => {
      await notifyApi.delete(editing.value.id)
      msg.success('已删除')
      showModal.value = false
      editing.value = null
      await loadDests()
    }
  })
}

async function sendTest() {
  if (!editing.value) return
  testing.value = true
  try {
    const res = await notifyApi.test(editing.value.id)
    if (res.data?.message === '发送成功') msg.success('测试通知已发送')
    else msg.error(res.data?.error || '发送失败')
  } catch { msg.error('测试失败') }
  finally { testing.value = false }
}

async function loadDests() {
  try { destinations.value = (await notifyApi.list()).data ?? [] } catch { destinations.value = [] }
}

async function loadEvents() {
  try { events.value = (await notifyApi.events()).data ?? [] } catch { events.value = [] }
}

onMounted(async () => {
  await Promise.all([loadDests(), loadEvents()])
  loading.value = false
})
</script>

<style scoped>
.notify-page { padding: 0.5rem 0; padding-bottom: 120px; }

/* ── 入场动画 ── */
.anim-in { opacity: 0; transform: translateY(12px); animation: slideUp 0.35s cubic-bezier(0.22,1,0.36,1) forwards; animation-delay: calc(var(--i, 0) * 50ms); }
@keyframes slideUp { to { opacity: 1; transform: translateY(0); } }

/* ── 目标卡片 ── */
.dest-card {
  display: flex; align-items: flex-start; justify-content: space-between;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 0.85rem;
  margin-bottom: 0.6rem; cursor: pointer;
  transition: all 0.15s;
}
.dest-card:active { transform: scale(0.98); background: var(--bg-secondary); }
.dest-left { display: flex; gap: 0.65rem; flex: 1; min-width: 0; }
.dest-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; background: linear-gradient(135deg, #8e8e93, #636366);
}
.dest-icon.active { background: linear-gradient(135deg, #0A84FF, #0055D6); box-shadow: 0 3px 10px rgba(0,122,255,0.25); }
.dest-body { flex: 1; min-width: 0; }
.dest-name { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.dest-url { font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
.dest-events { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 5px; }
.event-tag { font-size: 0.6rem; font-weight: 600; padding: 1px 5px; border-radius: 3px; background: rgba(0,122,255,0.08); color: var(--brand); }
.more-tag { font-size: 0.6rem; color: var(--text-muted); }
.dest-error { font-size: 0.65rem; color: #FF3B30; margin-top: 3px; }
.status-tag { font-size: 0.65rem; font-weight: 600; padding: 2px 8px; border-radius: 5px; flex-shrink: 0; }
.status-on { background: rgba(52,199,89,0.1); color: #248A3D; }
.status-off { background: rgba(142,142,147,0.1); color: #8e8e93; }

/* ── 骨架屏 ── */
.loading-wrap { padding: 0.5rem 0; }
.skel-dest { display: flex; gap: 0.65rem; padding: 0.85rem; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; margin-bottom: 0.6rem; }
.skel-icon { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; flex-shrink: 0; }
.skel-body { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.skel-line { height: 12px; border-radius: 6px; background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.skel-line.w60 { width: 60%; }
.skel-line.w80 { width: 80%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* ── 空状态 ── */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; padding: 4rem 1rem; color: var(--text-muted); }
.empty-title { font-size: 0.95rem; font-weight: 600; color: var(--text); }
.empty-desc { font-size: 0.8rem; }

/* ── FAB ── */
.fab-notify {
  position: fixed; bottom: calc(80px + 1rem); right: 1.5rem;
  width: 52px; height: 52px;
  box-shadow: 0 4px 16px rgba(0,122,255,0.3);
  z-index: 50; transition: transform 0.15s;
}
.fab-notify:active { transform: scale(0.9); }
@media (max-width: 767px) {
  .fab-notify { bottom: calc(80px + 0.5rem); right: 1rem; width: 48px; height: 48px; }
}
</style>
