# Emby Next Gen Console

Emby 媒体管理控制台 — 独立部署，FastAPI + Vue 3。

## 快速启动

```bash
# 创建 .env 文件
cat > .env << 'EOF'
SECRET_KEY=your-secret-key
EMBY_HOST=http://your-emby-host:8096
EMBY_API_KEY=your-api-key
EMBY_DATA_MODE=api
EOF

# 启动
docker compose pull && docker compose up -d
```

访问 `http://localhost:3000`，默认登录：`admin` / `admin`

## 前置条件

- Emby Server 4.x+
- **必须安装 Playback Reporting 插件**（统计/分析功能依赖此插件的 SQL 查询接口）
- Emby API Key（在 Emby 后台 → API Keys 生成）

## 架构

```
backend/                         # FastAPI 后端
├── app/
│   ├── core/
│   │   ├── emby.py              # Emby API 适配器 (HTTPX 异步)
│   │   ├── emby_db.py           # SQLite 直读（同机部署用）
│   │   ├── emby_data.py         # 统一数据接口，自动路由 API/SQLite
│   │   ├── settings.py          # Pydantic 配置
│   │   └── ...
│   ├── db/
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   │   ├── playback.py      # PlaybackEvent + PlaybackSession
│   │   │   ├── calendar.py      # CalendarEntry
│   │   │   ├── risk.py          # RiskEvent
│   │   │   ├── notification.py  # Notification
│   │   │   ├── invite.py        # InviteCode + PermissionTemplate
│   │   │   └── ...
│   │   └── session.py           # AsyncSession 工厂
│   ├── modules/                 # 各功能模块（每个模块含 api + service + schemas）
│   │   ├── dashboard/           # 仪表盘（总览/播放/会话/风控/通知）
│   │   ├── users/               # 用户管理（列表/详情/VIP/邀请码）
│   │   ├── invites/             # 邀请码系统
│   │   ├── templates/           # 权限模板
│   │   ├── stats/               # 统计分析（趋势/排行/观看历史）
│   │   ├── risk/                # 风控系统（规则引擎/事件管理）
│   │   ├── calendar/            # 追剧日历（月视图/周瀑布流/Emby 同步）
│   │   ├── media/               # 媒体管理（发现/搜索/重复检测/缺集检测）
│   │   ├── notifications/       # 通知系统（规则/模板/渠道/历史）
│   │   ├── portal/              # 用户门户（Emby 用户自助登录）
│   │   ├── tasks/               # 任务中心（媒体请求管理）
│   │   ├── poster/              # 海报工坊（模板/生成/预览）
│   │   ├── webhook/             # Webhook 处理器
│   │   ├── system/              # 系统管理（设置/健康检查）
│   │   └── auth/                # 认证模块
│   └── main.py                  # FastAPI 入口
└── alembic/                     # 数据库迁移

frontend/                        # Vue 3 + Vite 前端
├── src/
│   ├── api/                     # API 客户端（17 个模块）
│   ├── pages/                   # 页面组件（16 个页面）
│   ├── components/              # 通用组件
│   │   ├── common/              # AppSidebar, TabBar, StatCard 等
│   │   ├── calendar/            # CalendarGrid, WeekWaterfall, DayDetail
│   │   ├── charts/              # TrendChart, HeatmapChart
│   │   ├── risk/                # RiskEventsTable, RiskFilterBar
│   │   ├── users/               # UsersTable, UsersFilterBar
│   │   └── notifications/       # TemplateEditor, ChannelConfig 等
│   ├── stores/                  # Pinia 状态管理
│   ├── layouts/                 # DefaultLayout (sidebar + content + tabbar)
│   └── router/                  # Vue Router
```

## 模块详情

### Dashboard (`/admin`)
- 概览卡片：用户数/在线会话/播放量
- 播放趋势图（7/30 天）
- 实时会话列表
- 风控摘要 + 通知摘要

### 用户管理 (`/admin/users`)
- 用户列表（从 Emby API 实时拉取）
- 用户详情页（头像/播放记录/VIP 状态/邀请码）
- 邀请码管理（创建/统计/失效）
- 权限模板（批量应用权限）

### 统计分析 (`/admin/stats`)
- 播放趋势（支持 7/14/30 天）
- 热门用户/媒体排行
- 观看历史（分页）
- 生物钟热力图（24x7 网格）
- 设备分布
- 类型偏好（从 Emby API 查询 genres）
- 质量分析（分辨率分布 + 转码率）
- 时长排行

### 追剧日历 (`/admin/calendar`)
- 月视图：日历网格，每格显示更新剧集
- 周视图：7 列瀑布流，按周一到周日排列
- 从 Emby 同步剧集日历（AirDate/PremiereDate/DateCreated fallback）
- 统计卡片（本月更新/未来 7 天/追踪剧集）

### 媒体管理 (`/admin/media`)
- 媒体库列表（从 Emby 获取）
- 发现：TMDB 搜索 + 即将上映
- 缺集检测（从本地数据库推断）
- 重复媒体检测

### 风控系统 (`/admin/risk`)
- 规则引擎（并发/时长/设备数/离线播放）
- 事件管理（查看详情/处理/忽略）
- 用户风控级别

### 通知系统 (`/admin/notifications`)
- 通知规则（多条件矩阵）
- 通知模板（变量替换 + 预览）
- 渠道配置（飞书/Telegram/Webhook）
- 历史记录

### 任务中心 (`/admin/tasks`)
- 媒体请求管理（状态/进度/取消）

### 海报工坊 (`/admin/poster`)
- 海报模板管理
- 生成弹窗（选模板/标题/Item IDs）
- iframe 预览

### 用户门户 (`/admin/portal`)
- Emby 用户自助登录
- 个人中心（播放统计/日历）

### 系统设置 (`/admin/settings`)
- Emby 配置
- 系统参数

## Emby API 数据模式

通过 `EMBY_DATA_MODE` 环境变量控制：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `api` | 全部通过 Emby HTTP API | 远程部署（默认） |
| `sqlite` | 直接读 Emby SQLite 数据库 | 同机部署 |
| `auto` | 自动检测，DB 不可用时回退 API | 推荐 |

**Playback Reporting 插件 SQL 接口：**
```
POST {EMBY_HOST}/emby/user_usage_stats/submit_custom_query
Header: X-Emby-Token: {API_KEY}
Body: {"CustomQueryString": "SELECT ... FROM PlaybackActivity"}
```
响应格式：`{"colums": [...], "results": [[...], ...]}`（注意 `colums` 拼写）

## 数据库模型

| 表 | 说明 |
|----|------|
| `users` | 本地用户缓存 |
| `playback_events` | 播放事件（从 webhook 写入） |
| `playback_sessions` | 活跃播放会话 |
| `calendar_entries` | 追剧日历条目 |
| `risk_events` | 风控事件 |
| `notifications` | 通知记录 |
| `invite_codes` | 邀请码 |
| `permission_templates` | 权限模板 |
| `webhook_events` | Webhook 原始事件 |

## 仓库结构

```
GitHub: https://github.com/Yinghuo5588/emby-next-console
分支: main
CI: GitHub Actions (backend test + frontend build)
镜像: ghcr.io/yinghuo5588/emby-next-console-backend:latest
      ghcr.io/yinghuo5588/emby-next-console-frontend:latest
```

## 已知限制

- Genre 偏好：逐条搜索 Emby API，性能一般（可优化为批量查询）
- 缺集检测：依赖本地 `playback_sessions` 表，需要 webhook 写入数据
- 用户门户：JWT 密钥建议 >= 32 字节
