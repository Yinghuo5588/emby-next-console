<template>
  <div class="ctrl-page">
    <PageHeader title="管控中心">
    </PageHeader>

    <!-- 二级导航 -->
    <div class="risk-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="risk-tab"
        :class="{ active: activeTab === tab.key, 'has-drawer': tab.key === 'overview' && activeTab === 'overview' }"
        @click="handleTabClick(tab.key)"
      >
        {{ tab.label }}
        <svg v-if="tab.key === 'overview'" class="tab-chevron" :class="{ open: showDrawer }" width="12" height="12" viewBox="0 0 12 12"><polyline points="3,4.5 6,7.5 9,4.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>

    <!-- 操作抽屉 -->
    <div v-if="showDrawer" class="action-drawer">
      <div class="drawer-actions">
        <n-button size="small" :loading="scanning" @click="handleScan">
          <span class="btn-content">
            <IosIcon name="zap" :size="16" :stroke-width="2" style="flex-shrink:0" />
            <span>扫描</span>
          </span>
        </n-button>
        <n-button size="small" type="warning" :loading="sweeping" @click="handleSweep">
          <span class="btn-content">
            <IosIcon name="fire" :size="16" :stroke-width="2" style="flex-shrink:0" />
            <span>扫荡</span>
          </span>
        </n-button>
        <n-button size="small" @click="loadAll">
          <span class="btn-content">
            <IosIcon name="filter" :size="16" :stroke-width="2" style="flex-shrink:0" />
            <span>刷新</span>
          </span>
        </n-button>
      </div>
    </div>

    <!-- ═══ 总览 ═══ -->
    <template v-if="activeTab === 'overview'">
      <div class="overview-row">
        <div class="rkpi-card" :class="{ danger: (summary?.open_count ?? 0) > 0 }" style="--i:0">
          <div class="rkpi-icon" :class="(summary?.open_count ?? 0) > 0 ? 'rkpi-red' : 'rkpi-gray'"><IosIcon name="alert" :size="18" color="#fff" :stroke-width="2" /></div>
          <div class="rkpi-body"><span class="rkpi-val">{{ summary?.open_count ?? 0 }}</span><span class="rkpi-lbl">待处理</span></div>
        </div>
        <div class="rkpi-card" :class="{ danger: (summary?.high_count ?? 0) > 0 }" style="--i:1">
          <div class="rkpi-icon" :class="(summary?.high_count ?? 0) > 0 ? 'rkpi-red' : 'rkpi-gray'"><IosIcon name="zap" :size="18" color="#fff" :stroke-width="2" /></div>
          <div class="rkpi-body"><span class="rkpi-val">{{ summary?.high_count ?? 0 }}</span><span class="rkpi-lbl">高危</span></div>
        </div>
        <div class="rkpi-card" style="--i:2">
          <div class="rkpi-icon rkpi-green"><IosIcon name="play" :size="18" color="#fff" :stroke-width="2" /></div>
          <div class="rkpi-body"><span class="rkpi-val">{{ liveSessions.length }}</span><span class="rkpi-lbl">播放中</span></div>
        </div>
        <div class="rkpi-card" style="--i:3" @click="activeTab = 'policy'">
          <div class="rkpi-icon rkpi-purple"><IosIcon name="trash" :size="18" color="#fff" :stroke-width="2" /></div>
          <div class="rkpi-body"><span class="rkpi-val">{{ blacklist.length }}</span><span class="rkpi-lbl">黑名单</span></div>
        </div>
      </div>

      <!-- 实时播放 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="play" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>实时播放</span>
          </span>
          <n-button text size="tiny" @click="loadSessions">刷新</n-button>
        </div>
        <LoadingState v-if="sessionsLoading" compact />
        <n-empty v-else-if="liveSessions.length === 0" description="暂无播放" />
        <div v-else class="session-list">
          <div v-for="s in liveSessions" :key="s.Id" class="session-card">
            <div class="sc-top">
              <span class="sc-user-wrap">
                <IosIcon name="users" :size="16" color="var(--text-muted)" :stroke-width="1.5" style="flex-shrink:0" />
                <span class="sc-user">{{ s.UserName || '未知' }}</span>
              </span>
              <n-tag v-if="s.Client" size="tiny" type="info">{{ s.Client }}</n-tag>
            </div>
            <div class="sc-media">{{ s.NowPlayingItem?.Name || '-' }}</div>
            <div class="sc-actions">
              <n-button size="tiny" type="error" :loading="kicking === s.Id" @click="doKick(s.Id, s.DeviceId || '', 'soft')">停止</n-button>
              <n-button size="tiny" type="error" quaternary :loading="kicking === s.Id+'h'" @click="doKick(s.Id, s.DeviceId || '', 'hard')">强踢</n-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 并发状态 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="chart" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>并发状态</span>
          </span>
          <n-button text size="tiny" @click="loadConcurrent">刷新</n-button>
        </div>
        <LoadingState v-if="concurrentLoading" compact />
        <n-empty v-else-if="concurrent.length === 0" description="无活跃用户" />
        <div v-else class="cc-list">
          <div v-for="u in concurrent" :key="u.user_id" class="cc-card" :class="{ exceeded: u.exceeded }">
            <div class="cc-top">
              <span class="cc-name">{{ u.user_name || u.user_id }}</span>
              <n-tag :type="u.exceeded ? 'error' : 'success'" size="tiny">{{ u.current }}/{{ u.max }}</n-tag>
            </div>
            <div v-for="sess in u.sessions" :key="sess.session_id" class="cc-sess">
              <span class="cc-client">{{ sess.client }}</span>
              <span class="cc-title">{{ sess.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 风控事件 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="alert" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>风控事件</span>
          </span>
          <div class="filter-pills">
            <button v-for="s in ['', 'open', 'resolved', 'ignored']" :key="s" class="pill" :class="{ active: evFilter.status === s }" @click="evFilter.status = s; loadEvents()">{{ sLabel(s) }}</button>
          </div>
        </div>
        <LoadingState v-if="evLoading && events.length === 0" />
        <n-empty v-else-if="events.length === 0" description="系统正常 ✅" />
        <div v-else class="ev-list">
          <div v-for="ev in events" :key="ev.event_id" class="ev-item" :class="{ 'ev-high': ev.severity === 'high' && ev.status === 'open', 'ev-open': ev.status === 'open' }">
            <div class="ev-main">
              <div class="ev-title">
                <n-tag :type="svType(ev.severity)" size="tiny">
                  <span class="sev-tag-inner">
                    <span class="sev-dot" :class="`sev-${ev.severity}`"></span>
                    <span>{{ svLabel(ev.severity) }}</span>
                  </span>
                </n-tag>
                <span>{{ ev.title }}</span>
              </div>
              <div class="ev-desc">{{ ev.description || '-' }}</div>
              <div class="ev-time">{{ fmtTime(ev.detected_at) }}</div>
            </div>
            <div v-if="ev.status === 'open'" class="ev-acts">
              <n-button size="tiny" type="primary" :loading="acting === ev.event_id" @click="doAction(ev.event_id, 'resolve')">解决</n-button>
              <n-button size="tiny" quaternary :loading="acting === ev.event_id" @click="doAction(ev.event_id, 'ignore')">忽略</n-button>
            </div>
            <div v-else class="ev-status">
              <n-tag :type="ev.status === 'resolved' ? 'success' : 'default'" size="small">{{ ev.status === 'resolved' ? '已解决' : '已忽略' }}</n-tag>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ 策略 ═══ -->
    <template v-if="activeTab === 'policy'">
      <!-- 策略配置 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="settings" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>策略配置</span>
          </span>
          <n-button text size="tiny" :loading="policyLoading" @click="savePolicy">保存</n-button>
        </div>
        <div v-if="policy" class="policy-grid">
          <div class="policy-group policy-client">
            <div class="pg-title">客户端管控</div>
            <div class="pr-row">
              <span class="pr-label">模式</span>
              <div class="pr-radio">
                <button class="rbtn" :class="{ active: policy.client_policy.mode === 'blacklist' }" @click="policy.client_policy.mode = 'blacklist'">黑名单</button>
                <button class="rbtn" :class="{ active: policy.client_policy.mode === 'whitelist' }" @click="policy.client_policy.mode = 'whitelist'">白名单</button>
              </div>
            </div>
            <div class="pr-row">
              <span class="pr-label">模糊匹配</span>
              <n-switch v-model:value="policy.client_policy.fuzzy_match" size="small" />
            </div>
            <div class="pr-row">
              <span class="pr-label">执行动作</span>
              <div class="pr-radio">
                <button v-for="a in clientActions" :key="a.value" class="rbtn" :class="{ active: policy.client_policy.action === a.value }" @click="policy.client_policy.action = a.value">{{ a.label }}</button>
              </div>
            </div>
            <div class="pr-row">
              <span class="pr-label">复发加重</span>
              <n-switch v-model:value="policy.client_policy.escalation" size="small" />
            </div>
            <div class="pr-row">
              <span class="pr-label">封禁时长</span>
              <n-input-number v-model:value="policy.client_policy.ban_hours" size="small" :min="1" :max="720" :show-button="false" style="width:80px" />
              <span class="pr-unit">小时</span>
            </div>
            <template v-if="policy.client_policy.escalation">
              <div class="pg-title" style="margin-top:10px">弹窗内容（支持 {client} {user_name} {ban_hours} 变量）</div>
              <div class="pr-row" v-for="m in msgTemplates" :key="m.key">
                <span class="pr-label">{{ m.label }}</span>
                <n-input v-model:value="policy.client_policy[m.key]" size="small" placeholder="留空用默认文案" style="flex:1" />
              </div>
            </template>
            <div v-else class="pr-row">
              <span class="pr-label">{{ currentActionLabel }} 弹窗内容</span>
              <n-input v-model:value="policy.client_policy[currentMsgKey]" size="small" placeholder="留空用默认文案" style="flex:1" />
            </div>
          </div>
          <div class="policy-group policy-concurrent">
            <div class="pg-title">并发管控</div>
            <div class="pr-row">
              <span class="pr-label">全局默认并发</span>
              <n-input-number v-model:value="policy.concurrent_policy.default_max" size="small" :min="1" :max="20" :show-button="false" style="width:80px" />
            </div>
            <div class="pr-row">
              <span class="pr-label">超限处理</span>
              <div class="pr-radio">
                <button v-for="a in concurrentActions" :key="a.value" class="rbtn" :class="{ active: policy.concurrent_policy.action === a.value }" @click="policy.concurrent_policy.action = a.value">{{ a.label }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 黑名单 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="link" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>客户端黑名单</span>
          </span>
        </div>
        <div class="bl-add">
          <n-input v-model:value="newItem" placeholder="客户端名称" size="small" @keyup.enter="addBl" />
          <n-button type="primary" size="small" :disabled="!newItem.trim()" @click="addBl">添加</n-button>
          <n-button size="small" quaternary @click="showHistory = true">历史客户端</n-button>
        </div>
        <n-empty v-if="blacklist.length === 0" description="空" />
        <div v-else class="bl-tags">
          <n-tag v-for="item in blacklist" :key="item" closable type="warning" size="small" @close="removeBl(item)">{{ item }}</n-tag>
        </div>
      </div>
    </template>

    <!-- ═══ 记录 ═══ -->
    <template v-if="activeTab === 'records'">
      <!-- 违规记录 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="check" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>违规记录</span>
          </span>
          <n-button text size="tiny" @click="loadViolations">刷新</n-button>
        </div>
        <n-empty v-if="violationItems.length === 0" description="暂无记录" />
        <div v-else class="vi-list">
          <div v-for="v in violationItems" :key="v.id" class="vi-item" :class="{ 'vi-locked': isLocked(v) }">
            <span class="vi-user" @click.stop="router.push(`/users/${v.user_id}`)">{{ v.user_name || v.user_id }}</span>
            <span class="vi-type">{{ v.violation_type === 'client_blocked' ? '客户端违规' : '并发超限' }}</span>
            <span class="vi-count">×{{ v.violation_count }}</span>
            <n-tag v-if="isLocked(v)" type="error" size="tiny">封禁中</n-tag>
            <span class="vi-time">{{ fmtTime(v.last_violation_at) }}</span>
            <n-button size="tiny" quaternary @click.stop="viDetail = v">详情</n-button>
          </div>
        </div>
      </div>

      <!-- 执法日志 -->
      <div class="section-card">
        <div class="section-head">
          <span class="section-title">
            <IosIcon name="tasks" :size="16" color="var(--brand)" :stroke-width="2" style="margin-right:4px" />
            <span>执法日志</span>
          </span>
        </div>
        <n-empty v-if="logs.length === 0" description="暂无记录" />
        <div v-else class="log-list">
          <div v-for="l in logs.slice(0, logShowAll ? 999 : 5)" :key="l.id" class="log-item">
            <div class="log-dot" :class="logDotClass(l.action)"></div>
            <div class="log-body">
              <div class="log-top">
                <n-tag :type="logType(l.action)" size="tiny">{{ logLabel(l.action) }}</n-tag>
                <span class="log-target">{{ l.target }}</span>
                <span class="log-time">{{ fmtTime(l.created_at) }}</span>
              </div>
              <span class="log-reason">{{ l.reason }}</span>
            </div>
          </div>
        </div>
        <div v-if="logs.length > 5" class="log-more" @click="logShowAll = !logShowAll">
          {{ logShowAll ? '收起' : `查看更多 (${logs.length - 5})` }}
        </div>
      </div>
    </template>

    <!-- 历史客户端抽屉 -->
    <div v-if="showHistory" class="vi-detail-overlay" @click="showHistory = false">
      <div class="vi-detail-drawer" @click.stop>
        <div class="vi-detail-head">
          <span>历史客户端</span>
          <n-button quaternary size="tiny" @click="showHistory = false">✕</n-button>
        </div>
        <div class="vi-detail-body">
          <div v-if="suggestions.length === 0" class="empty-sm">暂无记录</div>
          <div v-else class="bl-history-list">
            <div v-for="s in suggestions" :key="s" class="bl-history-item">
              <span class="bl-history-name">{{ s }}</span>
              <n-button v-if="!isBlacklisted(s)" size="tiny" type="warning" @click="addBlDirect(s)">拉黑</n-button>
              <n-tag v-else size="tiny" type="warning">已拉黑</n-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 违规详情抽屉 -->
    <div v-if="viDetail" class="vi-detail-overlay" @click="viDetail = null">
      <div class="vi-detail-drawer" @click.stop>
        <div class="vi-detail-head">
          <span>违规详情</span>
          <n-button quaternary size="tiny" @click="viDetail = null">✕</n-button>
        </div>
        <div class="vi-detail-body">
          <div class="vd-row"><span class="vd-label">用户</span><span class="vd-value vd-link" @click="router.push(`/users/${viDetail.user_id}`); viDetail = null">{{ viDetail.user_name || viDetail.user_id }}</span></div>
          <div class="vd-row"><span class="vd-label">客户端</span><span class="vd-value">{{ viDetail.client_name || '未知' }}</span></div>
          <div class="vd-row"><span class="vd-label">违规类型</span><span class="vd-value">{{ viDetail.violation_type === 'client_blocked' ? '客户端违规' : '并发超限' }}</span></div>
          <div class="vd-row"><span class="vd-label">违规次数</span><span class="vd-value vd-count">×{{ viDetail.violation_count }}</span></div>
          <div class="vd-row"><span class="vd-label">最近动作</span><span class="vd-value">{{ viDetail.last_action ? actionLabel(viDetail.last_action) : '无' }}</span></div>
          <div class="vd-row"><span class="vd-label">最后违规</span><span class="vd-value">{{ fmtTime(viDetail.last_violation_at) }}</span></div>
          <div v-if="viDetail.device_id" class="vd-row"><span class="vd-label">设备 ID</span><span class="vd-value vd-mono">{{ viDetail.device_id }}</span></div>
          <div v-if="viDetail.locked_until" class="vd-row"><span class="vd-label">封禁至</span><span class="vd-value vd-danger">{{ fmtTime(viDetail.locked_until) }}</span></div>
          <div v-if="isLocked(viDetail)" class="vd-row"><span class="vd-label">状态</span><n-tag type="error" size="small">封禁中</n-tag></div>
        </div>
        <div class="vi-detail-foot">
          <n-button v-if="isLocked(viDetail)" size="small" type="primary" :loading="unbanning" @click="doUnban(viDetail)">解封</n-button>
          <n-button size="small" type="error" quaternary @click="deleteViolation(viDetail.id); viDetail = null">清除记录</n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NTag, NInput, NEmpty, NSwitch, NInputNumber, useMessage } from 'naive-ui'
import PageHeader from '@/components/common/PageHeader.vue'
import IosIcon from '@/components/common/IosIcon.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import { riskApi } from '@/api/risk'
import type { RiskActionLog, ConcurrentItem, RiskPolicy, RiskViolation } from '@/api/risk'
import apiClient from '@/api/client'

const msg = useMessage()
const router = useRouter()

// ── Tab 导航 ──
type TabKey = 'overview' | 'policy' | 'records'
const activeTab = ref<TabKey>('overview')
const showDrawer = ref(false)
const tabs = [
  { key: 'overview' as const, label: '总览' },
  { key: 'policy' as const, label: '策略' },
  { key: 'records' as const, label: '记录' },
]

function handleTabClick(key: TabKey) {
  if (activeTab.value === key && key === 'overview') {
    showDrawer.value = !showDrawer.value
  } else {
    activeTab.value = key
    showDrawer.value = false
  }
}

const summary = ref<any>(null)
const blacklist = ref<string[]>([])
const scanning = ref(false)
const sweeping = ref(false)

// ── 实时播放 ──
const liveSessions = ref<any[]>([])
const sessionsLoading = ref(false)
const kicking = ref<string | null>(null)

// ── 并发状态 ──
const concurrent = ref<ConcurrentItem[]>([])
const concurrentLoading = ref(false)

// ── 风控事件 ──
const events = ref<any[]>([])
const evLoading = ref(false)
const evFilter = reactive({ status: 'open' })
const acting = ref<string | null>(null)

// ── 违规记录 ──
const violationItems = ref<RiskViolation[]>([])
const viDetail = ref<RiskViolation | null>(null)
const unbanning = ref(false)

// ── 执法日志 ──
const logs = ref<RiskActionLog[]>([])
const logShowAll = ref(false)

// ── 策略配置 ──
const policy = ref<RiskPolicy | null>(null)
const policyLoading = ref(false)
const newItem = ref('')
const showHistory = ref(false)
const suggestions = ref<string[]>([])
const clientActions = [
  { value: 'message', label: '弹窗' },
  { value: 'stop', label: '停止' },
  { value: 'force_kick', label: '强踢' },
  { value: 'ban', label: '封禁' },
]
const concurrentActions = [
  { value: 'warn', label: '仅告警' },
  { value: 'kick_newest', label: '踢最新' },
  { value: 'kick_all', label: '踢全部超限' },
]
const msgTemplates = [
  { key: 'msg_message', label: '弹窗' },
  { key: 'msg_stop', label: '停止' },
  { key: 'msg_force_kick', label: '强踢' },
  { key: 'msg_ban', label: '封禁' },
]
const currentActionLabel = computed(() => (msgTemplates.find(m => m.key === 'msg_' + policy.value?.client_policy?.action)?.label) || '')
const currentMsgKey = computed(() => 'msg_' + (policy.value?.client_policy?.action || ''))

// ── 数据加载 ──
async function loadSummary() { try { summary.value = (await riskApi.summary()).data } catch {} }
async function loadEvents() {
  evLoading.value = true
  try { const r = await riskApi.events(1, 50, evFilter.status || undefined); events.value = r.data?.items ?? [] }
  catch { events.value = [] }
  finally { evLoading.value = false }
}
async function loadBlacklist() { try { const r = await riskApi.blacklist(); blacklist.value = r.data ?? [] } catch { blacklist.value = [] } }
async function loadSuggestions() { try { const r = await riskApi.deviceClients(); suggestions.value = r.data ?? [] } catch { suggestions.value = [] } }
function isBlacklisted(name: string) { return blacklist.value.includes(name.toLowerCase()) }
async function addBlDirect(name: string) {
  if (isBlacklisted(name)) return
  try { const r = await riskApi.addBlacklist(name); blacklist.value = r.data ?? [...blacklist.value, name.toLowerCase()]; msg.success(`已添加 ${name}`) }
  catch { msg.error('失败') }
}
async function loadSessions() {
  sessionsLoading.value = true
  try { const r = await apiClient.get('/system/sessions'); liveSessions.value = (r.data?.data ?? []).filter((s: any) => s.NowPlayingItem) }
  catch { liveSessions.value = [] }
  finally { sessionsLoading.value = false }
}
async function loadConcurrent() {
  concurrentLoading.value = true
  try { const r = await riskApi.concurrentStatus(); concurrent.value = r.data ?? [] }
  catch { concurrent.value = [] }
  finally { concurrentLoading.value = false }
}
async function loadLogs() { try { const r = await riskApi.logs(1, 20); logs.value = r.data?.items ?? [] } catch { logs.value = [] } }
async function loadViolations() { try { const r = await riskApi.violations(undefined, 1, 50); violationItems.value = r.data?.items ?? [] } catch { violationItems.value = [] } }
async function deleteViolation(id: number) {
  try { await riskApi.deleteViolation(id); violationItems.value = violationItems.value.filter(v => v.id !== id); msg.success('已清除') }
  catch { msg.error('失败') }
}
async function doUnban(v: any) {
  unbanning.value = true
  try {
    await riskApi.unban(v.user_id)
    msg.success('已解封，违规记录已重置')
    viDetail.value = null
    await loadViolations()
  } catch { msg.error('解封失败') }
  finally { unbanning.value = false }
}
function isLocked(v: RiskViolation) { return v.locked_until && new Date(v.locked_until).getTime() > Date.now() }
function actionLabel(a: string) { return ({ message: '弹窗', stop: '停止', force_kick: '强踢', ban: '封禁' })[a] ?? a }

async function doKick(sessionId: string, deviceId: string, level: string) {
  kicking.value = level === 'hard' ? sessionId + 'h' : sessionId
  try {
    const r = await riskApi.kick(sessionId, deviceId, level)
    if (r.data?.success) { msg.success(level === 'hard' ? '已强制踢出' : '已停止播放'); await loadAll() }
    else { msg.error('失败') }
  } catch { msg.error('失败') }
  finally { kicking.value = null }
}

async function addBl() {
  const n = newItem.value.trim(); if (!n) return
  try { const r = await riskApi.addBlacklist(n); blacklist.value = r.data ?? [...blacklist.value, n.toLowerCase()]; newItem.value = ''; msg.success(`已添加 ${n}`) }
  catch { msg.error('失败') }
}
async function removeBl(n: string) {
  try { const r = await riskApi.removeBlacklist(n); blacklist.value = r.data ?? blacklist.value.filter(x => x !== n); msg.success(`已移除`) }
  catch { msg.error('失败') }
}
async function doAction(id: string, action: string) {
  acting.value = id
  try { await riskApi.action(id, action as any); msg.success(action === 'resolve' ? '已解决' : '已忽略'); await loadAll() }
  catch { msg.error('失败') }
  finally { acting.value = null }
}
async function handleScan() {
  scanning.value = true
  try { const r = await riskApi.scan(); const d = r.data; if (d) msg.success(`扫描: 拦截${d.blocked?.length||0} 越界${d.violations?.length||0}`); await loadAll() }
  catch { msg.error('失败') }
  finally { scanning.value = false }
}
async function handleSweep() {
  sweeping.value = true
  try { const r = await riskApi.sweep(); msg.success(r.data?.deleted_count ? `删除${r.data.deleted_count}个设备` : '无匹配'); await loadAll() }
  catch { msg.error('失败') }
  finally { sweeping.value = false }
}
async function loadPolicy() {
  try { const r = await riskApi.getPolicy(); policy.value = r.data ?? null } catch { policy.value = null }
}
async function savePolicy() {
  if (!policy.value) return
  policyLoading.value = true
  try {
    await riskApi.updatePolicy({ client_policy: policy.value.client_policy, concurrent_policy: policy.value.concurrent_policy })
    msg.success('策略已保存')
  } catch { msg.error('保存失败') }
  finally { policyLoading.value = false }
}
async function loadAll() { await Promise.all([loadSummary(), loadEvents(), loadBlacklist(), loadSessions(), loadLogs(), loadConcurrent(), loadPolicy(), loadViolations(), loadSuggestions()]) }

function svType(s: string) { return ({ high: 'error', medium: 'warning', low: 'info' })[s] as any ?? 'default' }
function svLabel(s: string) { return ({ high: '高危', medium: '中危', low: '低危' })[s] ?? s }
function sLabel(s: string) { return ({ '': '全部', open: '待处理', resolved: '已解决', ignored: '已忽略' })[s] ?? s }
function logType(a: string) { return ({ kick: 'error', ban: 'error', unban: 'success', device_sweep: 'warning' })[a] as any ?? 'default' }
function logLabel(a: string) { return ({ kick: '踢出', ban: '封禁', unban: '解封', device_sweep: '设备清除' })[a] ?? a }
function logDotClass(a: string) {
  return ({ kick: 'is-red', ban: 'is-red', unban: 'is-green', device_sweep: 'is-orange', sweep: 'is-orange' })[a] ?? 'is-gray'
}
function fmtTime(iso: string) {
  const d = new Date(iso), diff = Date.now() - d.getTime()
  // 未来时间显示绝对时间
  if (diff < 0) return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadAll)
</script>

<style scoped>
.ctrl-page { padding-bottom: 24px; }

.risk-tabs {
  display: flex;
  gap: 0;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 3px;
  margin-bottom: 1rem;
}
.risk-tab {
  flex: 1;
  text-align: center;
  padding: 0.5rem 0.25rem;
  border-radius: var(--radius);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.2s;
  cursor: pointer;
  font-family: inherit;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.risk-tab.active {
  background: var(--surface);
  color: var(--text);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.tab-chevron { transition: transform 0.25s; opacity: 0.4; }
.tab-chevron.open { transform: rotate(180deg); opacity: 0.8; }
.risk-tab.has-drawer .tab-chevron { opacity: 0.8; }

.action-drawer {
  margin-bottom: 12px;
  animation: slideDown 0.2s ease;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.drawer-actions {
  display: flex;
  gap: 8px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(245,247,250,0.92));
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}
.btn-content {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-icon { flex-shrink: 0; }

.overview-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-bottom: 1rem; }

/* ── KPI 卡片 ── */
.rkpi-card {
  display: flex; align-items: center; gap: 0.65rem;
  background: var(--surface); border-radius: 14px; padding: 0.85rem;
  border: 1px solid var(--border); cursor: default;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  opacity: 0; transform: translateY(12px);
  animation: rkpiIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}
.rkpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.rkpi-card.danger { border-color: rgba(255,59,48,0.2); }
@keyframes rkpiIn { to { opacity: 1; transform: translateY(0); } }
.rkpi-icon { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rkpi-red { background: linear-gradient(135deg, #FF3B30, #D70015); box-shadow: 0 3px 10px rgba(255,59,48,0.25); }
.rkpi-gray { background: linear-gradient(135deg, #8e8e93, #636366); }
.rkpi-green { background: linear-gradient(135deg, #34C759, #248A3D); box-shadow: 0 3px 10px rgba(52,199,89,0.25); }
.rkpi-purple { background: linear-gradient(135deg, #AF52DE, #8944AB); box-shadow: 0 3px 10px rgba(175,82,222,0.25); }
.rkpi-body { display: flex; flex-direction: column; }
.rkpi-val { font-size: 1.3rem; font-weight: 800; color: var(--text); line-height: 1.2; font-variant-numeric: tabular-nums; }
.rkpi-lbl { font-size: 0.68rem; color: var(--text-muted); margin-top: 1px; }
.section-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.95));
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 8px;
  flex-wrap: wrap;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}
.section-title {
  font-size: 14px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding-left: 2px;
}
.section-icon { color: var(--brand); flex-shrink: 0; }

.session-list { display: flex; flex-direction: column; gap: 8px; }
.session-card {
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(248,250,252,0.9), rgba(255,255,255,0.98));
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.session-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
  border-color: rgba(59, 130, 246, 0.16);
}
.sc-top { display: flex; align-items: center; justify-content: space-between; gap: 6px; margin-bottom: 4px; }
.sc-user-wrap { display: inline-flex; align-items: center; gap: 6px; min-width: 0; }
.user-icon { color: var(--text-muted); flex-shrink: 0; }
.sc-user { font-weight: 700; font-size: 13px; }
.sc-media { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sc-actions {
  display: flex;
  gap: 8px;
  padding-top: 2px;
}
:deep(.sc-actions .n-button) {
  border-radius: 999px;
  font-weight: 600;
}

.cc-list { display: flex; flex-direction: column; gap: 8px; }
.cc-card {
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(248,250,252,0.92), rgba(255,255,255,0.98));
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.cc-card.exceeded {
  border-color: rgba(220, 38, 38, 0.12);
  border-left: 3px solid var(--danger);
  background: linear-gradient(90deg, rgba(255,59,48,0.08), rgba(255,255,255,0.98) 28%);
}
.cc-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.cc-name { font-weight: 800; font-size: 14px; }
.cc-sess { font-size: 12px; color: var(--text-muted); padding: 3px 0; display: flex; gap: 6px; }
.cc-client { color: var(--brand); font-weight: 600; white-space: nowrap; }
.cc-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.filter-pills { display: flex; gap: 4px; }
.pill { border: none; background: var(--bg); color: var(--text-muted); font-size: 12px; padding: 4px 10px; border-radius: 20px; cursor: pointer; font-family: inherit; }
.pill.active { background: var(--brand); color: #fff; }

.ev-list { display: flex; flex-direction: column; gap: 8px; }
.ev-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(180deg, rgba(248,250,252,0.9), rgba(255,255,255,0.98));
}
.ev-item.ev-high.ev-open {
  border-color: rgba(208,48,80,0.12);
  border-left: 3px solid var(--danger);
  background: linear-gradient(90deg, rgba(208,48,80,0.08), rgba(255,255,255,0.98) 26%);
}
.ev-item.ev-open:not(.ev-high) { border-color: rgba(245, 158, 11, 0.18); }
.ev-main { flex: 1; min-width: 0; }
.ev-title { font-size: 13px; font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.ev-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.ev-time { font-size: 11px; color: var(--text-muted); }
.ev-acts { display: flex; gap: 4px; flex-direction: column; flex-shrink: 0; }
.ev-status { flex-shrink: 0; }
.sev-tag-inner { display: inline-flex; align-items: center; gap: 5px; }
.sev-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.sev-high { background: #ef4444; }
.sev-medium { background: #f59e0b; }
.sev-low { background: #3b82f6; }

.policy-grid { display: grid; gap: 12px; }
.policy-group {
  background: linear-gradient(180deg, rgba(248,250,252,0.88), rgba(255,255,255,0.98));
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-left: 3px solid var(--brand);
}
.policy-client { border-left-color: #3b82f6; }
.policy-concurrent { border-left-color: #8b5cf6; }
.pg-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; }
.pr-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid rgba(15, 23, 42, 0.06); gap: 8px; }
.pr-row:last-child { border-bottom: none; }
.pr-label { font-size: 13px; flex-shrink: 0; }
.pr-unit { font-size: 12px; color: var(--text-muted); margin-left: 4px; }
.pr-radio { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.rbtn {
  padding: 5px 12px;
  border-radius: 10px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255,255,255,0.92);
  font-size: 12px;
  cursor: pointer;
  color: var(--text);
  transition: all 0.18s ease;
  font-weight: 600;
}
.rbtn.active { background: var(--brand); color: white; border-color: var(--brand);  }
.rbtn:hover:not(.active) { border-color: var(--brand); background: rgba(59, 130, 246, 0.06); transform: translateY(-1px); }

.bl-add { display: flex; gap: 8px; margin-bottom: 10px; }
.bl-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.bl-suggest { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.bl-suggest-label { font-size: 12px; color: var(--text-muted); }
.bl-suggest-btn { padding: 3px 8px; border-radius: 8px; border: 1px dashed var(--border); background: var(--bg); font-size: 12px; cursor: pointer; color: var(--text); transition: all 0.15s; }
.bl-suggest-btn:hover:not(.disabled) { border-color: var(--brand); border-style: solid; color: var(--brand); }
.bl-suggest-btn.disabled { opacity: 0.4; cursor: default; text-decoration: line-through; }

/* 历史客户端 */
.bl-history-list { display: flex; flex-direction: column; gap: 4px; }
.bl-history-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border); }
.bl-history-name { font-size: 13px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-sm { text-align: center; padding: 2rem 1rem; color: var(--text-muted); font-size: 13px; }

.log-list {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 16px;
}
.log-list::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: linear-gradient(180deg, rgba(148,163,184,0.45), rgba(148,163,184,0.12));
  border-radius: 999px;
}
.log-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0 8px 4px;
}
.log-more {
  text-align: center; padding: 10px; color: var(--brand);
  font-size: 0.8rem; font-weight: 600; cursor: pointer;
  border-radius: 8px; transition: background 0.15s;
}
.log-more:active { background: rgba(0,122,255,0.06); }
.log-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  position: relative;
  z-index: 1;
  margin-top: 6px;
  margin-left: -19px;
  border: 2px solid rgba(255,255,255,0.95);
  box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
  background: #94a3b8;
  flex-shrink: 0;
}
.log-dot.is-red { background: #ef4444; }
.log-dot.is-green { background: #22c55e; }
.log-dot.is-orange { background: #f59e0b; }
.log-dot.is-gray { background: #94a3b8; }
.log-body {
  flex: 1;
  min-width: 0;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(248,250,252,0.75);
  border-radius: 12px;
  padding: 10px 12px;
}
.log-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.log-target { font-weight: 700; }
.log-reason { color: var(--text-muted); display: block; font-size: 12px; line-height: 1.5; }
.log-time { color: var(--text-muted); white-space: nowrap; font-size: 11px; margin-left: auto; }

.vi-list { display: flex; flex-direction: column; gap: 8px; }
.vi-item {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-radius: 12px;
  background: var(--surface); border: 1px solid var(--border);
  transition: border-color 0.2s; font-size: 13px;
}
.vi-item.vi-locked { border-left: 3px solid var(--danger); }
.vi-type { font-size: 11px; padding: 1px 6px; border-radius: 999px; background: var(--border); color: var(--text-muted); white-space: nowrap; }
.vi-count { font-weight: 700; color: var(--warning); white-space: nowrap; }
.vi-user { color: var(--brand); cursor: pointer; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100px; flex-shrink: 0; }
.vi-user:hover { text-decoration: underline; }
.vi-time { margin-left: auto; font-size: 11px; color: var(--text-muted); white-space: nowrap; }

/* 违规详情抽屉 */
.vi-detail-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 3000; display: flex; justify-content: flex-end; }
.vi-detail-drawer { width: min(340px, 85vw); height: 100%; background: var(--bg); display: flex; flex-direction: column; animation: slideInRight 0.25s ease; }
@keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
.vi-detail-head { display: flex; justify-content: space-between; align-items: center; padding: 16px; font-size: 16px; font-weight: 700; border-bottom: 1px solid var(--border); }
.vi-detail-body { flex: 1; overflow-y: auto; padding: 16px; }
.vd-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); }
.vd-row:last-child { border-bottom: none; }
.vd-label { font-size: 12px; color: var(--text-muted); }
.vd-value { font-size: 13px; font-weight: 600; text-align: right; max-width: 60%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vd-link { color: var(--brand); cursor: pointer; }
.vd-link:hover { text-decoration: underline; }
.vd-count { color: var(--warning); }
.vd-mono { font-family: monospace; font-size: 11px; }
.vd-danger { color: var(--danger); }
.vi-detail-foot { padding: 12px 16px; border-top: 1px solid var(--border); }

@media (min-width: 769px) {
  .overview-row { grid-template-columns: repeat(4, 1fr); }
  .rkpi-card { padding: 1rem; }
  .ev-item { flex-direction: row; }
  .ev-acts { flex-direction: row; }
  .policy-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
