# Emby Next Console API 文档

## 鉴权方式

所有 API 请求需要以下任一鉴权方式：

### 方式一：JWT Token（前端使用）

```
Authorization: Bearer <你的 JWT Token>
```

### 方式二：API Key（外部调用）

```
X-API-Key: <你的 API Key>
```

在控制台「更多 → API」中创建密钥。

---

## 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/manage/users` | 获取用户列表 |
| POST | `/api/v1/manage/users` | 创建用户 |
| GET | `/api/v1/manage/users/{user_id}` | 获取用户详情 |
| PUT | `/api/v1/manage/users/{user_id}` | 更新用户 |
| DELETE | `/api/v1/manage/users/{user_id}` | 删除用户 |
| POST | `/api/v1/manage/users/batch` | 批量操作 |

### 批量操作

```json
POST /api/v1/manage/users/batch
{
  "operation": "enable|disable|set_vip|unset_vip|delete|renew",
  "user_ids": ["user_id_1", "user_id_2"],
  "days": 30  // renew 操作时必填
}
```

---

## 风控管控

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/risk/summary` | 风控概览（待处理/高危计数） |
| GET | `/api/v1/risk/events` | 风控事件列表 |
| POST | `/api/v1/risk/events/{event_id}/action` | 处理事件（resolve/ignore） |
| GET | `/api/v1/risk/violations` | 违规记录列表 |
| POST | `/api/v1/risk/ban` | 封禁用户 |
| POST | `/api/v1/risk/unban` | 解封用户 |
| POST | `/api/v1/risk/scan` | 手动触发扫描 |
| GET | `/api/v1/risk/policy` | 获取策略配置 |
| PUT | `/api/v1/risk/policy` | 更新策略配置 |
| GET | `/api/v1/risk/blacklist` | 获取客户端黑名单 |
| POST | `/api/v1/risk/blacklist` | 添加黑名单项 |
| DELETE | `/api/v1/risk/blacklist/{name}` | 移除黑名单项 |

---

## 统计分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/stats/overview?period=30d` | 总览数据 |
| GET | `/api/v1/stats/trend?period=30d` | 播放趋势 |
| GET | `/api/v1/stats/top-content?limit=5&period=30d` | 热门内容排行 |
| GET | `/api/v1/stats/top-users?limit=5&period=30d` | 活跃用户排行 |
| GET | `/api/v1/stats/heatmap?period=30d` | 观影生物钟热力图 |
| GET | `/api/v1/stats/device-dist?type=client&period=30d` | 设备分布 |

period 参数：`7d` / `30d` / `90d` / `all`

---

## 追剧日历

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/calendar/upcoming?week_offset=0` | 获取周历 |
| POST | `/api/v1/calendar/refresh?week_offset=0` | 强制刷新 |

---

## 质量盘点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/quality/overview` | 扫描概览 |
| GET | `/api/v1/quality/items?page=1&size=25` | 媒体质量列表 |
| POST | `/api/v1/quality/scan` | 开始扫描 |
| POST | `/api/v1/quality/{item_id}/ignore` | 忽略/恢复 |

---

## 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/system/health` | 健康检查 |
| GET | `/api/v1/system/settings` | 获取配置列表 |
| GET | `/api/v1/system/sessions` | Emby 播放会话 |

---

## 推送通知

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/notify/destinations` | 获取推送目标列表 |
| POST | `/api/v1/notify/destinations` | 创建推送目标 |
| PATCH | `/api/v1/notify/destinations/{id}` | 更新推送目标 |
| DELETE | `/api/v1/notify/destinations/{id}` | 删除推送目标 |
| POST | `/api/v1/notify/destinations/{id}/test` | 发送测试通知 |
| GET | `/api/v1/notify/events` | 获取支持的事件类型 |

---

## Webhook（接收 Emby 事件）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/webhook/emby?token=xxx` | 接收 Emby Webhook |

---

## 调用示例

```bash
# 获取用户列表
curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/manage/users

# 创建用户
curl -X POST -H "X-API-Key: enc_xxx" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","password":"123456","max_concurrent":2}' \
  https://your-host/api/v1/manage/users

# 获取风控概览
curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/risk/summary

# 获取统计总览
curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/stats/overview?period=30d

# 获取周历
curl -H "X-API-Key: enc_xxx" https://your-host/api/v1/calendar/upcoming
```
