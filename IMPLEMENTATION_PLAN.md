# Emby Next Console — 实施计划 v2.2

> 基于 DESIGN_V2.md 的具体落地计划，逐文件列出新增/修改

---

## 现有文件清单

### 后端 (backend/app/)
```
core/       emby.py, emby_data.py, emby_db.py, event_bus.py, risk_monitor.py, security.py, middleware.py
db/models/  user.py, playback.py, risk.py, notification.py, system.py, webhook.py
modules/    auth, dashboard, users, stats, risk, notifications, webhook, system
tasks/      worker.py
```

### 前端 (frontend/src/)
```
pages/      Dashboard, Login, Users, UserDetail, Stats, Risk, Notifications, Settings
api/        auth, dashboard, users, stats, risk, notifications, system
stores/     auth, notifications, ui
components/ common/*, charts/*, users/*, risk/*, notifications/*
layouts/    DefaultLayout, AuthLayout
```

---

## Phase 1: 用户管理增强

### 1.1 新增数据库模型

**新建 `backend/app/db/models/invite.py`**
```python
class InviteCode(Model):
    code: str                    # 邀请码(唯一)
    template_emby_user_id: str | None   # 权限继承源(Emby User ID)
    permission_template_id: int | None  # 或使用权限模板(FK)
    max_uses: int                # 最大使用次数
    used_count: int              # 已使用次数
    expires_at: datetime | None
    concurrent_limit: int | None
    created_by: int              # FK -> users.id
    status: str                  # active/used/expired/disabled
    created_at: datetime

class InviteUsage(Model):
    invite_id: int               # FK -> invite_codes.id
    emby_user_id: str
    used_at: datetime

class PermissionTemplate(Model):
    name: str
    description: str | None
    library_access: list[str]    # PostgreSQL ARRAY
    policy_json: dict            # JSONB
    configuration_json: dict     # JSONB
    is_default: bool
    created_at: datetime
    updated_at: datetime

class UserOverride(Model):
    emby_user_id: str            # 唯一
    concurrent_limit: int | None
    max_bitrate: int | None
    allow_transcode: bool | None
    client_blacklist: list[str] | None
    note: str | None
    expires_at: datetime | None
    updated_at: datetime
```

**修改 `backend/app/db/models/__init__.py`**
```python
from app.db.models.invite import InviteCode, InviteUsage, PermissionTemplate, UserOverride  # noqa: F401
```

### 1.2 后端新增/修改文件

**新建 `backend/app/modules/invites/__init__.py`** — 空
**新建 `backend/app/modules/invites/api.py`** — 邀请码 API
```
POST   /admin/invites              生成邀请码
GET    /admin/invites              邀请码列表
GET    /admin/invites/:code        邀请码详情
DELETE /admin/invites/:code        禁用邀请码
GET    /admin/invites/stats        统计(总发出/已使用/过期)
GET    /register?code=XXX          验证邀请码有效性(公开API)
```

**新建 `backend/app/modules/invites/service.py`** — 邀请码业务逻辑
```
- generate_invite()    生成邀请码，设置过期/次数限制
- use_invite()         用户注册时消耗邀请码，继承模板权限
- validate_invite()    验证邀请码是否有效
- list_invites()       分页列表
- get_stats()          统计
```

**新建 `backend/app/modules/invites/schemas.py`** — 请求/响应模型

**新建 `backend/app/modules/templates/__init__.py`** — 空
**新建 `backend/app/modules/templates/api.py`** — 权限模板 API
```
POST   /admin/templates           创建模板
GET    /admin/templates           模板列表
GET    /admin/templates/:id       模板详情
PUT    /admin/templates/:id       更新模板
DELETE /admin/templates/:id       删除模板
POST   /admin/templates/:id/apply  应用模板到用户
```

**新建 `backend/app/modules/templates/service.py`**

**修改 `backend/app/modules/users/api.py`** — 新增用户详情增强端点
```
GET    /admin/users/:id/permissions    用户库权限详情(从Emby拉取)
PUT    /admin/users/:id/permissions    更新用户库权限(写入Emby)
GET    /admin/users/:id/override       用户级覆盖配置
PUT    /admin/users/:id/override       更新用户级覆盖配置
POST   /admin/users/:id/force-logout   强制下线
POST   /admin/users/create             手动创建用户
```

**修改 `backend/app/modules/users/service.py`** — 新增用户创建/权限操作
```
- create_user()         手动创建 Emby 用户 + 本地记录
- get_user_permissions() 从 Emby API 拉取用户库权限+策略
- update_user_permissions() 写入 Emby API 更新权限
- force_logout()        强制踢出用户会话
- get_user_override()   获取用户级覆盖配置
- upsert_user_override() 更新覆盖配置
```

**修改 `backend/app/modules/auth/api.py`** — 注册流程支持邀请码
```
POST   /auth/register?code=XXX   注册时自动继承邀请码模板权限
```

**新建 `backend/app/core/emby_users.py`** — Emby 用户操作封装
```
- create_emby_user()        POST /emby/Users/New
- get_user_policy()         GET /emby/Users/:id/Policy
- update_user_policy()      POST /emby/Users/:id/Policy
- get_user_configuration()  GET /emby/Users/:id/Configuration
- update_user_configuration() POST /emby/Users/:id/Configuration
- delete_emby_user()        DELETE /emby/Users/:id
- get_user_sessions()       GET /emby/Sessions?UserId=:id
- force_logout_session()    POST /emby/Sessions/Logout
```

### 1.3 前端新增/修改文件

**新建 `frontend/src/api/invites.ts`** — 邀请码 API 客户端
**新建 `frontend/src/api/templates.ts`** — 权限模板 API 客户端

**新建 `frontend/src/pages/InvitesPage.vue`** — 邀请管理页面
```
- 邀请码列表(状态筛选)
- 创建邀请码表单(有效期/数量/权限模板选择/并发限制)
- 邀请链接复制
- 使用统计卡片
```

**新建 `frontend/src/pages/CreateInvitePage.vue`** — 创建邀请码
**新建 `frontend/src/pages/TemplatesPage.vue`** — 权限模板管理
**新建 `frontend/src/pages/TemplateDetailPage.vue`** — 模板编辑

**修改 `frontend/src/pages/UserDetailPage.vue`** — 增加 Tab
```
现有: 基础信息
新增: 库权限 Tab、高级策略 Tab、观看数据 Tab、操作区
```

**新建 `frontend/src/components/users/PermissionEditor.vue`** — 库权限编辑器
**新建 `frontend/src/components/users/OverrideEditor.vue`** — 用户级覆盖配置
**新建 `frontend/src/components/users/CreateUserForm.vue`** — 手动创建用户表单

**修改 `frontend/src/router/index.ts`** — 新增路由
```
/admin/users/invites
/admin/users/invites/create
/admin/users/templates
/admin/users/templates/:id
```

**修改 `frontend/src/components/common/AppSidebar.vue`** — 用户管理子菜单
**修改 `frontend/src/components/common/TabBar.vue`** — 更多面板增加入口

### 1.4 Alembic 迁移

**新建 `backend/alembic/versions/0002_invite_templates.py`**
```python
def upgrade():
    op.create_table('invite_codes', ...)
    op.create_table('invite_usages', ...)
    op.create_table('permission_templates', ...)
    op.create_table('user_overrides', ...)
```

---

## Phase 2: 用户门户骨架（独立前端 App）

### 2.1 前端目录结构调整

```
frontend/
├── src/
│   ├── admin/           ← 现有代码搬到这里(管理后台)
│   │   ├── pages/
│   │   ├── api/
│   │   ├── stores/
│   │   └── components/
│   ├── portal/          ← 新增(用户门户)
│   │   ├── pages/
│   │   │   ├── HomePage.vue
│   │   │   ├── ProfilePage.vue
│   │   │   ├── PasswordPage.vue
│   │   │   ├── MyStatsPage.vue
│   │   │   ├── MyCalendarPage.vue
│   │   │   ├── MyTicketsPage.vue
│   │   │   ├── MyPointsPage.vue
│   │   │   └── LoginPage.vue
│   │   ├── api/
│   │   │   ├── portal.ts
│   │   │   ├── profile.ts
│   │   │   └── points.ts
│   │   ├── stores/
│   │   │   └── portal-auth.ts
│   │   ├── components/
│   │   │   ├── PortalTabBar.vue
│   │   │   └── ...
│   │   └── router/
│   │       └── index.ts
│   └── shared/          ← 两个App共用的组件
│       ├── components/
│       │   ├── LoadingState.vue
│       │   ├── EmptyState.vue
│       │   └── ...
│       ├── styles/
│       └── utils/
```

**构建配置变更 `frontend/vite.config.ts`：**
```typescript
// 两个入口点: admin 和 portal
build: {
  rollupOptions: {
    input: {
      admin: resolve(__dirname, 'admin.html'),
      portal: resolve(__dirname, 'portal.html'),
    }
  }
}
```

**新建 `frontend/admin.html`** — 管理后台入口
**新建 `frontend/portal.html`** — 用户门户入口

### 2.2 后端认证扩展

**修改 `backend/app/modules/auth/api.py`**
```
POST /auth/portal/login     Emby 账号登录(用户名+密码)
  → 验证: 调用 Emby API POST /emby/Users/AuthenticateByName
  → 成功: 签发 portal JWT (role=portal_user, 含 emby_user_id)
  → 返回: token + 用户基本信息
```

**修改 `backend/app/core/security.py`**
```
- create_portal_token()  创建门户 JWT(含 emby_user_id)
- 验证中间件区分 admin 和 portal 角色
```

**修改 `backend/app/core/middleware.py`**
```
- 权限中间件: admin 路由要求 role=admin
- 权限中间件: portal 路由要求登录(任意角色)
```

### 2.3 后端 Portal API

**新建 `backend/app/modules/portal/__init__.py`**
**新建 `backend/app/modules/portal/api.py`**
```
GET  /portal/profile              我的资料
PUT  /portal/profile/password     修改密码(→Emby同步)
GET  /portal/profile/devices      我的设备列表
POST /portal/profile/devices/:id/logout  远程登出设备
GET  /portal/stats/me             我的观影统计
GET  /portal/home                 门户首页数据
```

**新建 `backend/app/modules/portal/service.py`**
```
- get_my_profile()        从 Emby API + 本地数据组合
- change_password()       验证旧密码 → 调用 Emby API 更新
- get_my_devices()        从 Emby Sessions 拉取
- logout_device()         踢出指定会话
- get_home_data()         继续观看 + 最新入库 + 公告
```

### 2.4 前端 Portal 页面

**`portal/pages/HomePage.vue`**
- 继续观看卡片(Emby API 最近播放)
- 最新入库(Emby API 最近添加)
- 个人数据卡片(本月时长/签到/积分)

**`portal/pages/ProfilePage.vue`**
- 头像(从 Emby 同步)
- 用户名(只读)、显示名
- 账号到期时间、VIP 状态
- 通知偏好入口

**`portal/pages/PasswordPage.vue`**
- 旧密码 + 新密码 + 确认密码
- 调用 PUT /portal/profile/password

---

## Phase 3: Analytics 重构

### 3.1 后端修改

**修改 `backend/app/modules/stats/api.py`** — 新增端点
```
GET /admin/analytics/watch-history       观看历史(支持 user_id 筛选)
GET /admin/analytics/clock-24h           24H 生物钟热力图数据
GET /admin/analytics/device-dist         设备分布
GET /admin/analytics/genre-preference    类型偏好
GET /admin/analytics/hot-rank            热度排行
GET /admin/analytics/duration-rank       时长排行
GET /admin/analytics/user-rank           用户排行
GET /admin/analytics/quality             质量分析
```

**修改 `backend/app/modules/stats/service.py`** — 对应业务逻辑

### 3.2 前端修改

**修改 `frontend/src/pages/StatsPage.vue`** — 重构为 Tab 布局
```
Tab 1: 用户数据
  - 观看历史列表(用户筛选)
  - 24H 生物钟热力图(用 canvas 绘制)
  - 观影频率柱状图
  - 类型偏好雷达图
  - 设备/软件分布饼图

Tab 2: 媒体排行
  - 热度排行 Top N
  - 时长排行 Top N
  - 用户播放量排行
  - 多维度筛选栏

Tab 3: 质量分析
  - 分辨率分布
  - 编码分布
  - 码率分布
  - 文件大小排行
```

**新建 `frontend/src/components/charts/HeatmapChart.vue`** — 24H 热力图
**新建 `frontend/src/components/charts/RadarChart.vue`** — 类型偏好雷达图
**新建 `frontend/src/components/charts/PieChart.vue`** — 设备分布饼图
**新建 `frontend/src/components/charts/RankList.vue`** — 排行榜组件(带进度条)

**修改 `frontend/src/api/stats.ts`** — 新增 API 客户端

---

## Phase 4: 媒体管理

### 4.1 后端新增

**新建 `backend/app/core/tmdb.py`** — TMDB 客户端
```python
import httpx

class TMDBClient:
    BASE = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search_movie(query, page=1)
    async def search_tv(query, page=1)
    async def get_movie(tmdb_id)
    async def get_tv(tmdb_id)
    async def get_tv_season(tmdb_id, season_number)
    async def upcoming_movies(page=1)
    async def on_the_air(page=1)
    def poster_url(path, size="w300")
    def backdrop_url(path, size="w780")
```

**新建 `backend/app/modules/media/__init__.py`**
**新建 `backend/app/modules/media/api.py`**
```
GET  /admin/media/library              媒体库列表(从 Emby 同步)
GET  /admin/media/missing              缺集列表
POST /admin/media/missing/scan         触发缺集扫描
GET  /admin/media/duplicates           去重列表
POST /admin/media/duplicates/scan      触发去重扫描
GET  /admin/media/strategies           去重策略列表
POST /admin/media/strategies           创建去重策略
GET  /admin/media/search?query=xxx     搜索(Emby+TMDB)
```

**新建 `backend/app/modules/media/service.py`**
```
- sync_library()           同步 Emby 库到本地 MediaItem 表
- detect_missing_episodes() 缺集检测(Emby 库 vs TMDB)
- find_duplicates()        去重分析(TMDB 分组+质量评分)
- search_media()           统一搜索
```

**新建 `backend/app/db/models/media.py`**
```python
class MediaItem(Model):
    emby_item_id: str, tmdb_id: int|None, title: str, media_type: str
    resolution: str, codec: str, bitrate: int, file_size: int
    quality_score: float, is_duplicate: bool, duplicate_group: str|None
    last_scanned: datetime

class MissingEpisode(Model):
    series_id: str, series_name: str, season: int, episode: int
    tmdb_title: str, scanned_at: datetime

class DedupStrategy(Model):
    name: str, keep_rule: str, auto_delete: bool, is_active: bool
```

### 4.2 前端新增

**新建 `frontend/src/pages/MediaPage.vue`** — 媒体库浏览
**新建 `frontend/src/pages/MissingEpisodesPage.vue`** — 缺集管理
**新建 `frontend/src/pages/DuplicatesPage.vue`** — 去重管理

**新建 `frontend/src/api/media.ts`**

**修改 `frontend/src/router/index.ts`**
```
/admin/media
/admin/media/missing
/admin/media/duplicates
```

---

## Phase 5: 社区功能

### 5.1 追剧日历

**新建 `backend/app/modules/calendar/`** — api.py, service.py, schemas.py
**新建 `backend/app/db/models/calendar.py`** — CalendarEntry, ContentSubscription

**新建 `frontend/src/pages/CalendarPage.vue`** — 月视图日历
**新建 `frontend/src/components/calendar/CalendarGrid.vue`** — 日历网格
**新建 `frontend/src/components/calendar/DayDetail.vue`** — 日期详情弹窗

### 5.2 工单系统

**新建 `backend/app/modules/tickets/`** — api.py, service.py, schemas.py
**新建 `backend/app/db/models/ticket.py`** — Ticket, TicketComment

**新建 `frontend/src/pages/TicketsPage.vue`** — 工单列表
**新建 `frontend/src/pages/TicketDetailPage.vue`** — 工单详情+评论

### 5.3 积分系统

**新建 `backend/app/modules/points/`** — api.py, service.py, schemas.py
**新建 `backend/app/db/models/points.py`** — PointsAccount, PointsTransaction, DailyCheckin

**新建 `frontend/src/pages/PointsPage.vue`** — 积分中心

---

## Phase 6: 通知系统重构

### 6.1 后端重构

**修改 `backend/app/modules/notifications/`** — 大幅重写

新增端点:
```
# 通道管理
POST   /admin/notifications/channels
GET    /admin/notifications/channels
PUT    /admin/notifications/channels/:id
DELETE /admin/notifications/channels/:id
POST   /admin/notifications/channels/:id/test

# 模板管理
POST   /admin/notifications/templates
GET    /admin/notifications/templates
PUT    /admin/notifications/templates/:id
DELETE /admin/notifications/templates/:id

# 场景矩阵
POST   /admin/notifications/rules
GET    /admin/notifications/rules
PUT    /admin/notifications/rules/:id
DELETE /admin/notifications/rules/:id

# 发送记录
GET    /admin/notifications/logs

# 用户偏好
GET    /portal/notifications/prefs
PUT    /portal/notifications/prefs

# 用户订阅
POST   /portal/subscriptions
GET    /portal/subscriptions
DELETE /portal/subscriptions/:id

# 用户模板
GET    /portal/notifications/templates
POST   /portal/notifications/templates
DELETE /portal/notifications/templates/:id
```

**修改 `backend/app/modules/webhook/service.py`** — 新增 library.new 处理
```python
async def _handle_library_new(self, payload):
    # 解析新入库内容
    # 查 ContentSubscription 匹配
    # 触发用户通知
```

**新建 `backend/app/db/models/notification.py`** — 扩展
```python
class NotificationChannel(Model)   # 通道配置
class NotificationTemplate(Model)  # 消息模板
class NotificationRule(Model)      # 场景矩阵
class UserNotificationPref(Model)  # 用户偏好
class ContentSubscription(Model)   # 内容订阅
class NotificationLog(Model)       # 发送记录
```

### 6.2 前端重构

**重写 `frontend/src/pages/NotificationsPage.vue`** — 改为 Tab 布局
```
Tab 1: 通知列表(现有功能保留)
Tab 2: 通道配置
Tab 3: 模板编辑
Tab 4: 场景矩阵
Tab 5: 发送记录
```

**新建 `frontend/src/components/notifications/ChannelConfig.vue`** — 通道配置卡片
**新建 `frontend/src/components/notifications/TemplateEditor.vue`** — 模板编辑器
**新建 `frontend/src/components/notifications/RuleMatrix.vue`** — 场景矩阵

**新建 `frontend/src/pages/SubscriptionsPage.vue`** — 用户订阅管理(门户)

---

## Phase 7: 高级功能

### 7.1 任务中心

**新建 `backend/app/modules/tasks/`** — api.py, service.py
**扩展 `backend/app/tasks/worker.py`** — ARQ 队列
**新建 `frontend/src/pages/TasksPage.vue`**

### 7.2 海报工坊

**新建 `backend/app/modules/poster/`**
**新建 `backend/app/db/models/poster.py`** — PosterTemplate, GeneratedPoster
**新建 `frontend/src/pages/PosterPage.vue`**

### 7.3 系统设置完善

**修改 `backend/app/modules/system/`** — 扩展设置项
**修改 `frontend/src/pages/SettingsPage.vue`** — 增加权限模板管理入口

---

## 全局文件变更汇总

### 新增文件 (后端) — 约 35 个
```
backend/app/
├── core/tmdb.py
├── core/emby_users.py
├── db/models/invite.py
├── db/models/media.py
├── db/models/calendar.py
├── db/models/ticket.py
├── db/models/points.py
├── db/models/poster.py
├── modules/invites/  (3 files)
├── modules/templates/ (3 files)
├── modules/portal/   (3 files)
├── modules/media/    (3 files)
├── modules/calendar/ (3 files)
├── modules/tickets/  (3 files)
├── modules/points/   (3 files)
├── modules/poster/   (3 files)
└── modules/tasks/    (2 files)
```

### 修改文件 (后端) — 约 10 个
```
backend/app/
├── db/models/__init__.py           加 import
├── db/models/notification.py       大幅扩展
├── modules/auth/api.py             portal 登录
├── modules/users/api.py            增强端点
├── modules/users/service.py        增强逻辑
├── modules/stats/api.py            新端点
├── modules/stats/service.py        新逻辑
├── modules/notifications/*          大幅重写
├── modules/webhook/service.py      library.new 处理
├── modules/system/api.py           扩展
├── core/security.py                portal token
└── main.py                         新模块注册
```

### 新增文件 (前端) — 约 30 个
```
frontend/src/
├── admin/ (现有文件搬入)
├── portal/
│   ├── pages/ (7 pages)
│   ├── api/ (3 files)
│   ├── stores/ (1 file)
│   └── components/ (5+ files)
├── shared/ (共用组件搬入)
├── pages/InvitesPage.vue
├── pages/CreateInvitePage.vue
├── pages/TemplatesPage.vue
├── pages/MediaPage.vue
├── pages/MissingEpisodesPage.vue
├── pages/DuplicatesPage.vue
├── pages/CalendarPage.vue
├── pages/TicketsPage.vue
├── pages/PointsPage.vue
├── pages/SubscriptionsPage.vue
├── pages/TasksPage.vue
├── pages/PosterPage.vue
├── api/invites.ts
├── api/templates.ts
├── api/media.ts
├── api/calendar.ts
├── api/tickets.ts
├── api/points.ts
├── api/portal.ts
├── components/charts/HeatmapChart.vue
├── components/charts/RadarChart.vue
├── components/charts/PieChart.vue
└── components/calendar/*.vue
```

### 修改文件 (前端) — 约 10 个
```
frontend/src/
├── pages/StatsPage.vue             重构为 Tab
├── pages/UserDetailPage.vue        增加 Tab
├── pages/NotificationsPage.vue     重构为 Tab
├── pages/SettingsPage.vue          扩展
├── router/index.ts                 新路由
├── api/stats.ts                    新端点
├── api/users.ts                    新端点
├── api/notifications.ts            大幅扩展
├── components/common/AppSidebar.vue 扩展菜单
├── components/common/TabBar.vue     扩展更多面板
└── vite.config.ts                   双入口配置
```

---

## 每个 Phase 的 Alembic 迁移

| Phase | 迁移文件 | 新增表 |
|-------|---------|--------|
| 1 | 0002_invite_templates | invite_codes, invite_usages, permission_templates, user_overrides |
| 2 | 无新表 | — |
| 3 | 无新表 | — |
| 4 | 0003_media | media_items, missing_episodes, dedup_strategies |
| 5 | 0004_community | calendar_entries, content_subscriptions, tickets, ticket_comments, points_accounts, points_transactions, daily_checkins |
| 6 | 0005_notifications | notification_channels, notification_templates, notification_rules, user_notification_prefs, notification_logs (扩展原表) |
| 7 | 0006_advanced | poster_templates, generated_posters |
