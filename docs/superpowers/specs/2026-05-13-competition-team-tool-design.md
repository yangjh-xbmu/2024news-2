# 竞赛组队工具 — 设计方案

## 概述

面向在校学生的学科竞赛组队工具。解决两个核心问题：学生不知道有什么比赛可以参加，以及有比赛但找不到队友。移动端 Web 应用，Next.js 全栈，SQLite 本地数据库。

## 目标用户

单校在校学生（架构预留多校扩展）。通过微信登录使用。

## 核心功能（MVP）

1. **发现比赛** — 浏览、搜索、按分类筛选竞赛信息
2. **组队招募** — 队长发布招募帖，队员浏览并申请加入
3. **个人资料** — 维护学校、专业、技能标签等基础信息

## 技术选型

| 层 | 选择 | 说明 |
|---|------|------|
| 框架 | Next.js 15 App Router | Server Components + API Routes |
| 数据库 | SQLite (better-sqlite3) | 零配置单文件，后续可迁 PostgreSQL |
| ORM | Drizzle | 轻量类型安全，SQLite 原生支持好 |
| 设计系统 | Ant Design Mobile | 移动端原生组件，中文文档一流 |
| 样式 | Tailwind CSS + antd-mobile | 页面布局用 Tailwind，组件用 antd-mobile |
| 认证 | 微信 OAuth 2.0 | 公众号/开放平台网页授权 |
| 测试 | Vitest + Playwright | 单元 + E2E |
| 部署 | VPS 直接运行 | 不用 Docker |

## 数据模型

5 张表，SQLite + Drizzle ORM。JSON 字段用 TEXT 存储，应用层解析。

### users
```
id, wechat_openid(unique), nickname, avatar_url,
school, major, grade, skills(TEXT/JSON), bio, created_at
```

### competitions
```
id, title, category, description, organizer,
registration_deadline, competition_date, url,
status(upcoming/ongoing/ended), created_by(FK users),
is_verified, created_at
```

### recruitments
```
id, competition_id(FK competitions), creator_id(FK users),
title, description, team_name, required_roles(TEXT/JSON),
team_size, deadline, status(open/closed), created_at
```

### recruitment_applications
```
id, recruitment_id(FK recruitments), applicant_id(FK users),
message, status(pending/accepted/rejected), created_at
```

### competition_contributions（v2 启用）
```
id, competition_id(FK competitions, nullable),
contributor_id(FK users), suggested_data(TEXT/JSON),
status(pending/approved/rejected), admin_note, created_at
```

## 页面结构

底部 3 Tab 导航：发现比赛 / 组队广场 / 我的。共 6 个核心页面。

| 路由 | 页面 | 渲染方式 |
|------|------|---------|
| `/` | 比赛列表（搜索 + 分类筛选） | Server Component |
| `/competitions/[id]` | 比赛详情 + 关联招募帖 | Server Component |
| `/recruitment` | 招募广场 | Server Component |
| `/recruitment/[id]` | 招募详情 | Server Component |
| `/recruitment/new` | 发布招募表单 | Client Component |
| `/profile` | 个人中心 + 资料编辑 | Client Component |

## API Routes（10 个端点）

### 认证
- `POST /api/auth/wechat/callback` — 微信 OAuth 回调，签发 session
- `POST /api/auth/logout` — 退出登录

### 比赛
- `GET /api/competitions` — 列表（`?q=&category=&status=`）
- `GET /api/competitions/[id]` — 详情 + 关联招募帖
- `POST /api/competitions` — 管理员新增（MVP: 简单 token 鉴权）

### 招募
- `GET /api/recruitments` — 列表（`?competition_id=&status=`）
- `GET /api/recruitments/[id]` — 详情
- `POST /api/recruitments` — 发布招募（需登录）
- `PATCH /api/recruitments/[id]` — 关闭招募（仅队长）
- `POST /api/recruitments/[id]/apply` — 申请加入（需登录）

### 用户
- `GET /api/users/me` — 当前用户信息
- `PATCH /api/users/me` — 更新资料

## 组件架构

```
components/
├── ui/                        # 通用 UI 组件
│   ├── SearchBar.tsx          # 搜索框（防抖）
│   ├── FilterTabs.tsx         # 横向滚动筛选标签
│   ├── BottomSheet.tsx        # 底部弹出面板
│   ├── EmptyState.tsx         # 空状态占位
│   ├── LoadingSkeleton.tsx    # 骨架屏
│   └── Avatar.tsx             # 用户头像
├── features/                  # 业务组件
│   ├── CompetitionCard.tsx    # 比赛卡片
│   ├── CompetitionDetail.tsx  # 比赛详情主体
│   ├── RecruitmentCard.tsx    # 招募卡片
│   ├── RecruitmentDetail.tsx  # 招募详情主体
│   ├── ApplicationButton.tsx  # 申请按钮（含状态机）
│   ├── UserProfileForm.tsx    # 个人资料表单
│   └── WechatLoginButton.tsx  # 微信登录按钮
└── layout/
    ├── MobileShell.tsx        # 移动端壳
    └── TabBar.tsx             # 底部导航
```

## 渲染策略

- **Server Components**（默认）：比赛列表/详情、招募广场/详情，直接读 SQLite，无 API 中转
- **Client Components**（交互）：搜索框、筛选标签、表单、登录按钮、申请按钮
- **API Routes**（写操作）：发布招募、申请入队、编辑资料

## 错误处理

三层兜底：

- **API 层**：try-catch → 返回 `{ error, message }`
- **页面级**：Next.js `error.tsx` 边界 + 重试按钮
- **全局**：`global-error.tsx` 兜底

P0 边界情况：微信授权失败、未登录点击申请、招募已关闭、重复申请、空列表、首次启动无 DB 文件。

## 测试策略

| 类型 | 工具 | 优先级 |
|------|------|--------|
| 数据库 Schema 测试 | Vitest + 内存 SQLite | P0 |
| API Route 测试 | Vitest | P0 |
| 关键流程 E2E | Playwright | P1 |
| 组件测试 | Vitest + Testing Library | P2 |

## MVP 不做（YAGNI）

- 后台管理系统
- 消息通知系统
- 智能匹配算法
- 用户贡献比赛信息 UI（表已建，v2 启用）
- 跨校切换/多校数据隔离
- CI/CD 流水线
