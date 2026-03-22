# Emby Next Console — 全局架构设计 v2.2

> 双站点架构：管理后台 + 用户门户 + 用户订阅通知

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

### 9. Notifications — 通知系统（两层架构）

通知系统分管理员层和用户层，各自独立。

#### 9.1 管理员层（管理后台）

**通道配置：**

| 通道 | 配置项 |
|------|--------|
| 飞书 | Webhook URL、签名校验(可选) |
| Telegram | Bot Token、Chat ID |
| 企业微信 | Webhook URL |
| Bark | Device Key、Server URL |
| Email | SMTP 服务器、端口、用户名、密码、发件人 |
| 站内信 | 默认开启，无需配置 |

每个通道：启用/禁用、连接测试、发送记录

**消息模板管理：**

| 模板类型 | 说明 | 权限 |
|----------|------|------|
| 系统预设 | 不可删除，可修改 | 管理员 |
| 管理员模板 | 管理员创建 | 管理员 |
| 分享模板 | 管理员标记"分享给用户" | 用户可使用/复制 |

```
模板管理
├── 系统预设模板（不可删除）
│   ├── 新用户注册通知
│   ├── 账号到期提醒
│   ├── 并发越界告警
│   ├── 新工单通知
│   ├── 工单状态变更
│   ├── 签到提醒
│   ├── 系统异常告警
│   ├── 新影片入库通知
│   └── 异常登录提醒
│
├── 管理员自定义模板
│   └── 标记"分享给用户" → 用户可见、可用、可复制后自定义
│
└── 模板编辑器
    ├── Markdown 编辑
    ├── 变量插入面板（点击插入 {variable}）
    ├── 实时预览（填入示例数据）
    └── 多语言（同一场景可设不同语言）
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
| `{checkin_streak}` | 连续签到 | 7天 |
| `{system_status}` | 系统状态 | 正常 |
| `{error_message}` | 错误信息 | Redis连接超时 |
| `{media_title}` | 媒体标题 | 流浪地球3 |
| `{series_name}` | 剧集名称 | 庆余年 |
| `{season_episode}` | 季集 | S02E05 |
| `{concurrent_count}` | 当前并发 | 3 |
| `{concurrent_limit}` | 并发限额 | 2 |
| `{ip_address}` | IP 地址 | 192.168.1.1 |
| `{client_name}` | 客户端 | Emby for iOS |
| `{current_time}` | 当前时间 | 2026-03-22 08:30 |
| `{site_name}` | 站点名称 | 我的影视库 |

**管理员场景矩阵（场景×通道×模板）：**

```
场景: "新用户注册"
├── 飞书: ✅ → 模板 "新用户注册-飞书版"
├── Telegram: ✅ → 模板 "New User Notification"
├── Email: ❌ 禁用
└── 站内信: ✅ → 模板 "注册通知-站内"
```

#### 9.2 用户层（用户门户 /profile/notifications）

**用户通知偏好：**

| 通知类型 | 默认 | 说明 |
|----------|------|------|
| 账号到期提醒 | ✅ | 到期前 N 天通知 |
| 异常登录提醒 | ✅ | 新设备/IP 登录时 |
| 工单状态变更 | ✅ | 工单有回复/状态变化 |
| 签到提醒 | ❌ | 每日提醒签到(可选) |
| 订阅更新 | ✅ | 追踪的剧集/电影有更新 |

每个通知类型可选择推送到哪个通道（用户可选的通道由管理员在通道配置中设置"允许用户使用"）。

**内容订阅管理（核心新功能）：**

```
我的订阅
├── 追踪中的剧集
│   ├── 《庆余年》 S02 追踪中 → 新集入库时通知
│   ├── 《某综艺》 追踪中 → 首播时通知
│   └── 《某剧》已完结 → 取消追踪
│
├── 关注的电影
│   ├── 《流浪地球3》→ 首播时通知
│   └── 《某片》→ 上线流媒体时通知
│
└── 订阅规则
    ├── 新集入库 → 默认开启
    ├── 首播/首映 → 可选
    └── 推送通道 → 用户自选
```

**订阅创建方式：**
1. **追剧日历** → 点"追踪"按钮自动创建订阅
2. **搜索影片** → 点"关注"按钮
3. **用户门户首页** → 推荐内容点"订阅"

**订阅通知流程：**

```
Emby 新集入库 
  → Webhook 触发 (item.add)
  → Event Bus 收到事件
  → 查询：哪些用户订阅了这部剧？
  → 对每个订阅用户：
      → 查用户的通道偏好
      → 用用户选择的模板渲染
      → 推送通知："📺《庆余年》S02E05 已入库！"
```

**用户模板：**

| 类型 | 说明 | 操作 |
|------|------|------|
| 管理员分享的模板 | 管理员创建并标记分享 | 可直接使用 / 可复制后自定义 |
| 我的模板 | 用户自己创建 | 完全自定义 |

```
用户模板编辑器
├── 可用模板
│   ├── 系统默认
│   ├── 管理员分享-简洁版（📺 {series_name} {season_episode} 更新了！）
│   ├── 管理员分享-详细版（📺 {series_name} 第{season}季第{episode}集已入库...）
│   └── 我的自定义模板（用户自己写的）
│
└── 创建新模板
    ├── 模板名称
    ├── 通知内容（支持 Markdown + 变量）
    └── 预览
```

#### 9.3 发送记录

- 管理员可查看全站所有通知发送记录
- 用户只能查看自己的通知发送记录
- 支持按场景/通道/时间筛选
- 失败重试机制

#### 9.4 通知数据模型

```python
class NotificationChannel(Model):
    """通知通道配置（管理员管理）"""
    name: str                  # 飞书/Telegram/企微/Bark/Email
    channel_type: str
    config_json: dict
    is_enabled: bool           # 管理员是否启用
    allow_user_use: bool       # 是否允许用户选择此通道
    last_test_at: datetime | None
    last_test_ok: bool

class NotificationTemplate(Model):
    """消息模板"""
    name: str
    scenario: str              # new_user/ticket_new/sub_update 等
    channel_type: str          # all = 通用, 或指定通道
    content: str               # {variable} 模板文本
    is_system: bool            # 系统预设
    shared_with_users: bool    # 管理员标记是否分享给用户
    created_by: str            # admin/user id
    owner_type: str            # admin/user
    created_at: datetime

class NotificationRule(Model):
    """管理员场景矩阵"""
    scenario: str
    channel_id: str
    template_id: str
    is_enabled: bool

class UserNotificationPref(Model):
    """用户通知偏好"""
    emby_user_id: str
    notify_expire: bool        # 到期提醒
    notify_login: bool         # 异常登录
    notify_ticket: bool        # 工单变更
    notify_checkin: bool       # 签到提醒
    notify_subscription: bool  # 订阅更新
    channels: list[str]        # 用户选择的通道 ["telegram", "email"]
    custom_template_id: str | None  # 用户选择的自定义模板

class ContentSubscription(Model):
    """内容订阅（核心新表）"""
    emby_user_id: str
    tmdb_id: int
    media_type: str            # movie/tv
    title: str
    poster_url: str | None
    notify_on: list[str]       # ["new_episode", "premiere", "finale"]
    channel: str | None        # 用户选择的推送通道(Null=用默认)
    is_active: bool
    created_at: datetime

class NotificationLog(Model):
    """发送记录"""
    scenario: str
    channel_type: str
    sender_type: str           # system/admin/user_subscription
    recipient_user_id: str | None
    content: str
    status: str                # sent/failed
    error: str | None
    sent_at: datetime
```

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
| 通知偏好 | 选择接收哪些场景通知 + 选择通道 + 管理订阅 + 模板选择 |
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
/profile/subscriptions    我的订阅（追踪/关注）
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

## 十、影视数据源方案

### 三层数据源

| 层 | 数据源 | 用途 |
|----|--------|------|
| 已入库内容 | Emby API | 标题、封面、元数据全部从 Emby 直接读 |
| 未入库内容 | TMDB API (免费) | 搜索、上映日历、海报、详情 |
| 封面缓存 | 本地 + CDN | TMDB 海报本地缓存，减少外部请求 |

### TMDB 集成

**申请：** https://www.themoviedb.org/settings/api → 免费 API Key

**API 限制：** 40次/10秒，支持中文(zh-CN)

**核心接口：**

| 接口 | TMDB Endpoint | 用途 |
|------|---------------|------|
| 搜索影片 | `GET /search/movie?query=xxx` | 求片/订阅搜索 |
| 搜索剧集 | `GET /search/tv?query=xxx` | 求片/订阅搜索 |
| 电影详情 | `GET /movie/{id}` | 影片详情页 |
| 剧集详情 | `GET /tv/{id}` | 剧集详情页(含季集列表) |
| 某季集列表 | `GET /tv/{id}/season/{n}` | 缺集检测比对 |
| 即将上映 | `GET /movie/upcoming` | 追剧日历 |
| 正在播出 | `GET /tv/on_the_air` | 追剧日历 + 订阅同步 |
| 海报图片 | `https://image.tmdb.org/t/p/w500/{path}` | 海报显示 |

### 后端模块设计

```
backend/app/core/tmdb.py        ← TMDB 客户端
├── search_movie(query, page)
├── search_tv(query, page)
├── get_movie(tmdb_id)
├── get_tv(tmdb_id)
├── get_tv_season(tmdb_id, season)
├── upcoming_movies(page)
├── on_the_air(page)
├── poster_url(path, size)      ← size: w92/w185/w300/w500/w780/original
└── backdrop_url(path, size)

backend/app/modules/media/service.py  ← 媒体服务(依赖 tmdb.py)
├── sync_library()                    同步 Emby 库到本地索引
├── detect_missing_episodes()         缺集检测
├── find_duplicates()                 去重分析
└── get_calendar_data(start, end)     获取日历数据

backend/app/modules/calendar/service.py  ← 日历服务
├── get_month_view(year, month)       月视图数据
├── get_upcoming()                    即将上映
├── subscribe(user_id, tmdb_id)       用户订阅
├── unsubscribe(user_id, tmdb_id)     取消订阅
└── sync_subscriptions()              定时同步订阅更新
```

### 封面图策略

| 场景 | 数据源 | URL 格式 |
|------|--------|----------|
| Emby 已入库 | Emby API | `PrimaryImageUrl` (Emby 自带) |
| TMDB 搜索结果 | TMDB | `image.tmdb.org/t/p/w300/{poster_path}` |
| 追剧日历 | TMDB | 同上，w185 缩略图 |
| 用户海报生成 | TMDB + Emby | 组合渲染 |

**封面缓存：** TMDB 海报 URL 通过后端代理缓存，避免直接引用外部 CDN：
```
GET /api/proxy/image?url=https://image.tmdb.org/t/p/w500/xxx.jpg
→ 后端下载并缓存到本地/Redis
→ 返回图片，设置长缓存头
```

### 定时任务与 Webhook（混合方案）

```
新集入库通知 → Emby Webhook（实时，核心）
  → Emby Library Scan 发现新文件
  → 发 Webhook: { Event: "library.new", Item: { Type, SeriesName, ParentIndexNumber, IndexNumber, ProviderIds: { Tmdb: "12345" } } }
  → 后端收到 → 解析 tmdb_id → 查 ContentSubscription → 推送用户
  → "📺《庆余年》S02E05 已入库！"

即将上映日历 → TMDB 定时同步（每天 1 次，仅用于日历展示）
  → 同步 upcoming 电影 + on_the_air 剧集
  → 存入 CalendarEntry（tmdb_id, title, poster, release_date）
  → 前端日历页面展示

缺集检测 → 手动触发或每周（对比 Emby 库 vs TMDB 集列表）

电影首播通知 → TMDB 定时同步 + 对比用户关注列表
  → 关注的电影 release_date 到了 → 触发通知
```

**Webhook 事件处理（在现有 webhook/service.py 扩展）：**

```python
# webhook/service.py 中新增 library.new 处理
async def handle_library_new(payload):
    item = payload.get("Item", {})
    tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
    item_type = item.get("Type")  # Episode / Movie
    series_name = item.get("SeriesName")
    season = item.get("ParentIndexNumber")
    episode = item.get("IndexNumber")
    
    if item_type == "Episode" and tmdb_id:
        # 查哪些用户订阅了这部剧
        subs = await get_subscriptions(tmdb_id=tmdb_id, notify_on="new_episode")
        for sub in subs:
            await send_user_notification(
                user_id=sub.emby_user_id,
                template_vars={
                    "series_name": series_name or item.get("Name"),
                    "season_episode": f"S{season:02d}E{episode:02d}",
                    "media_title": item.get("Name"),
                },
                channel=sub.channel  # 用户自选的通道
            )
    
    elif item_type == "Movie" and tmdb_id:
        # 查哪些用户关注了这部电影
        subs = await get_subscriptions(tmdb_id=tmdb_id, notify_on="premiere")
        for sub in subs:
            await send_user_notification(...)
```

---

**下一步：** 整合图图反馈 → 定稿 → 按 Phase 开发
