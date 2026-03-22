# Emby Next Gen Console — 功能对比与开发计划

## 一、当前项目状态

### ✅ 已实现（基本可用）
| 模块 | 功能 | 状态 |
|------|------|------|
| Dashboard | 总览/播放/会话/风控/通知卡片 | ✅ 可用 |
| Users | 用户列表/详情/VIP管理 | ✅ 可用 |
| Invites | 邀请码系统 | ✅ 可用 |
| Templates | 权限模板 | ✅ 可用 |
| Stats | 趋势/排行/观看历史/热力图 | ✅ 可用 |
| Analytics | 设备分布/时长/热度/质量/类型 | ✅ 可用 |
| Calendar | 月视图/周瀑布流/Emby同步 | ✅ 可用 |
| Media | 媒体库/TMDB搜索 | ⚠️ 缺集检测用本地表，可能没数据 |
| Risk | 事件列表/处理 | ⚠️ 只能记录，不能踢出/封禁 |
| Notifications | 通知列表/标记已读 | ⚠️ 规则引擎未实现 |
| Portal | Emby用户登录/个人中心 | ✅ 可用 |
| Tasks | 任务列表/取消 | ⚠️ 没有实际执行能力 |
| Poster | 海报模板/生成 | ⚠️ 只有框架 |
| Webhook | 接收Emby事件 | ✅ 基础可用 |
| System | 设置/健康检查 | ✅ 可用 |
| Auth | JWT认证 | ✅ 可用 |

### ❌ 缺失功能

| 功能 | Emby Pulse | 我们 | 优先级 |
|------|-----------|------|--------|
| **风控执法：踢出播放** | ✅ POST /Sessions/{id}/Playing/Stop | ❌ | 🔴 高 |
| **风控执法：封禁用户** | ✅ POST /Users/{id}/Policy | ❌ | 🔴 高 |
| **成就徽章系统** | ✅ 深夜修仙/肝帝等 | ❌ | 🟡 中 |
| **智能名称清洗** | ✅ 提取系列名+季数 | ❌ | 🟡 中 |
| **缺集检测（TMDB对比）** | ✅ 用 TMDB API 逐集对比 | ❌ 只查本地 | 🔴 高 |
| **重复媒体检测** | ✅ Emby Items API | ⚠️ 基础可用 | 🟢 低 |
| **客户端黑名单** | ✅ 客户端管理/封禁 | ❌ | 🟡 中 |
| **媒体请求系统** | ✅ 用户请求/审批流程 | ❌ 任务只有列表 | 🔴 高 |
| **通知规则引擎** | ✅ 多条件触发 | ❌ 只有通知列表 | 🟡 中 |
| **海报分享** | ✅ 融合 binge/late-night/genres | ❌ | 🟡 中 |
| **Insight 内容分析** | ✅ 质量盘点/忽略列表 | ❌ | 🟢 低 |
| **积分系统** | ✅ 观影积分/排行榜 | ❌ | 🟢 低 |
| **时区处理** | ✅ localtime + UTC+8 | ❌ UTC | 🟡 中 |

---

## 二、Emby API 数据获取模式参考

### Playback Reporting 插件 SQL 接口
```
POST {EMBY_HOST}/emby/user_usage_stats/submit_custom_query
Headers: X-Emby-Token: {API_KEY}
Body: {"CustomQueryString": "SELECT ... FROM PlaybackActivity"}
响应: {"colums": [...], "results": [[...], ...]}  ← 注意 colums 拼写
```

### 常用 Emby API
```python
# 用户管理
GET  /emby/Users                          # 用户列表
GET  /emby/Users/{id}                     # 用户详情
POST /emby/Users/{id}/Policy              # 修改用户策略（封禁等）

# 会话控制
GET  /emby/Sessions                       # 活跃会话
POST /emby/Sessions/{id}/Playing/Stop     # 踢出播放

# 媒体库
GET  /emby/Library/VirtualFolders         # 媒体库列表
GET  /emby/Users/{id}/Views               # 用户视图
GET  /emby/Items?includeItemTypes=...     # 查询项目
GET  /emby/Items/{id}                     # 单个项目详情
GET  /emby/Items/Counts                   # 各类型数量

# 设备
GET  /emby/Devices                        # 设备列表

# 系统
GET  /emby/System/Info/Public             # 系统信息
GET  /emby/System/ActivityLog/Entries     # 活动日志
```

### TMDB API（缺集检测用）
```
GET https://api.themoviedb.org/3/tv/{tmdb_id}?language=zh-CN&api_key={key}
GET https://api.themoviedb.org/3/tv/{tmdb_id}/season/{num}?language=zh-CN&api_key={key}
```

---

## 三、下一步开发计划

### Phase 8: 风控增强（立即需要）
1. **踢出播放** — POST /emby/Sessions/{session_id}/Playing/Stop
2. **封禁用户** — POST /emby/Users/{user_id}/Policy 设置 IsDisabled=True
3. **解封用户** — 同上，IsDisabled=False
4. **风控日志表** — 记录所有执法操作
5. 前端：Risk 页面加「踢出」「封禁」「解封」按钮

### Phase 9: 缺集检测（TMDB 对比）
1. 从 Emby 获取所有 Series + ProviderIds.Tmdb
2. 逐个调 TMDB API 获取完整季/集列表
3. 与本地 Emby 库对比，找出缺失的集
4. 前端：Media 页面「缺集检测」Tab 显示缺失列表

### Phase 10: 媒体请求系统
1. 用户提交请求（TMDB 搜索 → 选择 → 提交）
2. 管理员审批/拒绝流程
3. 状态管理（pending/approved/rejected/completed）
4. 前端：Tasks 页面完整 CRUD

### Phase 11: 客户端管理
1. 设备列表（从 /emby/Devices 获取）
2. 客户端黑名单（封禁特定 app）
3. 播放拦截（webhook 检查黑名单客户端）
4. 前端：Settings 增加「客户端管理」Tab

### Phase 12: 通知规则引擎
1. 定义触发条件（事件类型 + 用户 + 时间 + 阈值）
2. 定义动作（发通知/踢出/封禁）
3. 规则评估引擎
4. 前端：Notifications 规则配置 UI

### Phase 13: 趣味功能
1. 成就徽章系统（深夜修仙/周末狂欢/核心肝帝/带薪观影）
2. 智能名称清洗（提取系列名+季数）
3. 时区修复（UTC → localtime）
4. 海报分享数据

---

## 四、技术要点

### 数据流
```
Emby Webhook → WebhookService → EventBus → 各模块
Emby API (query_playback_stats) → Playback Reporting 插件 SQL
Emby API (标准接口) → 用户/会话/媒体库/设备
TMDB API → 缺集检测/搜索
本地 PostgreSQL → playback_events/calendar_entries/risk_events
```

### 关键文件
- `backend/app/core/emby.py` — Emby API 适配器
- `backend/app/core/emby_data.py` — 统一数据接口（API/SQLite 自动路由）
- `backend/app/modules/*/service.py` — 各模块业务逻辑
- `backend/app/modules/*/api.py` — 各模块 HTTP 端点
- `frontend/src/pages/*.vue` — 前端页面
- `frontend/src/api/*.ts` — 前端 API 客户端

### 环境变量
```
EMBY_HOST=http://your-emby:8096
EMBY_API_KEY=your-api-key
EMBY_DATA_MODE=api  # api|sqlite|auto
TMDB_API_KEY=your-tmdb-key  # 缺集检测需要
```
