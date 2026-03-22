# Analytics 重构实现报告

## 已完成的任务

### 1. 修改的文件

1. **app/modules/stats/schemas.py**
   - 添加了 8 个新的 Pydantic 模型用于 analytics 端点：
     - `WatchHistoryItem`, `WatchHistoryResponse`
     - `ClockHeatmapResponse`
     - `DeviceDistributionItem`
     - `GenrePreferenceItem`
     - `HotRankItem`
     - `DurationRankItem`
     - `UserRankItem`
     - `QualityAnalysisResponse`

2. **app/modules/stats/api.py**
   - 添加了新的 `analytics_router = APIRouter(prefix="/admin/analytics", tags=["analytics"])`
   - 实现了 8 个新的 analytics 端点：
     - `GET /admin/analytics/watch-history` - 观看历史
     - `GET /admin/analytics/clock-24h` - 24H 生物钟热力图
     - `GET /admin/analytics/device-dist` - 设备分布
     - `GET /admin/analytics/genre-preference` - 类型偏好
     - `GET /admin/analytics/hot-rank` - 热度排行
     - `GET /admin/analytics/duration-rank` - 时长排行
     - `GET /admin/analytics/user-rank` - 用户排行
     - `GET /admin/analytics/quality` - 质量分析
   - 所有端点都包含适当的参数验证和默认值

3. **app/modules/stats/service.py**
   - 添加了 8 个新的分析方法到 `StatsService` 类：
     - `get_watch_history()` - 从 `playback_events` 表获取观看历史
     - `get_clock_heatmap()` - 使用 SQL 查询构建 24x7 热力图
     - `get_device_distribution()` - 统计设备分布
     - `get_genre_preference()` - 类型偏好（当前返回空列表，因 genres 字段不存在）
     - `get_hot_rank()` - 热度排行（播放次数 + 唯一用户数）
     - `get_duration_rank()` - 时长排行（总播放时长）
     - `get_user_rank()` - 用户排行（连接 users 表）
     - `get_quality_analysis()` - 质量分析（返回占位数据，因分辨率/转码信息不存在）
   - 所有方法都包含适当的错误处理

4. **app/main.py**
   - 添加了 `analytics_router` 的导入
   - 注册了 analytics_router：`app.include_router(analytics_router, prefix=API_PREFIX)`

### 2. 实现细节

#### 数据库查询
- 使用 SQLAlchemy 的 `text()` 函数处理复杂 SQL 查询
- 使用 `PlaybackEvent` 模型进行 ORM 查询（用于观看历史）
- 所有查询都包含时间过滤（`days` 参数）
- 支持分页（观看历史端点）

#### 错误处理
- 所有方法都包含 try-except 块
- 记录错误日志到 `app.stats` logger
- 返回合理的空值而不是抛出异常

#### 参数验证
- 所有端点参数都有合理的默认值
- 使用 FastAPI 的 `Query` 进行参数验证
- 范围限制：`ge=1, le=365` 用于 days 参数，`ge=1, le=100` 用于 limit 参数

### 3. 注意事项

1. **缺失字段处理**：
   - `genres` 字段不存在于 `playback_events` 表中，因此 `get_genre_preference()` 返回空列表
   - 分辨率/转码信息不存在，因此 `get_quality_analysis()` 返回占位数据

2. **数据库表**：
   - 使用了现有的 `playback_events` 表而不是 `playback_sessions` 表
   - `playback_events` 表包含更完整的播放历史数据

3. **用户连接**：
   - `get_user_rank()` 方法通过 `LEFT JOIN` 连接 `users` 表获取用户名
   - 其他方法中的用户名字段为 `None`，需要时可通过类似方式添加

### 4. API 端点详情

所有 analytics 端点都位于 `/api/v1/admin/analytics/` 前缀下：

1. **GET /watch-history**
   - 参数：`user_id` (可选), `page` (默认1), `page_size` (默认20), `days` (默认30)
   - 返回：分页的观看历史记录

2. **GET /clock-24h**
   - 参数：`days` (默认30), `user_id` (可选)
   - 返回：24x7 二维数组（小时 x 星期）

3. **GET /device-dist**
   - 参数：`days` (默认30)
   - 返回：设备分布列表

4. **GET /genre-preference**
   - 参数：`days` (默认30), `user_id` (可选)
   - 返回：类型偏好列表（当前为空）

5. **GET /hot-rank**
   - 参数：`days` (默认30), `limit` (默认20)
   - 返回：热度排行（播放次数 + 唯一用户数）

6. **GET /duration-rank**
   - 参数：`days` (默认30), `limit` (默认20)
   - 返回：时长排行（总播放时长）

7. **GET /user-rank**
   - 参数：`days` (默认30), `limit` (默认20)
   - 返回：用户排行（连接 users 表）

8. **GET /quality**
   - 参数：`days` (默认30)
   - 返回：质量分析（分辨率分布 + 转码率）

### 5. 测试验证
- 所有 Python 文件语法正确
- 导入结构有效
- 代码符合项目现有风格

## 下一步建议

1. **数据库迁移**：如果需要 `genres` 字段，可以添加数据库迁移
2. **Emby API 集成**：对于缺失的数据（如分辨率、转码信息），可以集成 Emby API
3. **性能优化**：对于大数据集，考虑添加数据库索引
4. **缓存**：考虑为 analytics 数据添加缓存机制