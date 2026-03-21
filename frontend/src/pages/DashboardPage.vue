<template>
  <div class="dashboard-page">
    <PageHeader title="Dashboard" desc="Overview of your Emby Next system" />
    
    <div v-if="loading" class="loading-container">
      <LoadingState />
    </div>
    
    <div v-else-if="error" class="error-container">
      <ErrorState :message="error" />
      <button class="btn btn-ghost" @click="fetchData">Retry</button>
    </div>
    
    <div v-else class="dashboard-content">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <StatCard
          v-for="stat in stats"
          :key="stat.title"
          :title="stat.title"
          :value="stat.value"
          :change="stat.change"
          :icon="stat.icon"
          :trend="stat.trend"
        />
      </div>
      
      <!-- Charts -->
      <div class="charts-grid">
        <div class="chart-card">
          <h3 class="chart-title">Activity Trend</h3>
          <TrendChart :x-data="trendData.xData" :series="trendData.series" height="300px" />
        </div>
        
        <div class="chart-card">
          <h3 class="chart-title">Top Media</h3>
          <div class="top-media-list">
            <div v-for="media in topMedia" :key="media.id" class="media-item">
              <div class="media-info">
                <div class="media-title">{{ media.title }}</div>
                <div class="media-meta">{{ media.type }} • {{ media.plays }} plays</div>
              </div>
              <div class="media-users">{{ media.users }} users</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Sessions & Risk -->
      <div class="sections-grid">
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">Active Sessions</h3>
            <router-link to="/sessions" class="btn btn-ghost btn-sm">View all</router-link>
          </div>
          <div class="sessions-list">
            <div v-for="session in activeSessions" :key="session.id" class="session-item">
              <div class="session-user">
                <div class="avatar">{{ session.user?.charAt(0) || 'U' }}</div>
                <div class="session-info">
                  <div class="session-name">{{ session.user || 'Unknown' }}</div>
                  <div class="session-device">{{ session.device || 'Unknown device' }}</div>
                </div>
              </div>
              <div class="session-time">{{ formatDuration(session.duration) }}</div>
            </div>
            <div v-if="activeSessions.length === 0" class="empty-sessions">
              No active sessions
            </div>
          </div>
        </div>
        
        <div class="section-card">
          <div class="section-header">
            <h3 class="section-title">Recent Risk Events</h3>
            <router-link to="/risk" class="btn btn-ghost btn-sm">View all</router-link>
          </div>
          <div class="risk-list">
            <div v-for="event in recentRiskEvents" :key="event.id" class="risk-item">
              <span :class="`tag tag-${getSeverityColor(event.severity)}`">
                {{ event.severity }}
              </span>
              <div class="risk-info">
                <div class="risk-title">{{ event.title }}</div>
                <div class="risk-time">{{ formatTime(event.created_at) }}</div>
              </div>
            </div>
            <div v-if="recentRiskEvents.length === 0" class="empty-risk">
              No recent risk events
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { fetchDashboardData } from '@/api/dashboard'

interface StatItem {
  title: string
  value: string | number
  change?: string
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
}

interface TrendData {
  xData: string[]
  series: Array<{ name: string; data: number[]; color?: string }>
}

interface MediaItem {
  id: string
  title: string
  type: string
  plays: number
  users: number
}

interface Session {
  id: string
  user?: string
  device?: string
  duration: number
}

interface RiskEvent {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  created_at: string
}

const loading = ref(true)
const error = ref('')
const stats = ref<StatItem[]>([])
const trendData = ref<TrendData>({ xData: [], series: [] })
const topMedia = ref<MediaItem[]>([])
const activeSessions = ref<Session[]>([])
const recentRiskEvents = ref<RiskEvent[]>([])

const fetchData = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const data = await fetchDashboardData()
    
    // Mock data for demonstration
    stats.value = [
      { title: 'Total Users', value: data.total_users || 1254, change: '+12%', trend: 'up' },
      { title: 'Active Sessions', value: data.active_sessions || 42, change: '+5%', trend: 'up' },
      { title: 'Media Plays', value: data.media_plays || '12.5k', change: '+8%', trend: 'up' },
      { title: 'Risk Events', value: data.risk_events || 8, change: '-3%', trend: 'down' }
    ]
    
    trendData.value = {
      xData: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      series: [
        { name: 'Plays', data: [120, 200, 150, 180, 190, 230, 260], color: 'var(--brand)' },
        { name: 'Users', data: [80, 100, 120, 110, 130, 150, 180], color: 'var(--success)' }
      ]
    }
    
    topMedia.value = [
      { id: '1', title: 'The Matrix', type: 'Movie', plays: 1250, users: 450 },
      { id: '2', title: 'Breaking Bad', type: 'TV Show', plays: 980, users: 320 },
      { id: '3', title: 'Inception', type: 'Movie', plays: 850, users: 280 },
      { id: '4', title: 'Stranger Things', type: 'TV Show', plays: 720, users: 240 },
      { id: '5', title: 'Interstellar', type: 'Movie', plays: 650, users: 210 }
    ]
    
    activeSessions.value = [
      { id: '1', user: 'John Doe', device: 'Chrome on Windows', duration: 3600 },
      { id: '2', user: 'Jane Smith', device: 'Safari on iPhone', duration: 1800 },
      { id: '3', user: 'Bob Johnson', device: 'Android TV', duration: 7200 },
      { id: '4', user: 'Alice Brown', device: 'Fire TV', duration: 5400 }
    ]
    
    recentRiskEvents.value = [
      { id: '1', title: 'Failed login attempt', severity: 'medium', created_at: new Date(Date.now() - 3600000).toISOString() },
      { id: '2', title: 'Unusual bandwidth usage', severity: 'high', created_at: new Date(Date.now() - 7200000).toISOString() },
      { id: '3', title: 'Multiple device connections', severity: 'low', created_at: new Date(Date.now() - 10800000).toISOString() }
    ]
  } catch (err: any) {
    error.value = err.message || 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'red'
    case 'high': return 'red'
    case 'medium': return 'yellow'
    case 'low': return 'blue'
    case 'info': return 'gray'
    default: return 'gray'
  }
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

const formatTime = (date: string) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.dashboard-page {
  padding-bottom: 2rem;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.chart-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 1rem 0;
}

.top-media-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.media-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.media-info {
  flex: 1;
}

.media-title {
  font-weight: 500;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.media-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.media-users {
  font-weight: 600;
  color: var(--brand);
  font-size: 0.875rem;
}

.sections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.sessions-list,
.risk-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.session-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--brand);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.session-info {
  display: flex;
  flex-direction: column;
}

.session-name {
  font-weight: 500;
  color: var(--text);
  font-size: 0.875rem;
}

.session-device {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.session-time {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.risk-info {
  flex: 1;
}

.risk-title {
  font-weight: 500;
  color: var(--text);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.risk-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.empty-sessions,
.empty-risk {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-style: italic;
}

.tag {
  font-size: 10px;
  padding: 1px 4px;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .sections-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>