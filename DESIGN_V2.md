# Emby Next Console — 全局架构设计 v2.1

> 双站点架构：管理后台 + 用户门户

---

## 〇、架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx / Caddy 反代                     │
├────────────────────────┬────────────────────────────────┤
│   /admin               │   / (根路径)                    │
│   管理后台 (Admin)       │   用户门户 (User Portal)        │
│                        │                                │
│   登录: 本地管理员账号    │   登录: Emby 账号(用户名+密码)   │
│   JWT 鉴权              │   JWT 鉴权(含 Emby Token 桥接)  │
│   权限: admin 角色       │   权限: 普通用户                │
│                        │                                │
│   功能:                 │   功能:                        │
│   - 用户管理/邀请/权限    │   - 个人资料/改密码(→Emby同步)  │
│   - 数据分析/风控        │   - 观看历史/统计               │
│   - 媒体管理/去重        │   - 追剧日历                   │
│   - 任务中心/工单管理     │   - 提交工单/求片              │
│   - 系统设置/通知模板     │   - 签到积分/商城              │
│   - 通知通道配置         │   - 通知偏好/海报生成           │
└────────────────────────┴────────────────────────────────┘
                        │
                    FastAPI 后端
                    (统一 API 服务)
                        │
            ┌───────────┼───────────┐
            │           │           │
        PostgreSQL    Redis     Emby API
```

**关键设计决策：**
- 同一个 FastAPI 后端，通过路由前缀和权限中间件区分 Admin/Portal
- 前端两个独立 Vue App，分别打包到 `/admin` 和 `/` 路径
- 用户密码修改：调用 Emby API 直接同步，不在本地存储密码
- 管理员账号：本地 JWT 鉴权，不走 Emby

---

## 一、整体功能模块划分（13 大模块）

### 管理后台模块（10 个）

| # | 模块 | 说明 |
|---|------|------|
| 1 | Dashboard | 概览仪表盘 |
| 2 | Users | 用户管理（邀请/创建/权限/详情） |
| 3 | Analytics | 数据分析（观看数据/设备/排行/质量） |
| 4 | Risk | 风控天眼 |
| 5 | Calendar | 追剧日历（管理员全局视图） |
| 6 | Media | 媒体库（去重/缺集） |
| 7 | Tasks | 任务中心 |
| 8 | Tickets | 工单大厅（管理端） |
| 9 | Notifications | 通知中心（通道配置/模板编辑/场景总控） |
| 10 | Settings | 系统设置 |

### 用户门户模块（5 个）

| # | 模块 | 说明 |
|---|------|------|
| 1 | Home | 门户首页（推荐/继续观看/最新入库） |
| 2 | Profile | 个人中心（资料/密码/偏好/头像） |
| 3 | MyStats | 我的观影（历史/统计/生物钟/偏好） |
| 4 | Calendar | 追剧日历（我的追踪/想看/已看） |
| 5 | Tickets | 工单/求片（提交/查看/评论） |
| 6 | Points | 积分（签到/余额/排行/商城） |

---

## 二、管理后台详细设计

### 1. Dashboard

| 卡片 | 数据来源 | 刷新 |
|------|----------|------|
| 在线用户数 | Emby Sessions | 30s |
| 活跃播放数 | Emby Sessions | 30s |
| 待处理工单 | Tickets DB | 5min |
| 待处理风控 | RiskEvent DB | 5min |
| 今日新增用户 | Users API | 10min |
| 系统健康 | Health API | 5min |

额外组件：
- 实时播放列表（带进度条、设备信息）
- 今日趋势迷你图（24h 播放量折线）
- 最近 5 条未读通知

### 2. Users — 用户管理

#### 2.1 邀请系统

| 功能 | 字段 |
|------|------|
| 生成邀请码 | 邀请码(自动生成/自定义)、有效期、生成数量、权限继承源(模板用户)、并发限制、使用次数限制 |
| 邀请管理 | 列表：码、创建时间、过期时间、使用状态(已用/未用/过期)、使用者信息 |
| 邀请链接 | `https://domain/register?code=XXXX` → 注册后自动继承模板权限 |
| 统计 | 总发出/已使用/过期/使用率 |

#### 2.2 手动创建用户

| 字段 | 必填 | 说明 |
|------|------|------|
| 用户名 | ✅ | 唯一标识 |
| 用户备注 | ❌ | 管理员备注 |
| 初始密码 | ❌ | 不填自动生成 |
| 账号到期时间 | ❌ | 空 = 永久 |
| 专属并发限制 | ❌ | 覆盖全局 |
| 权限模板 | ❌ | 继承库权限+策略 |

#### 2.3 用户详情页（5 Tab）

**基础资料：** 头像、用户名、显示名、邮箱、状态、创建/最后活跃/到期时间
**库权限：** 媒体库 checkbox 列表、权限模板套用、变更记录
**高级策略：** 并发限制、码率限制、转码权限、客户端黑白名单
**观看数据：** 最近观看历史、累计时长、类型偏好、设备分布
**操作区：** 禁用/启用、删除、强制下线、发通知

#### 2.4 权限模板管理（独立页面）

| 功能 | 说明 |
|------|------|
| 创建模板 | 名称、描述、库权限选择、Policy 配置、Configuration 配置 |
| 编辑模板 | 修改后同步更新所有引用该模板的用户(可选) |
| 模板列表 | 模板名、关联用户数、创建时间 |
| 导入导出 | JSON 格式导入导出模板 |

### 3. Analytics — 数据分析

#### 3.1 用户数据

| 图表 | 说明 |
|------|------|
| 观看历史 | 全站/筛选用户，流水列表(时间、用户、影片、设备、时长) |
| 观影频率 | 日/周/月柱状图 |
| 24H 生物钟 | 0-24h 热力图 |
| 偏好天平 | 类型雷达图 |
| 设备分布 | 设备类型+客户端软件饼图 |

#### 3.2 全服排行

热度排行 / 时长排行 / 用户排行 / 近期热门 → 支持多维度筛选

#### 3.3 质量分析

分辨率分布 / 编码分布 / 码率分布 / 音轨分布 / 文件大小排行

**UI 设计原则：** Tab 分区 + 可折叠，不堆砌长页面。图表加载有渐入动画。能用图表不用纯表格。

### 4. Risk — 风控天眼

已有：并发越界检测、客户端黑名单、事件列表
需补充：实时并发雷达面板、历史事件趋势图、规则引擎配置(自定义阈值)、IP 黑名单、自动处置规则

### 5. Calendar — 追剧日历

月视图 / TMDB 数据来源 / 标记已看/想看 / 追踪列表 / iCal 导出

### 6. Media — 媒体库管理

#### 6.1 缺集管理

本地库 vs TMDB 比对 → 缺集列表 → 批量导出

#### 6.2 去重引擎

TMDB 分组 → 质量评分 → 策略配置 → **预览+确认** → 回收站(7天永久删除)

**安全：** 不自动删，必须预览确认。策略可自定义。

### 7. Tasks — 任务中心

Emby 计划任务 / 自定义任务 / 任务队列(ARQ) / 执行日志 / Cron 定时 / 手动触发

### 8. Tickets — 工单大厅

用户求片+问题反馈 / 工单状态流转 / 评论沟通 / 优先级 / 统计

### 9. Notifications — 通知中心（重点）

#### 9.1 通道配置

| 通道 | 配置项 |
|------|--------|
| 飞书 | Webhook URL、签名校验(可选) |
| Telegram | Bot Token、Chat ID |
| 企业微信 | Webhook URL |
| Bark | Device Key、Server URL |
| Email | SMTP 服务器、端口、用户名、密码、发件人 |
| 站内信 | 默认开启，无需配置 |

每个通道：启用/禁用、连接测试、发送记录

#### 9.2 消息模板编辑器

```
模板管理
├── 系统预设模板（不可删除，可修改）
│   ├── 新用户注册通知
│   ├── 账号到期提醒
│   ├── 并发越界告警
│   ├── 新工单通知
│   ├── 工单状态变更
│   ├── 签到提醒
│   ├── 系统异常告警
│   └── 新影片入库通知
│
├── 自定义模板（用户创建）
│   ├── 模板名称
│   ├── 模板内容（支持变量插值）
│   └── 适用场景
│
└── 模板编辑器
    ├── 富文本编辑（支持 Markdown）
    ├── 变量插入面板（点击插入 {variable}）
    ├── 实时预览（填入示例数据）
    └── 多语言支持（同一场景可设不同语言模板）
```

**模板变量系统：**

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `{username}` | 用户名 | zhangsan |
| `{display_name}` | 显示名 | 张三 |
| `{invite_code}` | 邀请码 | ABC123 |
| `{expire_date}` | 到期时间 | 2026-04-22 |
| `{ticket_title}` | 工单标题 | 请求添加XXX电影 |
| `{ticket_status}` | 工单状态 | 已完成 |
| `{points_balance}` | 积分余额 | 1500 |
| `{checkin_streak}` | 连续签到天数 | 7天 |
| `{system_status}` | 系统状态 | 正常 |
| `{error_message}` | 错误信息 | Redis连接超时 |
| `{media_title}` | 媒体标题 | 流浪地球3 |
| `{concurrent_count}` | 当前并发数 | 3 |
| `{concurrent_limit}` | 并发限额 | 2 |
| `{ip_address}` | IP 地址 | 192.168.1.1 |
| `{client_name}` | 客户端名称 | Emby for iOS |
| `{current_time}` | 当前时间 | 2026-03-22 08:30 |
| `{site_name}` | 站点名称 | 我的影视库 |

**通道×场景×模板 = 矩阵配置：**

```
场景: "新用户注册"
├── 飞书: ✅ 启用 → 使用模板 "新用户注册-飞书版" 
│   └── 🎉 新用户 {username} 注册成功，来自邀请码 {invite_code}
├── Telegram: ✅ 启用 → 使用模板 "New User Notification"
│   └── 🎉 New user {username} registered via invite {invite_code}
├── Email: ❌ 禁用
├── 站内信: ✅ 启用 → 使用模板 "注册通知-站内"
│   └── 欢迎 {username}！你的账号将于 {expire_date} 到期。
└── Bark: ❌ 禁用
```

#### 9.3 发送记录

- 每次推送的详细记录：时间、场景、通道、内容、发送状态
- 支持按场景/通道/时间筛选
- 失败重试机制

### 10. Settings — 系统设置

**原则：** Compose 只管 EMBA_HOST/EMBY_API_KEY/DB_URL/REDIS_URL，其余全部在 Web UI

| 分组 | 配置项 |
|------|--------|
| Emby 连接 | 服务器地址、API Key、连接测试 |
| 基础设置 | 站点名称、Logo、注册开关、语言 |
| 默认策略 | 全局并发限制、默认码率、默认账号有效期 |
| 权限模板 | CRUD（见 2.4） |
| 安全设置 | JWT 密钥、Token 过期、登录锁定 |
| 备份恢复 | 导出/导入配置、导出用户数据 |
| 关于 | 版本号、更新日志 |

---

## 三、用户门户详细设计

### 1. Home — 门户首页

| 区域 | 说明 |
|------|------|
| 继续观看 | 最近未看完的影片（调 Emby API） |
| 最新入库 | 最近添加的媒体 |
| 热门推荐 | 全站播放排行 |
| 个人数据卡片 | 本月观看时长、签到天数、积分余额 |
| 公告栏 | 管理员发布的公告 |

### 2. Profile — 个人中心

| 功能 | 说明 |
|------|------|
| 基础资料 | 头像(从Emby同步)、用户名、显示名、邮箱 |
| 修改密码 | 输入旧密码+新密码 → 调用 Emby API 更新 |
| 账号信息 | 注册时间、到期时间、VIP 状态、并发限制 |
| 通知偏好 | 选择接收哪些场景的通知、选择推送到哪些通道 |
| 设备管理 | 查看已登录设备、远程登出 |

**密码修改流程：**
```
用户输入旧密码+新密码 → 后端调用 Emby API 验证旧密码 
→ 调用 Emby API 更新密码 → 返回成功
```

### 3. MyStats — 我的观影

| 图表 | 说明 |
|------|------|
| 观看历史 | 我的观看记录，带封面缩略图 |
| 月度统计 | 本月看了多少、总时长 |
| 24H 生物钟 | 我的观影时段分布 |
| 类型偏好 | 我的观影类型雷达图 |
| 设备使用 | 我用什么设备看 |

### 4. Calendar — 追剧日历

我的追踪列表 / 想看/已看标记 / 月视图

### 5. Tickets — 求片/反馈

提交新工单 / 查看工单状态 / 在工单内评论沟通

### 6. Points — 积分

每日签到(连续加成) / 余额 / 流水 / 排行 / 商城兑换

---

## 四、后端路由结构

```
# 管理后台 API (需要 admin 角色)
/api/admin/dashboard/*
/api/admin/users/*
/api/admin/users/:id/permissions
/api/admin/users/:id/override
/api/admin/invites/*
/api/admin/templates/*
/api/admin/analytics/*
/api/admin/risk/*
/api/admin/media/*
/api/admin/calendar/admin-view
/api/admin/tasks/*
/api/admin/tickets/*
/api/admin/notifications/channels
/api/admin/notifications/templates
/api/admin/notifications/rules
/api/admin/notifications/logs
/api/admin/settings/*

# 用户门户 API (需要登录)
/api/portal/profile
/api/portal/profile/password
/api/portal/profile/devices
/api/portal/profile/notifications
/api/portal/stats/me
/api/portal/calendar/*
/api/portal/tickets/*
/api/portal/points/*
/api/portal/points/checkin
/api/portal/home/*

# 公开 API (不需要登录)
/api/auth/login
/api/auth/register?code=XXX
/api/public/info
```

---

## 五、数据库模型（完整版）

```python
# ===== 用户与权限 =====
class AdminUser(Model):
    """本地管理员账号"""
    username: str
    password_hash: str
    role: str  # super_admin/admin/viewer
    created_at: datetime

class InviteCode(Model):
    code: str
    template_user_id: str      # 权限继承源 Emby User ID
    permission_template_id: str | None  # 或使用权限模板
    max_uses: int
    used_count: int
    expires_at: datetime
    concurrent_limit: int | None
    created_by: str
    created_at: datetime
    status: str                # active/used/expired/disabled

class InviteUsage(Model):
    invite_id: str
    emby_user_id: str
    used_at: datetime

class PermissionTemplate(Model):
    name: str
    description: str
    library_access: list[str]
    policy_json: dict
    configuration_json: dict
    is_default: bool
    created_at: datetime
    updated_at: datetime

class UserOverride(Model):
    """用户级覆盖配置"""
    emby_user_id: str          # 唯一
    concurrent_limit: int | None
    max_bitrate: int | None
    allow_transcode: bool | None
    client_blacklist: list[str] | None
    note: str
    expires_at: datetime | None

# ===== 追剧日历 =====
class CalendarEntry(Model):
    user_id: str
    tmdb_id: int
    media_type: str
    title: str
    release_date: date
    poster_url: str | None
    status: str                # want_to_watch/watching/watched
    created_at: datetime

# ===== 工单系统 =====
class Ticket(Model):
    user_id: str               # Emby User ID
    title: str
    description: str
    category: str              # request/issue/suggestion
    priority: str
    status: str                # open/in_progress/completed/rejected
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime

class TicketComment(Model):
    ticket_id: str
    user_id: str
    is_admin: bool
    content: str
    created_at: datetime

# ===== 积分系统 =====
class PointsAccount(Model):
    emby_user_id: str          # 唯一
    balance: int
    total_earned: int
    total_spent: int

class PointsTransaction(Model):
    emby_user_id: str
    amount: int
    reason: str
    created_at: datetime

class DailyCheckin(Model):
    emby_user_id: str
    checkin_date: date
    streak: int
    points_earned: int

# ===== 媒体管理 =====
class MediaItem(Model):
    emby_item_id: str
    tmdb_id: int | None
    title: str
    media_type: str
    resolution: str
    codec: str
    bitrate: int
    file_size: int
    quality_score: float
    is_duplicate: bool
    duplicate_group: str | None
    last_scanned: datetime

class MissingEpisode(Model):
    series_id: str
    series_name: str
    season: int
    episode: int
    tmdb_title: str
    scanned_at: datetime

class DedupStrategy(Model):
    name: str
    keep_rule: str
    auto_delete: bool
    is_active: bool

# ===== 通知系统 =====
class NotificationChannel(Model):
    """通知通道配置"""
    name: str                  # 飞书/Telegram/企微/Bark/Email
    channel_type: str
    config_json: dict          # Webhook URL, Token 等
    is_enabled: bool
    last_test_at: datetime | None
    last_test_ok: bool

class NotificationTemplate(Model):
    """消息模板"""
    name: str
    scenario: str              # new_user/ticket_new/expire_warning 等
    channel_type: str          # all = 通用, 或指定通道
    content: str               # 含 {variable} 的模板文本
    is_system: bool            # 系统预设不可删除
    created_at: datetime

class NotificationRule(Model):
    """场景×通道×模板 矩阵"""
    scenario: str
    channel_id: str
    template_id: str
    is_enabled: bool
    recipient_type: str        # admin/user/all
    recipient_id: str | None   # 指定用户(可选)

class NotificationLog(Model):
    """发送记录"""
    rule_id: str | None
    scenario: str
    channel_type: str
    recipient: str
    content: str
    status: str                # sent/failed
    error: str | None
    sent_at: datetime

# ===== 海报 =====
class PosterTemplate(Model):
    name: str
    thumbnail_url: str
    template_json: dict
    is_active: bool

class GeneratedPoster(Model):
    user_id: str
    template_id: str
    time_range: str
    image_url: str
    created_at: datetime

# ===== 公告 =====
class Announcement(Model):
    title: str
    content: str
    created_by: str
    is_active: bool
    created_at: datetime
```

---

## 六、前端路由结构

### 管理后台 (/admin/*)

```
/admin                    → 重定向到 /admin/dashboard
/admin/dashboard          概览仪表盘
/admin/users              用户列表
/admin/users/invites      邀请管理
/admin/users/invites/create 创建邀请
/admin/users/templates    权限模板
/admin/users/:id          用户详情
/admin/analytics          数据分析(默认: 用户数据)
/admin/analytics/users    用户数据
/admin/analytics/media    媒体排行
/admin/analytics/quality  质量分析
/admin/calendar           追剧日历
/admin/media              媒体库
/admin/media/duplicates   去重管理
/admin/media/missing      缺集管理
/admin/risk               风控天眼
/admin/tasks              任务中心
/admin/tickets            工单大厅
/admin/tickets/:id        工单详情
/admin/notifications      通知中心
/admin/notifications/channels   通道配置
/admin/notifications/templates  模板编辑
/admin/notifications/rules      场景矩阵
/admin/notifications/logs       发送记录
/admin/settings           系统设置
```

### 用户门户 (/*)

```
/                         门户首页
/profile                  个人中心
/profile/password         修改密码
/profile/devices          设备管理
/profile/notifications    通知偏好
/stats                    我的观影统计
/calendar                 追剧日历
/tickets                  我的工单
/tickets/:id              工单详情
/points                   积分中心
/points/checkin           签到
```

---

## 七、前端 TabBar 适配

### 管理后台 Mobile TabBar

```
├── 概览 (Dashboard)
├── 用户 (Users)
├── 分析 (Analytics)
├── 媒体 (Media)
└── 更多 (More Panel)
    ├── 风控天眼
    ├── 追剧日历
    ├── 任务中心
    ├── 工单大厅
    ├── 通知中心
    ├── 系统设置
    ├── 切换主题
    └── 退出登录
```

### 管理后台 Desktop Sidebar（可折叠）

```
├── 概览
├── 用户管理 ▸
│   ├── 用户列表
│   ├── 邀请管理
│   └── 权限模板
├── 数据分析 ▸
│   ├── 用户数据
│   ├── 媒体排行
│   └── 质量分析
├── 媒体库 ▸
│   ├── 媒体管理
│   ├── 去重管理
│   └── 缺集管理
├── 追剧日历
├── 风控天眼
├── 任务中心
├── 工单大厅
├── 通知中心 ▸
│   ├── 通道配置
│   ├── 模板编辑
│   ├── 场景矩阵
│   └── 发送记录
└── 系统设置
```

### 用户门户 TabBar

```
├── 首页 (Home)
├── 日历 (Calendar)
├── 积分 (Points)
├── 工单 (Tickets)
└── 我的 (Profile)
```

---

## 八、开发 Phase 规划（修订版）

### Phase 1: 用户管理增强（核心中的核心）
- [ ] 邀请码系统（生成/管理/注册流程）
- [ ] 权限模板 CRUD
- [ ] 手动创建用户
- [ ] 用户详情增强（库权限编辑+高级策略）
- [ ] 用户级并发限制

### Phase 2: 用户门户骨架
- [ ] 独立前端 App（/ 路径）
- [ ] Emby 账号登录（验证 Emby 密码）
- [ ] 个人中心（资料/密码修改→Emby 同步）
- [ ] 我的观影数据
- [ ] 公告栏

### Phase 3: Analytics 重构
- [ ] 观看历史（全站+按用户筛选）
- [ ] 24H 生物钟热力图
- [ ] 设备/软件分布
- [ ] 多维度排行
- [ ] 质量分析

### Phase 4: 媒体管理
- [ ] 缺集扫描+TMDB 比对
- [ ] 去重引擎（TMDB 分组+质量评分+策略配置+预览确认）
- [ ] 媒体库浏览

### Phase 5: 社区功能
- [ ] 追剧日历（TMDB+月视图）
- [ ] 工单大厅（求片/反馈）
- [ ] 积分引擎（签到+流水+商城）

### Phase 6: 通知系统
- [ ] 多通道配置（飞书/Telegram/企微/Bark/Email）
- [ ] 消息模板编辑器（变量系统+实时预览）
- [ ] 场景×通道矩阵配置
- [ ] 发送记录+失败重试

### Phase 7: 自动化与高级
- [ ] 任务中心（自定义任务+Cron+ARQ 队列）
- [ ] 机器人指令交互（Telegram/飞书 Bot）
- [ ] 海报工坊
- [ ] WebSocket 实时推送
- [ ] 系统设置完善（备份恢复）

---

## 九、Emby Pulse 对比总结

| 对比维度 | Emby Pulse | 我们的方案 |
|----------|-----------|-----------|
| 登录体系 | 可能也是本地 | ✅ 双站点：管理员本地 + 用户 Emby 账号 |
| 用户门户 | 无/简单 | ✅ 独立门户，用户可改密码/看数据/签到 |
| 去重 | 可能自动 | ✅ 必须预览+确认，安全第一 |
| 通知模板 | 可能固定 | ✅ 完全自定义模板+变量系统+通道矩阵 |
| 工单系统 | 有 | ✅ 有，且区分管理端和用户端 |
| 积分系统 | 有 | ✅ 有，含签到+商城+排行 |
| Compose 配置 | 散布 | ✅ Compose 只管基础，其余全在 Web UI |
| 数据可视化 | 好看 | ✅ 对标，图表优先+动画过渡+移动端适配 |
| 界面设计 | 好看 | ✅ iOS glassmorphism 风格，浅色/深色主题 |

---

**下一步：** 整合图图的反馈 → 定稿 → 按 Phase 开发
