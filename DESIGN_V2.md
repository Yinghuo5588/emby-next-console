# Emby Next Console — 全局架构设计 v2

> 对标 Emby Pulse 优点，去其缺点，做更优方案

---

## 一、整体功能模块划分（12 大模块）

```
Emby Next Console
├── 1. Dashboard        概览仪表盘（实时状态一眼看清）
├── 2. Users            用户管理（邀请/创建/配置/权限）
├── 3. Analytics         数据分析（观看数据+设备数据+热度排行+质量分析）
├── 4. Risk             风控天眼（并发越界/客户端拦截/实时监控）
├── 5. Calendar          追剧日历（上映时间线+观影计划）
├── 6. Media             媒体库（缺集管理/去重引擎/质量评分）
├── 7. Tasks             任务中心（计划任务/后台作业/执行日志）
├── 8. Tickets           工单大厅（用户求片/问题反馈/审批流程）
├── 9. Points            积分引擎（签到/消费/排行/商城）
├── 10. Notifications    通知中心（双通道推送/场景总控/机器人交互）
├── 11. Poster           海报工坊（智能生成观影海报）
└── 12. Settings         系统设置（Emby连接/基础配置/权限模板/Compose只管基础项）
```

---

## 二、各模块详细设计

### 1. Dashboard — 概览仪表盘

**目标：** 一眼看清系统状态，30 秒内知道有没有问题

| 卡片 | 数据来源 | 刷新频率 |
|------|----------|----------|
| 在线用户数 | Emby Sessions API | 30s |
| 活跃播放数 | Emby Sessions API | 30s |
| 待处理工单 | Tickets DB | 5min |
| 待处理风控事件 | RiskEvent DB | 5min |
| 今日新增用户 | Users API | 10min |
| 系统健康状态 | Health API | 5min |

**额外组件：**
- **实时播放列表**：当前播放会话，带进度条、设备信息（已实现，保留）
- **今日趋势迷你图**：24h 播放量折线
- **最近通知**：最近 5 条未读通知

**不放在这里：** 详细统计、排行榜、历史分析 → 全部放 Analytics

---

### 2. Users — 用户管理（对标 Emby Pulse，重点模块）

#### 2.1 邀请系统

| 功能 | 字段/说明 |
|------|-----------|
| 生成邀请码 | 邀请码(自动生成/自定义)、账号有效期(天/永久)、生成数量(1~批量)、权限继承源(选择模板用户，全量克隆库权限+策略)、并发限制(可选)、单次/多次使用 |
| 邀请管理 | 列表：邀请码、创建时间、过期时间、使用状态(已用/未用/过期)、使用者信息、初始时长、操作(复制链接/禁用/删除) |
| 邀请链接格式 | `https://domain/register?code=XXXX` → 自动填入邀请码，注册后自动继承模板权限 |
| 邀请统计 | 总发出数/已使用数/过期数/使用率 |

#### 2.2 手动创建用户

| 字段 | 必填 | 说明 |
|------|------|------|
| 用户名 | ✅ | 唯一标识 |
| 用户备注 | ❌ | 管理员备注 |
| 初始密码 | ❌ | 不填则自动生成随机密码 |
| 账号到期时间 | ❌ | 空 = 永久 |
| 专属并发限制 | ❌ | 覆盖全局默认值 |
| 权限同步模板 | ❌ | 选择一个模板用户，继承其库权限+策略 |

#### 2.3 用户详情页

**基础资料 Tab：**
- 头像(从 Emby 同步)、用户名、显示名、邮箱、状态(active/disabled/expired)
- 账号创建时间、最后活跃时间、到期时间
- 修改备注、重置密码(管理员)

**库权限 Tab：**
- 媒体库列表(checkbox)，每个库可单独授权/取消
- 权限模板选择 → 一键套用
- 变更记录(谁改的、什么时候、改了什么)

**高级策略 Tab：**
- 专属并发限制(覆盖全局)
- 最大码率限制
- 是否允许转码
- 客户端白名单/黑名单(用户级别)
- 上传/下载带宽限制(可选)

**观看数据 Tab：**
- 观看历史列表(最近 50 条)
- 累计观看时长
- 观影偏好(类型分布)
- 设备使用分布

**操作区：**
- 禁用/启用账号
- 删除账号(确认弹窗)
- 强制下线(踢出所有会话)
- 发送通知(单独给该用户推送消息)

---

### 3. Analytics — 数据分析（对标 Emby Pulse 的数据统计）

分三个子区域：

#### 3.1 用户数据

| 图表 | 说明 |
|------|------|
| 观看历史 | 全站/筛选用户，流水式列表(时间、用户、影片、设备、时长、进度) |
| 观影频率统计 | 按日/周/月聚合的观看次数柱状图 |
| 24H 观影生物钟 | 0-24h 每小时观看量热力图(发现用户活跃时段) |
| 偏好天平 | 类型偏好雷达图(电影 vs 电视剧、各类型占比) |
| 设备分布 | 饼图：设备类型(iOS/Android/TV/Web) + 客户端软件(Emby/Plex/Infuse等) |
| 软件版本分布 | 各客户端版本占比 |

#### 3.2 全服播放排行

| 维度 | 说明 |
|------|------|
| 热度排行 | 播放次数 Top N(可筛选：电影/电视剧/音乐/全类型) |
| 时长排行 | 累计观看时长 Top N |
| 用户播放量排行 | 每个用户的总播放次数/时长 |
| 近期热门 | 最近 7/30 天新增播放最多 |
| 多维度筛选 | 按媒体类型、时间范围、全站/单用户交叉筛选 |

#### 3.3 质量分析

| 图表 | 说明 |
|------|------|
| 分辨率分布 | 4K/1080p/720p/SD 各占比 |
| 编码格式分布 | H.265/H.264/AV1 等 |
| 码率分布 | 各码率区间的媒体数量 |
| 音轨分布 | TrueHD/Atmos/DTS/AAC 等 |
| 文件大小排行 | 最大的 N 个文件 |

**Emby Pulse 缺点改进：**
- 他可能把所有图表堆在一个长页面 → 我们用 Tab 分区 + 可折叠
- 支持自定义时间范围(不只有预设 7/30/90)
- 图表支持导出为图片/PDF

---

### 4. Risk — 风控天眼（已有，补充完善）

**已有功能：**
- 并发越界检测 + 处理
- 客户端黑名单管理
- 事件列表 + 筛选

**需要补充：**
- 实时并发雷达面板(当前所有会话的并发状态，类似雷达扫描)
- 历史事件趋势图(每天产生多少事件)
- 规则引擎配置(自定义阈值，不需要改 compose)
- IP 黑名单管理
- 自动处置规则(超过 N 次自动封禁 X 小时)

---

### 5. Calendar — 追剧日历

| 功能 | 说明 |
|------|------|
| 月视图日历 | 显示当日上映的电影/剧集 |
| 数据来源 | Emby 媒体库 + TMDB API(获取上映日期) |
| 标记已看 | 用户可以标记"已看"/"想看" |
| 追踪列表 | 用户自定义追踪的剧集，显示最新一集状态 |
| 管理员视图 | 全站热门追踪排行(哪些剧被最多人追) |
| 日历导出 | iCal 格式，导入到手机日历 |

---

### 6. Media — 媒体库管理

#### 6.1 缺集管理

| 功能 | 说明 |
|------|------|
| 扫描比对 | 本地库剧集 vs TMDB 标准季/集 |
| 缺集列表 | 哪部剧缺了哪一季哪一集，严重程度标注 |
| 批量导出 | 导出缺集清单(CSV/TXT) |

#### 6.2 去重引擎

| 功能 | 说明 |
|------|------|
| TMDB 分组 | 同一影片的多个版本自动归组 |
| 质量评分 | 综合分辨率/编码/码率/音轨 评分排序 |
| 去重策略配置 | 自定义保留规则(保留最高质量/最小体积/最新版本) |
| 预览+确认 | 去重前预览将删除哪些，确认后批量执行 |
| 安全机制 | 默认移到回收站，7天后永久删除 |

**Emby Pulse 缺点改进：**
- 去重不应该全自动 → 必须预览+确认，安全第一
- 保留策略要可自定义，不只有"保留最高质量"

---

### 7. Tasks — 任务中心

| 功能 | 说明 |
|------|------|
| Emby 计划任务 | 读取 Emby 的 ScheduledTasks，展示/触发 |
| 自定义任务 | 去重扫描、缺集检测、数据同步等 |
| 任务队列 | 后台任务队列(用 Celery/ARQ，不阻塞主进程) |
| 执行日志 | 每次执行的详细日志(开始时间、结束时间、状态、输出) |
| 定时调度 | Cron 表达式配置执行频率 |
| 手动触发 | 一键触发任何任务 |

---

### 8. Tickets — 工单大厅

| 功能 | 说明 |
|------|------|
| 用户求片 | 用户提交影片请求(名称+链接+备注) |
| 问题反馈 | 使用问题、建议等 |
| 工单状态 | 待处理 → 处理中 → 已完成/已拒绝 |
| 评论沟通 | 管理员和用户在工单内对话 |
| 优先级 | 低/中/高/紧急 |
| 统计 | 待处理数、平均处理时长、完成率 |

---

### 9. Points — 积分引擎

| 功能 | 说明 |
|------|------|
| 签到系统 | 每日签到得积分，连续签到加成 |
| 积分规则 | 自定义：观看时长换积分、邀请注册得积分等 |
| 积分商城 | 兑换 VIP 时长、下载权限等 |
| 积分排行 | 全站积分榜 |
| 积分流水 | 每笔积分变动的明细 |

---

### 10. Notifications — 通知中心（对标 Emby Pulse）

#### 10.1 推送通道

| 通道 | 支持 |
|------|------|
| 飞书机器人 | ✅ Webhook |
| Telegram Bot | ✅ Bot API |
| 企业微信 | ✅ Webhook |
| Bark | ✅ Push API |
| Email | ✅ SMTP |
| 站内信 | ✅ 系统内通知 |

#### 10.2 推送场景总控

| 场景 | 默认 |
|------|------|
| 新用户注册 | 管理员通知 |
| 账号即将到期 | 用户通知(提前N天) |
| 并发越界 | 管理员通知 |
| 新工单 | 管理员通知 |
| 工单状态变更 | 用户通知 |
| 签到提醒 | 用户通知(可选) |
| 系统异常 | 管理员紧急通知 |
| 新影片入库 | 所有用户通知(可选) |

**每个场景可单独配置：** 启用/禁用 + 选择推送通道

#### 10.3 机器人指令交互

- 用户可通过机器人查询：今日签到、积分余额、账号到期时间、当前播放状态
- 管理员可通过机器人：查看在线人数、处理工单、禁用用户

---

### 11. Poster — 海报工坊

| 功能 | 说明 |
|------|------|
| 个人海报 | 根据用户观影数据生成专属海报 |
| 时间切片 | 选择分析范围(本月/本年/全部) |
| 数据来源 | 可选择统计哪些观看记录 |
| 模板系统 | 多种海报模板(简约/炫彩/复古) |
| 导出 | 下载为 PNG，可分享到社交媒体 |

---

### 12. Settings — 系统设置

**原则：** Compose 只管最基础的环境变量(EMBY_HOST, EMBY_API_KEY, DB_URL, REDIS_URL)。其余全部在 Web UI 配置。

| 分组 | 配置项 |
|------|--------|
| Emby 连接 | 服务器地址、API Key、连接测试 |
| 基础设置 | 站点名称、Logo、注册开关、默认语言 |
| 默认策略 | 全局默认并发限制、默认码率限制、默认账号有效期 |
| 权限模板 | 创建/编辑权限模板(库权限+策略打包成模板) |
| 安全设置 | JWT 密钥、Token 过期时间、登录失败锁定 |
| 备份恢复 | 导出/导入配置、导出用户数据 |
| 关于 | 版本号、更新日志、项目信息 |

---

## 三、数据库新增模型

```python
# 用户管理增强
class InviteCode(Model):
    code: str          # 邀请码
    template_user_id: str  # 权限继承源
    max_uses: int      # 最大使用次数
    used_count: int    # 已使用次数
    expires_at: datetime
    concurrent_limit: int | None
    created_by: str
    created_at: datetime
    status: str        # active/used/expired/disabled

class InviteUsage(Model):
    invite_id: str
    user_id: str
    used_at: datetime

class PermissionTemplate(Model):
    name: str          # 模板名
    description: str
    library_access: list[str]  # 允许的库 ID
    policy_json: dict  # Emby Policy
    configuration_json: dict  # Emby Configuration

class UserOverride(Model):
    user_id: str       # Emby User ID
    concurrent_limit: int | None
    max_bitrate: int | None
    allow_transcode: bool | None
    client_blacklist: list[str] | None
    note: str
    expires_at: datetime | None

# 追剧日历
class CalendarEntry(Model):
    user_id: str
    tmdb_id: int
    media_type: str    # movie/tv
    title: str
    release_date: date
    status: str        # want_to_watch/watched/watching
    created_at: datetime

# 工单系统
class Ticket(Model):
    user_id: str
    title: str
    description: str
    category: str      # request/issue/suggestion
    priority: str      # low/medium/high/urgent
    status: str        # open/in_progress/completed/rejected
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime

class TicketComment(Model):
    ticket_id: str
    user_id: str
    content: str
    created_at: datetime

# 积分系统
class PointsAccount(Model):
    user_id: str
    balance: int
    total_earned: int
    total_spent: int

class PointsTransaction(Model):
    user_id: str
    amount: int        # 正=赚，负=花
    reason: str
    created_at: datetime

class DailyCheckin(Model):
    user_id: str
    checkin_date: date
    streak: int        # 连续天数
    points_earned: int

# 媒体管理
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

# 去重策略
class DedupStrategy(Model):
    name: str
    description: str
    keep_rule: str      # highest_quality/smallest/newest
    auto_delete: bool   # False = 只标记不删除
    is_active: bool
    created_at: datetime

# 海报模板
class PosterTemplate(Model):
    name: str
    thumbnail_url: str
    template_json: dict  # 布局配置
    is_active: bool
```

---

## 四、前端路由结构

```
/dashboard              概览仪表盘
/users                  用户列表
/users/:id              用户详情
/users/invites          邀请管理
/users/invite/create    创建邀请
/analytics              数据分析(默认: 用户数据)
/analytics/users        用户数据
/analytics/media        媒体排行
/analytics/quality      质量分析
/calendar               追剧日历
/media                  媒体库
/media/duplicates       去重管理
/media/missing          缺集管理
/risk                   风控天眼
/tasks                  任务中心
/tickets                工单大厅
/tickets/:id            工单详情
/points                 积分系统
/notifications          通知中心
/poster                 海报工坊
/settings               系统设置(多 Tab)
```

---

## 五、前端 TabBar 适配

现有 5 个 tab + "更多"面板。需要扩展：

```
Tab Bar (移动端 5 tab):
├── 概览 (Dashboard)
├── 用户 (Users)
├── 分析 (Analytics)   ← 原"统计"改名
├── 媒体 (Media)       ← 新增，替代原"风控"
└── 更多 (More)
    ├── 风控天眼
    ├── 追剧日历
    ├── 任务中心
    ├── 工单大厅
    ├── 积分系统
    ├── 海报工坊
    ├── 通知中心
    ├── 系统设置
    ├── 切换主题
    └── 退出登录

Sidebar (桌面端):
├── 概览
├── 用户管理
│   ├── 用户列表
│   └── 邀请管理
├── 数据分析
│   ├── 用户数据
│   ├── 媒体排行
│   └── 质量分析
├── 媒体库
│   ├── 媒体管理
│   ├── 去重管理
│   └── 缺集管理
├── 追剧日历
├── 风控天眼
├── 任务中心
├── 工单大厅
├── 积分系统
├── 海报工坊
├── 通知中心
└── 系统设置
```

---

## 六、开发优先级排序（Phase 规划）

### Phase 1: 用户管理增强（最核心）
- [ ] 邀请码系统（生成/管理/注册流程）
- [ ] 权限模板 CRUD
- [ ] 手动创建用户
- [ ] 用户详情增强（库权限编辑 + 高级策略配置）
- [ ] 用户级并发限制

### Phase 2: Analytics 重构
- [ ] 观看历史页面（全站 + 按用户筛选）
- [ ] 24H 观影生物钟热力图
- [ ] 设备/软件分布图
- [ ] 多维度排行（热度/时长/用户）
- [ ] 质量分析

### Phase 3: 媒体管理
- [ ] 缺集扫描 + TMDB 比对
- [ ] 去重引擎（TMDB 分组 + 质量评分 + 策略配置）
- [ ] 媒体库浏览页面

### Phase 4: 社区功能
- [ ] 追剧日历（TMDB 日历数据 + 月视图）
- [ ] 工单大厅（求片/反馈）
- [ ] 积分引擎（签到 + 流水 + 商城）

### Phase 5: 通知与自动化
- [ ] 多通道推送配置（飞书/Telegram/企微/Bark）
- [ ] 推送场景总控
- [ ] 机器人指令交互
- [ ] 任务中心（自定义任务 + 定时调度）

### Phase 6: 高级功能
- [ ] 海报工坊（模板 + 数据生成）
- [ ] 系统设置完善（权限模板管理/备份恢复）
- [ ] WebSocket 实时推送

---

## 七、Emby Pulse 缺点分析与我们的改进

| Emby Pulse 缺点 | 我们的改进 |
|-----------------|-----------|
| 去重可能误删 | 必须预览+确认，默认进回收站，7天后才永久删除 |
| 设置项散布在 compose | Compose 只管基础环境变量，所有配置在 Web UI |
| 数据统计一个长页面 | Tab 分区 + 可折叠，不堆砌 |
| 通知通道不够灵活 | 场景×通道矩阵，每个场景可单独配置推到哪些通道 |
| 缺少工单系统 | 独立工单大厅，用户求片+问题反馈 |
| 缺少积分体系 | 完整积分引擎，可兑换 VIP/权限 |
| 邀请码功能单一 | 支持批量生成、权限模板继承、使用限制 |
| 没有质量分析 | 分辨率/编码/码率/音轨全面分析 |

---

**下一步：** 等图图看完 Emby Pulse 后反馈 → 整合调整 → 按 Phase 开始开发
