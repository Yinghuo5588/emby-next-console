# 前端重构方案

## 现状问题

- 各页面风格不统一，早期页面是拼凑的
- 缺少统一的设计语言（间距、字体层级、颜色语义不一致）
- 卡片和表格布局单调，缺少视觉层次
- 日历、统计、风控等核心页面没有充分利用数据可视化
- 海报和封面图用得太少，视觉冲击力弱
- 移动端适配粗糙

## 设计方向：「Plex 风」暗色媒体控制台

参考 Plex / Emby 原生风格：**暗底 + 海报优先 + 卡片浮动 + 丰富的数据可视化**

### 设计语言

| 元素 | 规范 |
|------|------|
| 主题 | 深色为主，浅色可选 |
| 背景 | `#0d0d0d`（极深灰），卡片 `#1a1a1a` |
| 强调色 | 蓝 `#2563eb`，绿成功 `#22c55e`，红危险 `#ef4444`，黄警告 `#f59e0b` |
| 字体 | Inter / SF Pro，标题 24/20/16px，正文 14px，辅助 12px |
| 圆角 | 卡片 12px，按钮 8px，标签 6px |
| 阴影 | 卡片 `0 2px 8px rgba(0,0,0,0.3)`，悬浮 `0 8px 24px rgba(0,0,0,0.4)` |
| 间距 | 8px 基准网格（8/16/24/32） |
| 动效 | 卡片悬浮上浮，列表滑入，骨架屏加载 |

### 布局重构

- **侧边栏**：固定 64px 图标栏（收起态）+ 可展开 240px（展开态），悬停展开
- **顶栏**：面包屑 + 搜索 + 用户头像 + 暗/亮切换
- **内容区**：max-width 1440px 居中，响应式网格
- **移动端**：底部 Tab 5 个核心入口 + 更多抽屉

### 页面重构优先级

#### Phase 1：核心视觉改造（最高优先）
1. **Dashboard** — 重新设计为信息密度更高的仪表盘
   - 大数字卡片（渐变背景）+ 趋势图 + 实时会话列表（带头像）+ 快捷操作
2. **日历** — Trakt 风格（已完成 ✅）
3. **统计** — 卡片式数据可视化，丰富图表

#### Phase 2：管理页面
4. **用户列表** — 头像 + 标签 + 状态指示灯
5. **风控** — 实时监控仪表盘风格
6. **通知** — 时间线风格

#### Phase 3：辅助页面
7. **设置** — 分组卡片式设置
8. **任务** — 任务看板风格
9. **媒体库** — 海报瀑布流

### 技术方案

**不引入新的 UI 框架**，保持当前 Vue 3 + TypeScript + Pinia 技术栈：
- 重写 `global.css` 设计系统
- 新增 CSS 变量 + 工具类
- 使用 CSS Grid 替代大部分 flex 布局
- 新增骨架屏组件、动画工具
- 图表保持 ECharts（TrendChart / HeatmapChart）

### 文件变更范围

```
改动:
  src/styles/global.css          ← 重写设计系统
  src/layouts/DefaultLayout.vue  ← 侧边栏收起态 + 顶栏
  src/components/common/AppSidebar.vue ← 图标栏 + 展开
  src/components/common/PageHeader.vue ← 统一改版
  src/components/common/StatCard.vue   ← 渐变背景大数字
  src/components/common/TabBar.vue     ← 移动端改版
  src/pages/DashboardPage.vue   ← 完全重写
  src/pages/StatsPage.vue       ← 重写（已有数据支撑）
  src/pages/UsersPage.vue       ← 头像卡片风格
  src/pages/RiskPage.vue        ← 仪表盘风格
  src/pages/NotificationsPage.vue← 时间线风格
  src/pages/SettingsPage.vue    ← 分组卡片
  src/pages/TasksPage.vue       ← 看板风格

新增:
  src/components/common/SkeletonLoader.vue
  src/components/common/AnimatedNumber.vue
  src/components/dashboard/SessionCard.vue
  src/components/dashboard/QuickActions.vue
  src/components/stats/StatOverviewCard.vue

不改:
  src/api/*                     ← 不动（功能已对）
  src/pages/LoginPage.vue       ← 不动
  src/pages/portal/*            ← 不动
  src/pages/CalendarPage.vue    ← 已完成
  src/components/calendar/*     ← 已完成
```

### 开发顺序

1. `global.css` 设计系统（颜色/字体/间距/动画基础）
2. `DefaultLayout` + `AppSidebar` + `PageHeader` 改版
3. `StatCard` + `SkeletonLoader` + `AnimatedNumber` 组件
4. `DashboardPage` 完全重写
5. `StatsPage` 重写
6. 其余管理页面依次改版
