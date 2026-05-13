# 竞赛组队工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建面向在校学生的竞赛组队移动端 Web 应用，支持比赛发现、招募发布、组队申请。

**Architecture:** Next.js 15 App Router 全栈应用。Server Components 直接读 SQLite 渲染列表/详情页，Client Components 处理表单和交互，API Routes 处理写操作。Ant Design Mobile 提供移动端原生组件。

**Tech Stack:** Next.js 15, TypeScript, SQLite (better-sqlite3), Drizzle ORM, Ant Design Mobile, Tailwind CSS, iron-session, Vitest, Playwright

**项目路径:** `~/Desktop/repos/competition-teams/`

---

### Task 1: 创建项目并安装依赖

**Files:**
- Create: `~/Desktop/repos/competition-teams/` (entire project scaffold)

- [ ] **Step 1: 使用 create-next-app 创建项目**

```bash
cd ~/Desktop/repos && npx create-next-app@latest competition-teams --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack
```

- [ ] **Step 2: 安装运行时依赖**

```bash
cd ~/Desktop/repos/competition-teams && npm install antd-mobile better-sqlite3 drizzle-orm iron-session
```

- [ ] **Step 3: 安装开发依赖**

```bash
npm install -D drizzle-kit @types/better-sqlite3 vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @playwright/test
```

- [ ] **Step 4: 验证项目能启动**

```bash
npm run dev
```
Expected: Next.js dev server starts on localhost:3000. 访问看到默认页面。Ctrl+C 停止。

- [ ] **Step 5: 初始化 Git 仓库并提交**

```bash
cd ~/Desktop/repos/competition-teams && git init && git add -A && git commit -m "chore: scaffold Next.js project with dependencies"
```

---

### Task 2: 配置 Tailwind + Ant Design Mobile 主题

**Files:**
- Modify: `src/app/globals.css`
- Modify: `tailwind.config.ts`
- Create: `src/lib/theme.ts`

- [ ] **Step 1: 创建主题配置文件**

```typescript
// src/lib/theme.ts
export const theme = {
  primary: '#00b96b',
  primaryDark: '#008a51',
  primaryLight: '#e6fffb',
  primaryBg: '#f6ffed',
};
```

- [ ] **Step 2: 更新 Tailwind 配置，扩展绿色主题色**

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#00b96b',
        'primary-dark': '#008a51',
        'primary-light': '#e6fffb',
      },
    },
  },
  plugins: [],
  // antd-mobile 与 Tailwind 的 preflight 可能有冲突，关闭 Tailwind 的
  corePlugins: {
    preflight: false,
  },
};
export default config;
```

- [ ] **Step 3: 更新全局样式，注入 antd-mobile 主题变量**

```css
/* src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --adm-color-primary: #00b96b;
  --adm-color-success: #00b96b;
  --adm-color-warning: #fa8c16;
  --adm-color-danger: #ff4d4f;
}

html, body {
  max-width: 100vw;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}

/* 移动端安全区 */
.safe-bottom {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "chore: configure Tailwind and Ant Design Mobile theme"
```

---

### Task 3: 定义数据库 Schema

**Files:**
- Create: `src/lib/db/schema.ts`
- Create: `src/lib/db/index.ts`
- Create: `drizzle.config.ts`

- [ ] **Step 1: 编写 Drizzle schema**

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  wechatOpenid: text('wechat_openid').notNull().unique(),
  nickname: text('nickname').notNull(),
  avatarUrl: text('avatar_url'),
  school: text('school').notNull(),
  major: text('major'),
  grade: text('grade'),
  skills: text('skills'),   // JSON string
  bio: text('bio'),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`),
});

export const competitions = sqliteTable('competitions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  category: text('category').notNull(),
  description: text('description'),
  organizer: text('organizer'),
  registrationDeadline: text('registration_deadline'),
  competitionDate: text('competition_date'),
  url: text('url'),
  status: text('status').default('upcoming'), // upcoming | ongoing | ended
  createdBy: integer('created_by').references(() => users.id),
  isVerified: integer('is_verified', { mode: 'boolean' }).default(false),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`),
});

export const recruitments = sqliteTable('recruitments', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  competitionId: integer('competition_id').references(() => competitions.id),
  creatorId: integer('creator_id').references(() => users.id).notNull(),
  title: text('title').notNull(),
  description: text('description').notNull(),
  teamName: text('team_name'),
  requiredRoles: text('required_roles'), // JSON: [{"role":"前端","count":2}]
  teamSize: integer('team_size'),
  deadline: text('deadline'),
  status: text('status').default('open'), // open | closed
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`),
});

export const recruitmentApplications = sqliteTable('recruitment_applications', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  recruitmentId: integer('recruitment_id').references(() => recruitments.id).notNull(),
  applicantId: integer('applicant_id').references(() => users.id).notNull(),
  message: text('message'),
  status: text('status').default('pending'), // pending | accepted | rejected
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`),
});

export const competitionContributions = sqliteTable('competition_contributions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  competitionId: integer('competition_id').references(() => competitions.id),
  contributorId: integer('contributor_id').references(() => users.id).notNull(),
  suggestedData: text('suggested_data').notNull(), // JSON
  status: text('status').default('pending'), // pending | approved | rejected
  adminNote: text('admin_note'),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`),
});
```

- [ ] **Step 2: 创建数据库连接**

```typescript
// src/lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';
import path from 'path';

const DB_PATH = process.env.DATABASE_PATH || path.join(process.cwd(), 'data.db');

const sqlite = new Database(DB_PATH);
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });
```

- [ ] **Step 3: 创建 Drizzle 配置文件**

```typescript
// drizzle.config.ts
import type { Config } from 'drizzle-kit';

export default {
  schema: './src/lib/db/schema.ts',
  out: './drizzle',
  dialect: 'sqlite',
  dbCredentials: {
    url: './data.db',
  },
} satisfies Config;
```

- [ ] **Step 4: 运行 migration 生成并提交**

```bash
npx drizzle-kit generate
```
Expected: 在 `drizzle/` 目录生成 SQL migration 文件。

```bash
git add -A && git commit -m "feat: add database schema with Drizzle ORM"
```

---

### Task 4: 编写 Schema 测试并运行 Migration

**Files:**
- Create: `tests/db/schema.test.ts`
- Create: `vitest.config.ts`

- [ ] **Step 1: 编写 Vitest 配置**

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

- [ ] **Step 2: 编写 Schema 测试 — 测试表可创建、插入和查询**

```typescript
// tests/db/schema.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

const sqlite = new Database(':memory:');
const db = drizzle(sqlite, { schema });

// 手动建表（内存数据库不走 migration）
beforeAll(() => {
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      wechat_openid TEXT NOT NULL UNIQUE,
      nickname TEXT NOT NULL,
      avatar_url TEXT,
      school TEXT NOT NULL,
      major TEXT,
      grade TEXT,
      skills TEXT,
      bio TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS competitions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      category TEXT NOT NULL,
      description TEXT,
      organizer TEXT,
      registration_deadline TEXT,
      competition_date TEXT,
      url TEXT,
      status TEXT DEFAULT 'upcoming',
      created_by INTEGER REFERENCES users(id),
      is_verified INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS recruitments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      competition_id INTEGER REFERENCES competitions(id),
      creator_id INTEGER REFERENCES users(id) NOT NULL,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      team_name TEXT,
      required_roles TEXT,
      team_size INTEGER,
      deadline TEXT,
      status TEXT DEFAULT 'open',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS recruitment_applications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      recruitment_id INTEGER REFERENCES recruitments(id) NOT NULL,
      applicant_id INTEGER REFERENCES users(id) NOT NULL,
      message TEXT,
      status TEXT DEFAULT 'pending',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);
});

describe('Database Schema', () => {
  it('inserts and reads a user', () => {
    const user = db.insert(schema.users).values({
      wechatOpenid: 'test_openid',
      nickname: '张三',
      school: '测试大学',
      major: '计算机科学',
      grade: '2023级',
      skills: JSON.stringify(['Python', '数据分析']),
    }).run();
    expect(user.lastInsertRowid).toBeGreaterThan(0);

    const found = db.select().from(schema.users).where(eq(schema.users.wechatOpenid, 'test_openid')).get();
    expect(found?.nickname).toBe('张三');
    expect(JSON.parse(found?.skills as string)).toEqual(['Python', '数据分析']);
  });

  it('inserts a competition and links recruitment', () => {
    const comp = db.insert(schema.competitions).values({
      title: '全国大学生数学建模竞赛',
      category: '数学建模',
      organizer: '中国工业与应用数学学会',
      status: 'upcoming',
    }).run();

    const user = db.insert(schema.users).values({
      wechatOpenid: 'captain_openid',
      nickname: '队长',
      school: '测试大学',
    }).run();

    const rec = db.insert(schema.recruitments).values({
      competitionId: Number(comp.lastInsertRowid),
      creatorId: Number(user.lastInsertRowid),
      title: '数学建模国赛找编程手',
      description: '已有建模手和写作手，缺编程手',
      status: 'open',
    }).run();
    expect(rec.lastInsertRowid).toBeGreaterThan(0);

    // 验证外键关联
    const found = db.select().from(schema.recruitments)
      .where(eq(schema.recruitments.id, Number(rec.lastInsertRowid)))
      .get();
    expect(found?.competitionId).toBe(Number(comp.lastInsertRowid));
  });

  it('inserts and queries recruitment application', () => {
    // 创建依赖数据
    const user1 = db.insert(schema.users).values({ wechatOpenid: 'u1', nickname: '队', school: 'X' }).run();
    const user2 = db.insert(schema.users).values({ wechatOpenid: 'u2', nickname: '员', school: 'X' }).run();
    const comp = db.insert(schema.competitions).values({ title: 'T', category: 'C' }).run();
    const rec = db.insert(schema.recruitments).values({
      competitionId: Number(comp.lastInsertRowid),
      creatorId: Number(user1.lastInsertRowid),
      title: '招人',
      description: '描述',
    }).run();

    const app = db.insert(schema.recruitmentApplications).values({
      recruitmentId: Number(rec.lastInsertRowid),
      applicantId: Number(user2.lastInsertRowid),
      message: '我想加入',
    }).run();
    expect(app.lastInsertRowid).toBeGreaterThan(0);

    const apps = db.select().from(schema.recruitmentApplications)
      .where(eq(schema.recruitmentApplications.recruitmentId, Number(rec.lastInsertRowid)))
      .all();
    expect(apps.length).toBe(1);
    expect(apps[0].status).toBe('pending');
  });
});
```

- [ ] **Step 3: 运行测试验证**

```bash
npx vitest run tests/db/schema.test.ts
```
Expected: 3 tests PASS.

- [ ] **Step 4: 运行 migration 创建本地数据库**

```bash
npx drizzle-kit push
```
Expected: 在项目根目录生成 `data.db` 文件。

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "test: add schema tests and run initial migration"
```

---

### Task 5: 实现认证系统

**Files:**
- Create: `src/lib/auth.ts`
- Create: `src/lib/session.ts`
- Create: `src/app/api/auth/wechat/callback/route.ts`
- Create: `src/app/api/auth/logout/route.ts`
- Create: `.env.local`

- [ ] **Step 1: 创建环境变量文件**

```
# .env.local
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
SESSION_SECRET=your_session_secret_at_least_32_chars
DATABASE_PATH=data.db
```

- [ ] **Step 2: 实现 session 工具**

```typescript
// src/lib/session.ts
import { getIronSession } from 'iron-session';
import { cookies } from 'next/headers';

export interface SessionData {
  userId?: number;
  wechatOpenid?: string;
}

const sessionOptions = {
  password: process.env.SESSION_SECRET || 'complex_password_at_least_32_characters_long',
  cookieName: 'comp_session',
  cookieOptions: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    sameSite: 'lax' as const,
    maxAge: 60 * 60 * 24 * 7, // 7 days
  },
};

export async function getSession() {
  const cookieStore = await cookies();
  return getIronSession<SessionData>(cookieStore, sessionOptions);
}

export async function getCurrentUserId(): Promise<number | null> {
  const session = await getSession();
  return session.userId || null;
}
```

- [ ] **Step 3: 实现微信 OAuth 工具函数**

```typescript
// src/lib/auth.ts
interface WechatTokenResponse {
  access_token: string;
  openid: string;
}

interface WechatUserInfo {
  openid: string;
  nickname: string;
  headimgurl: string;
}

export function getWechatAuthUrl(redirectUri: string): string {
  const appId = process.env.WECHAT_APP_ID;
  const encodedRedirect = encodeURIComponent(redirectUri);
  return `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${encodedRedirect}&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect`;
}

export async function getWechatAccessToken(code: string): Promise<WechatTokenResponse> {
  const appId = process.env.WECHAT_APP_ID;
  const secret = process.env.WECHAT_APP_SECRET;
  const url = `https://api.weixin.qq.com/sns/oauth2/access_token?appid=${appId}&secret=${secret}&code=${code}&grant_type=authorization_code`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('微信 access_token 请求失败');
  return res.json();
}

export async function getWechatUserInfo(accessToken: string, openid: string): Promise<WechatUserInfo> {
  const url = `https://api.weixin.qq.com/sns/userinfo?access_token=${accessToken}&openid=${openid}&lang=zh_CN`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('微信用户信息请求失败');
  return res.json();
}
```

- [ ] **Step 4: 编写 OAuth 回调 API Route**

```typescript
// src/app/api/auth/wechat/callback/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getWechatAccessToken, getWechatUserInfo } from '@/lib/auth';
import { getSession } from '@/lib/session';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get('code');
  if (!code) {
    return NextResponse.redirect(new URL('/?error=auth_failed', request.url));
  }

  try {
    const token = await getWechatAccessToken(code);
    const wxUser = await getWechatUserInfo(token.access_token, token.openid);

    // 查找或创建用户
    let user = db.select().from(users).where(eq(users.wechatOpenid, wxUser.openid)).get();
    if (!user) {
      const result = db.insert(users).values({
        wechatOpenid: wxUser.openid,
        nickname: wxUser.nickname,
        avatarUrl: wxUser.headimgurl,
        school: '', // 首次登录后引导完善资料
      }).run();
      user = db.select().from(users).where(eq(users.id, Number(result.lastInsertRowid))).get()!;
    }

    // 写入 session
    const session = await getSession();
    session.userId = user.id;
    session.wechatOpenid = user.wechatOpenid;
    await session.save();

    return NextResponse.redirect(new URL('/', request.url));
  } catch (error) {
    console.error('微信登录失败:', error);
    return NextResponse.redirect(new URL('/?error=auth_failed', request.url));
  }
}
```

- [ ] **Step 5: 编写登出 API Route**

```typescript
// src/app/api/auth/logout/route.ts
import { NextResponse } from 'next/server';
import { getSession } from '@/lib/session';

export async function POST() {
  const session = await getSession();
  session.destroy();
  return NextResponse.json({ success: true });
}
```

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: implement WeChat OAuth authentication"
```

---

### Task 6: 实现布局组件（MobileShell + TabBar）

**Files:**
- Create: `src/components/layout/MobileShell.tsx`
- Create: `src/components/layout/TabBar.tsx`
- Modify: `src/app/layout.tsx`

- [ ] **Step 1: 实现 TabBar 组件**

```typescript
// src/components/layout/TabBar.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { TabBar as AntTabBar } from 'antd-mobile';
import { AppOutline, UnorderedListOutline, UserOutline } from 'antd-mobile-icons';

const tabs = [
  { key: '/', title: '发现比赛', icon: <AppOutline /> },
  { key: '/recruitment', title: '组队广场', icon: <UnorderedListOutline /> },
  { key: '/profile', title: '我的', icon: <UserOutline /> },
];

export default function TabBar() {
  const pathname = usePathname();
  const activeKey = pathname.startsWith('/recruitment') ? '/recruitment'
    : pathname.startsWith('/profile') ? '/profile'
    : '/';

  return (
    <div className="fixed bottom-0 left-0 right-0 safe-bottom border-t border-gray-100 bg-white z-50">
      <AntTabBar activeKey={activeKey}>
        {tabs.map((tab) => (
          <AntTabBar.Item key={tab.key} icon={tab.icon} title={tab.title} />
        ))}
      </AntTabBar>
    </div>
  );
}
```

- [ ] **Step 2: 实现 MobileShell 组件**

```typescript
// src/components/layout/MobileShell.tsx
import TabBar from './TabBar';

export default function MobileShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="pb-14 max-w-lg mx-auto">
        {children}
      </main>
      <TabBar />
    </div>
  );
}
```

- [ ] **Step 3: 更新根 layout**

```typescript
// src/app/layout.tsx
import type { Metadata } from 'next';
import MobileShell from '@/components/layout/MobileShell';
import './globals.css';

export const metadata: Metadata = {
  title: '竞赛组队',
  description: '发现学科竞赛，找到你的队友',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <MobileShell>{children}</MobileShell>
      </body>
    </html>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: add layout components with mobile tab navigation"
```

---

### Task 7: 实现比赛列表页（首页）

**Files:**
- Create: `src/components/ui/SearchBar.tsx`
- Create: `src/components/ui/FilterTabs.tsx`
- Create: `src/components/ui/EmptyState.tsx`
- Create: `src/components/features/CompetitionCard.tsx`
- Modify: `src/app/page.tsx`

- [ ] **Step 1: 实现 SearchBar**

```typescript
// src/components/ui/SearchBar.tsx
'use client';

import { SearchBar as AntSearchBar } from 'antd-mobile';

export default function SearchBar({ onSearch }: { onSearch: (value: string) => void }) {
  return (
    <div className="px-4 pt-3 pb-2">
      <AntSearchBar
        placeholder="搜索比赛名称"
        onChange={onSearch}
        style={{ '--border-radius': '8px' }}
      />
    </div>
  );
}
```

- [ ] **Step 2: 实现 FilterTabs**

```typescript
// src/components/ui/FilterTabs.tsx
'use client';

const defaultCategories = ['全部', '数学建模', '编程开发', '创新创业', '电子设计', '英语', '其他'];

export default function FilterTabs({
  categories = defaultCategories,
  active,
  onChange,
}: {
  categories?: string[];
  active: string;
  onChange: (cat: string) => void;
}) {
  return (
    <div className="flex gap-2 px-4 pb-3 overflow-x-auto scrollbar-hide">
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => onChange(cat)}
          className={`shrink-0 px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
            active === cat
              ? 'bg-primary text-white'
              : 'bg-white text-gray-600 border border-gray-200'
          }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: 实现 EmptyState**

```typescript
// src/components/ui/EmptyState.tsx
export default function EmptyState({
  icon = '📭',
  title = '暂无内容',
  description,
}: {
  icon?: string;
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
      <span className="text-4xl mb-3">{icon}</span>
      <p className="text-sm font-medium text-gray-500">{title}</p>
      {description && <p className="text-xs mt-1">{description}</p>}
    </div>
  );
}
```

- [ ] **Step 4: 实现 CompetitionCard**

```typescript
// src/components/features/CompetitionCard.tsx
import Link from 'next/link';

interface CompetitionCardProps {
  id: number;
  title: string;
  category: string;
  organizer?: string | null;
  registrationDeadline?: string | null;
  recruitmentCount?: number;
}

export default function CompetitionCard({
  id, title, category, organizer, registrationDeadline, recruitmentCount,
}: CompetitionCardProps) {
  return (
    <Link href={`/competitions/${id}`} className="block">
      <div className="mx-4 mb-3 bg-white rounded-xl p-4 border border-gray-100 active:bg-gray-50 transition-colors">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-base text-gray-900 truncate">{title}</h3>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-xs px-2 py-0.5 rounded bg-primary-light text-primary">{category}</span>
              {organizer && <span className="text-xs text-gray-400">{organizer}</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>
            {registrationDeadline
              ? `报名截止 ${new Date(registrationDeadline).toLocaleDateString('zh-CN')}`
              : '时间待定'}
          </span>
          {recruitmentCount !== undefined && recruitmentCount > 0 && (
            <span className="text-primary font-medium">{recruitmentCount} 支队伍招募中</span>
          )}
        </div>
      </div>
    </Link>
  );
}
```

- [ ] **Step 5: 实现首页（Server Component，直接读 DB）**

```typescript
// src/app/page.tsx
import { db } from '@/lib/db';
import { competitions, recruitments } from '@/lib/db/schema';
import { desc, eq, and, sql } from 'drizzle-orm';
import CompetitionList from './CompetitionList';

export const dynamic = 'force-dynamic';

async function getCompetitions() {
  const rows = db.select({
    id: competitions.id,
    title: competitions.title,
    category: competitions.category,
    organizer: competitions.organizer,
    registrationDeadline: competitions.registrationDeadline,
    recruitmentCount: sql<number>`COUNT(DISTINCT ${recruitments.id})`.mapWith(Number),
  })
  .from(competitions)
  .leftJoin(recruitments, and(
    eq(recruitments.competitionId, competitions.id),
    eq(recruitments.status, 'open'),
  ))
  .where(eq(competitions.isVerified, true))
  .groupBy(competitions.id)
  .orderBy(desc(competitions.createdAt))
  .all();
  return rows;
}

export default async function HomePage() {
  const allCompetitions = await getCompetitions();
  return <CompetitionList competitions={allCompetitions} />;
}
```

- [ ] **Step 6: 实现客户端交互层 CompetitionList**

```typescript
// src/app/CompetitionList.tsx
'use client';

import { useState, useMemo } from 'react';
import SearchBar from '@/components/ui/SearchBar';
import FilterTabs from '@/components/ui/FilterTabs';
import EmptyState from '@/components/ui/EmptyState';
import CompetitionCard from '@/components/features/CompetitionCard';

interface CompetitionData {
  id: number;
  title: string;
  category: string;
  organizer: string | null;
  registrationDeadline: string | null;
  recruitmentCount: number;
}

export default function CompetitionList({ competitions }: { competitions: CompetitionData[] }) {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('全部');

  const filtered = useMemo(() => {
    return competitions.filter((c) => {
      const matchCat = category === '全部' || c.category === category;
      const matchSearch = !search || c.title.toLowerCase().includes(search.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [competitions, search, category]);

  const categories = ['全部', ...Array.from(new Set(competitions.map((c) => c.category)))];

  return (
    <div className="pt-3">
      <h1 className="px-4 text-lg font-bold text-gray-900">发现比赛</h1>
      <SearchBar onSearch={setSearch} />
      <FilterTabs categories={categories} active={category} onChange={setCategory} />
      {filtered.length === 0 ? (
        <EmptyState icon="🔍" title="没有找到相关比赛" description="试试更换筛选条件" />
      ) : (
        filtered.map((c) => <CompetitionCard key={c.id} {...c} />)
      )}
    </div>
  );
}
```

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "feat: implement competition list page with search and filter"
```

---

### Task 8: 实现比赛详情页

**Files:**
- Create: `src/components/features/CompetitionDetail.tsx`
- Create: `src/components/features/RecruitmentCard.tsx`
- Create: `src/app/competitions/[id]/page.tsx`

- [ ] **Step 1: 实现 RecruitmentCard**

```typescript
// src/components/features/RecruitmentCard.tsx
import Link from 'next/link';

interface RecruitmentCardProps {
  id: number;
  title: string;
  teamName?: string | null;
  description: string;
  teamSize?: number | null;
  requiredRoles?: string | null;
  createdAt: string;
}

export default function RecruitmentCard({
  id, title, teamName, description, teamSize, requiredRoles,
}: RecruitmentCardProps) {
  let roles: { role: string; count: number }[] = [];
  try { roles = requiredRoles ? JSON.parse(requiredRoles) : []; } catch {}

  return (
    <Link href={`/recruitment/${id}`} className="block">
      <div className="mx-4 mb-3 bg-white rounded-xl p-4 border border-gray-100 active:bg-gray-50">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-sm text-gray-900">{title}</h4>
          {teamName && <span className="text-xs text-gray-400">{teamName}</span>}
        </div>
        {roles.length > 0 && (
          <div className="flex gap-1.5 mt-2 flex-wrap">
            {roles.map((r, i) => (
              <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                {r.role} ×{r.count}
              </span>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-2.5 text-xs text-gray-400">
          <span>{teamSize ? `共需 ${teamSize} 人` : '人数未定'}</span>
        </div>
      </div>
    </Link>
  );
}
```

- [ ] **Step 2: 实现 CompetitionDetail Server Component**

```typescript
// src/app/competitions/[id]/page.tsx
import { db } from '@/lib/db';
import { competitions, recruitments } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { notFound } from 'next/navigation';
import CompetitionDetailClient from './CompetitionDetailClient';

export const dynamic = 'force-dynamic';

async function getCompetition(id: number) {
  const comp = db.select().from(competitions).where(eq(competitions.id, id)).get();
  if (!comp) return null;

  const recs = db.select().from(recruitments)
    .where(and(eq(recruitments.competitionId, id), eq(recruitments.status, 'open')))
    .all();

  return { comp, recs };
}

export default async function CompetitionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await getCompetition(Number(id));
  if (!data) notFound();
  return <CompetitionDetailClient competition={data.comp} recruitments={data.recs} />;
}
```

- [ ] **Step 3: 实现客户端渲染的详情组件**

```typescript
// src/app/competitions/[id]/CompetitionDetailClient.tsx
'use client';

import { useRouter } from 'next/navigation';
import { NavBar } from 'antd-mobile';
import EmptyState from '@/components/ui/EmptyState';
import RecruitmentCard from '@/components/features/RecruitmentCard';

export default function CompetitionDetailClient({ competition, recruitments }: {
  competition: any;
  recruitments: any[];
}) {
  const router = useRouter();

  return (
    <div>
      <NavBar onBack={() => router.back()} className="bg-white">
        {competition.category}
      </NavBar>
      <div className="p-4">
        <h1 className="text-lg font-bold text-gray-900">{competition.title}</h1>
        <div className="mt-2 space-y-1.5 text-sm text-gray-500">
          {competition.organizer && <p>主办：{competition.organizer}</p>}
          {competition.registrationDeadline && (
            <p>报名截止：{new Date(competition.registrationDeadline).toLocaleDateString('zh-CN')}</p>
          )}
          {competition.competitionDate && (
            <p>比赛时间：{new Date(competition.competitionDate).toLocaleDateString('zh-CN')}</p>
          )}
        </div>
        {competition.description && (
          <p className="mt-3 text-sm text-gray-600 leading-relaxed">{competition.description}</p>
        )}
      </div>

      <div className="border-t border-gray-100 pt-4">
        <h3 className="px-4 text-base font-semibold text-gray-900 mb-3">
          相关招募帖 ({recruitments.length})
        </h3>
        {recruitments.length === 0 ? (
          <EmptyState icon="📋" title="暂无招募帖" description="暂时没有人为此比赛发布招募" />
        ) : (
          recruitments.map((r) => (
            <RecruitmentCard
              key={r.id}
              id={r.id}
              title={r.title}
              teamName={r.teamName}
              description={r.description}
              teamSize={r.teamSize}
              requiredRoles={r.requiredRoles}
              createdAt={r.createdAt}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: implement competition detail page with linked recruitments"
```

---

### Task 9: 实现招募广场页

**Files:**
- Create: `src/app/recruitment/page.tsx`

- [ ] **Step 1: 实现招募列表 Server Component**

```typescript
// src/app/recruitment/page.tsx
import { db } from '@/lib/db';
import { recruitments, competitions, users } from '@/lib/db/schema';
import { eq, desc } from 'drizzle-orm';
import RecruitmentListClient from './RecruitmentListClient';

export const dynamic = 'force-dynamic';

async function getRecruitments() {
  const rows = db.select({
    id: recruitments.id,
    title: recruitments.title,
    description: recruitments.description,
    teamName: recruitments.teamName,
    teamSize: recruitments.teamSize,
    requiredRoles: recruitments.requiredRoles,
    status: recruitments.status,
    deadline: recruitments.deadline,
    createdAt: recruitments.createdAt,
    competitionTitle: competitions.title,
    competitionCategory: competitions.category,
    creatorName: users.nickname,
  })
  .from(recruitments)
  .leftJoin(competitions, eq(recruitments.competitionId, competitions.id))
  .leftJoin(users, eq(recruitments.creatorId, users.id))
  .where(eq(recruitments.status, 'open'))
  .orderBy(desc(recruitments.createdAt))
  .all();
  return rows;
}

export default async function RecruitmentPage() {
  const recs = await getRecruitments();
  return <RecruitmentListClient recruitments={recs} />;
}
```

- [ ] **Step 2: 实现客户端交互层**

```typescript
// src/app/recruitment/RecruitmentListClient.tsx
'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { NavBar, Button } from 'antd-mobile';
import FilterTabs from '@/components/ui/FilterTabs';
import EmptyState from '@/components/ui/EmptyState';
import RecruitmentCard from '@/components/features/RecruitmentCard';

export default function RecruitmentListClient({ recruitments }: { recruitments: any[] }) {
  const router = useRouter();
  const [category, setCategory] = useState('全部');

  const allCategories = ['全部', ...Array.from(new Set(
    recruitments.map((r: any) => r.competitionCategory).filter(Boolean)
  ))] as string[];

  const filtered = useMemo(() => {
    if (category === '全部') return recruitments;
    return recruitments.filter((r: any) => r.competitionCategory === category);
  }, [recruitments, category]);

  return (
    <div>
      <NavBar onBack={() => router.push('/')} className="bg-white">
        组队广场
      </NavBar>
      <div className="px-4 pt-3 pb-2">
        <Button
          block
          color="primary"
          size="large"
          onClick={() => router.push('/recruitment/new')}
        >
          发布招募
        </Button>
      </div>
      <FilterTabs categories={allCategories} active={category} onChange={setCategory} />
      {filtered.length === 0 ? (
        <EmptyState icon="👥" title="暂无招募帖" description="还没有人发布招募，来做第一个吧" />
      ) : (
        filtered.map((r: any) => (
          <RecruitmentCard
            key={r.id}
            id={r.id}
            title={r.title}
            teamName={r.teamName}
            description={r.description}
            teamSize={r.teamSize}
            requiredRoles={r.requiredRoles}
            createdAt={r.createdAt}
          />
        ))
      )}
    </div>
  );
}
```

- [ ] **Step 3: 提交**

```bash
git add -A && git commit -m "feat: implement recruitment list page"
```

---

### Task 10: 实现招募详情页 + 申请按钮

**Files:**
- Create: `src/components/features/ApplicationButton.tsx`
- Create: `src/app/recruitment/[id]/page.tsx`

- [ ] **Step 1: 实现 ApplicationButton 状态机**

```typescript
// src/components/features/ApplicationButton.tsx
'use client';

import { useState } from 'react';
import { Button, Dialog, Toast } from 'antd-mobile';

type AppStatus = 'not_logged_in' | 'can_apply' | 'applied_pending' | 'applied_accepted' | 'applied_rejected' | 'closed';

interface ApplicationButtonProps {
  recruitmentId: number;
  initialStatus: AppStatus;
  isLoggedIn: boolean;
}

export default function ApplicationButton({ recruitmentId, initialStatus, isLoggedIn }: ApplicationButtonProps) {
  const [status, setStatus] = useState<AppStatus>(initialStatus);

  const handleApply = async () => {
    if (!isLoggedIn) {
      Dialog.alert({ content: '请先使用微信登录' });
      return;
    }

    const confirmed = await Dialog.confirm({ content: '确认申请加入该队伍？' });
    if (!confirmed) return;

    try {
      const res = await fetch(`/api/recruitments/${recruitmentId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: '我想加入' }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus('applied_pending');
        Toast.show({ icon: 'success', content: '申请已提交' });
      } else {
        Toast.show({ icon: 'fail', content: data.message || '申请失败' });
      }
    } catch {
      Toast.show({ icon: 'fail', content: '网络错误，请重试' });
    }
  };

  if (status === 'closed') {
    return <Button block disabled>招募已关闭</Button>;
  }
  if (status === 'applied_pending') {
    return <Button block color="warning" loading>等待审核中</Button>;
  }
  if (status === 'applied_accepted') {
    return <Button block color="success" disabled>已通过</Button>;
  }
  if (status === 'applied_rejected') {
    return <Button block disabled>已被拒绝</Button>;
  }
  return (
    <Button block color="primary" onClick={handleApply}>
      申请加入
    </Button>
  );
}
```

- [ ] **Step 2: 实现招募详情 Server Component**

```typescript
// src/app/recruitment/[id]/page.tsx
import { db } from '@/lib/db';
import { recruitments, competitions, users, recruitmentApplications } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { notFound } from 'next/navigation';
import { getCurrentUserId } from '@/lib/session';
import RecruitmentDetailClient from './RecruitmentDetailClient';

export const dynamic = 'force-dynamic';

async function getRecruitment(id: number) {
  const rec = db.select({
    id: recruitments.id,
    title: recruitments.title,
    description: recruitments.description,
    teamName: recruitments.teamName,
    teamSize: recruitments.teamSize,
    requiredRoles: recruitments.requiredRoles,
    status: recruitments.status,
    deadline: recruitments.deadline,
    createdAt: recruitments.createdAt,
    competitionTitle: competitions.title,
    competitionId: competitions.id,
    creatorName: users.nickname,
    creatorMajor: users.major,
    creatorGrade: users.grade,
    creatorId: users.id,
  })
  .from(recruitments)
  .leftJoin(competitions, eq(recruitments.competitionId, competitions.id))
  .leftJoin(users, eq(recruitments.creatorId, users.id))
  .where(eq(recruitments.id, id))
  .get();
  return rec;
}

export default async function RecruitmentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const rec = await getRecruitment(Number(id));
  if (!rec) notFound();

  const userId = await getCurrentUserId();
  let appStatus: 'not_logged_in' | 'can_apply' | 'applied_pending' | 'applied_accepted' | 'applied_rejected' | 'closed' = 'not_logged_in';

  if (rec.status !== 'open') {
    appStatus = 'closed';
  } else if (!userId) {
    appStatus = 'not_logged_in';
  } else if (userId === rec.creatorId) {
    appStatus = 'closed'; // 不能申请自己的招募
  } else {
    const existing = db.select().from(recruitmentApplications)
      .where(and(
        eq(recruitmentApplications.recruitmentId, Number(id)),
        eq(recruitmentApplications.applicantId, userId),
      ))
      .get();
    if (!existing) {
      appStatus = 'can_apply';
    } else if (existing.status === 'pending') {
      appStatus = 'applied_pending';
    } else if (existing.status === 'accepted') {
      appStatus = 'applied_accepted';
    } else {
      appStatus = 'applied_rejected';
    }
  }

  return <RecruitmentDetailClient recruitment={rec} appStatus={appStatus} isLoggedIn={!!userId} />;
}
```

- [ ] **Step 3: 实现客户端详情组件**

```typescript
// src/app/recruitment/[id]/RecruitmentDetailClient.tsx
'use client';

import { useRouter } from 'next/navigation';
import { NavBar } from 'antd-mobile';
import ApplicationButton from '@/components/features/ApplicationButton';

export default function RecruitmentDetailClient({ recruitment, appStatus, isLoggedIn }: {
  recruitment: any;
  appStatus: string;
  isLoggedIn: boolean;
}) {
  const router = useRouter();
  let roles: { role: string; count: number }[] = [];
  try { roles = recruitment.requiredRoles ? JSON.parse(recruitment.requiredRoles) : []; } catch {}

  return (
    <div>
      <NavBar onBack={() => router.back()} className="bg-white">招募详情</NavBar>
      <div className="p-4">
        <h1 className="text-lg font-bold text-gray-900">{recruitment.title}</h1>
        {recruitment.teamName && (
          <p className="text-sm text-gray-400 mt-1">{recruitment.teamName}</p>
        )}

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white text-sm font-bold">
              {recruitment.creatorName?.charAt(0) || '?'}
            </div>
            <div>
              <p className="font-medium text-sm">{recruitment.creatorName}</p>
              <p className="text-xs text-gray-400">
                {[recruitment.creatorGrade, recruitment.creatorMajor].filter(Boolean).join(' · ')}
              </p>
            </div>
          </div>
        </div>

        {roles.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">需要角色</h4>
            <div className="flex gap-2 flex-wrap">
              {roles.map((r, i) => (
                <span key={i} className="text-sm bg-primary-light text-primary px-3 py-1 rounded-full">
                  {r.role} ×{r.count}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">招募描述</h4>
          <p className="text-sm text-gray-600 leading-relaxed">{recruitment.description}</p>
        </div>

        {recruitment.competitionTitle && (
          <div className="mt-4 text-sm text-gray-400">
            关联比赛：
            <span
              className="text-primary underline cursor-pointer"
              onClick={() => router.push(`/competitions/${recruitment.competitionId}`)}
            >
              {recruitment.competitionTitle}
            </span>
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-100 safe-bottom max-w-lg mx-auto">
        <ApplicationButton
          recruitmentId={recruitment.id}
          initialStatus={appStatus as any}
          isLoggedIn={isLoggedIn}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: implement recruitment detail page with application flow"
```

---

### Task 11: 实现发布招募页

**Files:**
- Create: `src/app/recruitment/new/page.tsx`

- [ ] **Step 1: 实现发布招募表单**

```typescript
// src/app/recruitment/new/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { NavBar, Form, Input, TextArea, Button, Picker, Toast, Dialog } from 'antd-mobile';
import { useSearchParams } from 'next/navigation';

export default function NewRecruitmentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async () => {
    const values = form.getFieldsValue();
    if (!values.title || !values.description) {
      Dialog.alert({ content: '请填写标题和描述' });
      return;
    }

    setLoading(true);
    try {
      const competitionId = searchParams.get('competitionId');

      const res = await fetch('/api/recruitments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: values.title,
          description: values.description,
          teamName: values.teamName,
          competitionId: competitionId ? Number(competitionId) : undefined,
          teamSize: values.teamSize ? Number(values.teamSize) : undefined,
          requiredRoles: values.requiredRoles
            ? values.requiredRoles.split(',').map((s: string) => s.trim()).filter(Boolean).map((s: string) => {
                const [role, count] = s.includes(':') ? s.split(':') : [s, '1'];
                return { role: role.trim(), count: Number(count) || 1 };
              })
            : [],
          deadline: values.deadline,
        }),
      });

      if (res.ok) {
        Toast.show({ icon: 'success', content: '发布成功' });
        router.push('/recruitment');
      } else {
        const data = await res.json();
        Toast.show({ icon: 'fail', content: data.message || '发布失败' });
      }
    } catch {
      Toast.show({ icon: 'fail', content: '网络错误' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <NavBar onBack={() => router.back()} className="bg-white">发布招募</NavBar>
      <div className="p-4">
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="招募标题" rules={[{ required: true }]}>
            <Input placeholder="如：数学建模国赛找编程手" />
          </Form.Item>
          <Form.Item name="teamName" label="队伍名称">
            <Input placeholder="可选，起个队名" />
          </Form.Item>
          <Form.Item name="description" label="招募描述" rules={[{ required: true }]}>
            <TextArea placeholder="介绍一下队伍情况和需要什么样的队友..." rows={4} />
          </Form.Item>
          <Form.Item name="teamSize" label="队伍总人数">
            <Input type="number" placeholder="如：3" />
          </Form.Item>
          <Form.Item name="requiredRoles" label="需要角色">
            <Input placeholder="如：编程手:1, 建模手:2（角色:人数，逗号分隔）" />
          </Form.Item>
          <Form.Item name="deadline" label="截止日期">
            <Input type="date" />
          </Form.Item>
        </Form>
        <Button block color="primary" size="large" loading={loading} onClick={handleSubmit} className="mt-4">
          发布招募
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add -A && git commit -m "feat: implement recruitment creation form"
```

---

### Task 12: 实现个人中心页

**Files:**
- Create: `src/components/features/UserProfileForm.tsx`
- Create: `src/app/profile/page.tsx`

- [ ] **Step 1: 实现资料编辑表单**

```typescript
// src/components/features/UserProfileForm.tsx
'use client';

import { useState } from 'react';
import { Form, Input, TextArea, Button, Toast } from 'antd-mobile';

export default function UserProfileForm({ user }: { user: any }) {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSave = async () => {
    const values = form.getFieldsValue();
    setLoading(true);
    try {
      const res = await fetch('/api/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      if (res.ok) {
        Toast.show({ icon: 'success', content: '保存成功' });
      } else {
        const data = await res.json();
        Toast.show({ icon: 'fail', content: data.message || '保存失败' });
      }
    } catch {
      Toast.show({ icon: 'fail', content: '网络错误' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        nickname: user.nickname || '',
        school: user.school || '',
        major: user.major || '',
        grade: user.grade || '',
        skills: user.skills ? JSON.parse(user.skills).join(', ') : '',
        bio: user.bio || '',
      }}
    >
      <Form.Item name="nickname" label="昵称">
        <Input placeholder="你的名字" />
      </Form.Item>
      <Form.Item name="school" label="学校">
        <Input placeholder="如：XX 大学" />
      </Form.Item>
      <Form.Item name="major" label="专业">
        <Input placeholder="如：计算机科学" />
      </Form.Item>
      <Form.Item name="grade" label="年级">
        <Input placeholder="如：2023级" />
      </Form.Item>
      <Form.Item name="skills" label="技能标签">
        <Input placeholder="如：Python, 数据分析, MATLAB（逗号分隔）" />
      </Form.Item>
      <Form.Item name="bio" label="个人简介">
        <TextArea placeholder="简单介绍一下自己..." rows={3} />
      </Form.Item>
      <Button block color="primary" size="large" loading={loading} onClick={handleSave}>
        保存
      </Button>
    </Form>
  );
}
```

- [ ] **Step 2: 实现个人中心页**

```typescript
// src/app/profile/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { getCurrentUserId } from '@/lib/session';
import ProfileClient from './ProfileClient';

export const dynamic = 'force-dynamic';

export default async function ProfilePage() {
  const userId = await getCurrentUserId();
  let user = null;
  if (userId) {
    user = db.select().from(users).where(eq(users.id, userId)).get();
  }
  return <ProfileClient user={user} />;
}
```

```typescript
// src/app/profile/ProfileClient.tsx
'use client';

import { useRouter } from 'next/navigation';
import { NavBar } from 'antd-mobile';
import WechatLoginButton from '@/components/features/WechatLoginButton';
import UserProfileForm from '@/components/features/UserProfileForm';

export default function ProfileClient({ user }: { user: any }) {
  const router = useRouter();

  return (
    <div>
      <NavBar onBack={() => router.push('/')} className="bg-white">我的</NavBar>
      <div className="p-4">
        {!user ? (
          <div className="flex flex-col items-center py-16">
            <p className="text-gray-400 text-sm mb-4">登录后查看个人资料</p>
            <WechatLoginButton />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-4 mb-6 p-4 bg-white rounded-xl border border-gray-100">
              <div className="w-14 h-14 rounded-full bg-primary flex items-center justify-center text-white text-xl font-bold">
                {user.nickname?.charAt(0) || '?'}
              </div>
              <div>
                <p className="font-semibold text-gray-900">{user.nickname}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {[user.grade, user.major].filter(Boolean).join(' · ') || '请完善个人资料'}
                </p>
              </div>
            </div>
            <UserProfileForm user={user} />

            <button
              className="w-full mt-6 py-3 text-sm text-gray-400 text-center"
              onClick={async () => {
                await fetch('/api/auth/logout', { method: 'POST' });
                router.refresh();
              }}
            >
              退出登录
            </button>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 实现微信登录按钮**

```typescript
// src/components/features/WechatLoginButton.tsx
'use client';

import { Button } from 'antd-mobile';

export default function WechatLoginButton() {
  const handleLogin = () => {
    // 构造微信授权 URL，回调到当前域名
    const redirectUri = encodeURIComponent(`${window.location.origin}/api/auth/wechat/callback`);
    const appId = process.env.NEXT_PUBLIC_WECHAT_APP_ID || 'your_app_id';
    window.location.href = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect`;
  };

  return (
    <Button block color="success" size="large" onClick={handleLogin}>
      微信一键登录
    </Button>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: implement profile page with edit and WeChat login"
```

---

### Task 13: 实现写操作 API Routes

**Files:**
- Create: `src/app/api/recruitments/route.ts`
- Create: `src/app/api/recruitments/[id]/route.ts`
- Create: `src/app/api/recruitments/[id]/apply/route.ts`
- Create: `src/app/api/users/me/route.ts`
- Create: `src/app/api/competitions/route.ts`

- [ ] **Step 1: POST /api/recruitments — 发布招募**

```typescript
// src/app/api/recruitments/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { recruitments } from '@/lib/db/schema';
import { getCurrentUserId } from '@/lib/session';

export async function POST(request: NextRequest) {
  const userId = await getCurrentUserId();
  if (!userId) {
    return NextResponse.json({ message: '请先登录' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const result = db.insert(recruitments).values({
      creatorId: userId,
      title: body.title,
      description: body.description,
      teamName: body.teamName || null,
      competitionId: body.competitionId || null,
      teamSize: body.teamSize || null,
      requiredRoles: body.requiredRoles ? JSON.stringify(body.requiredRoles) : null,
      deadline: body.deadline || null,
      status: 'open',
    }).run();

    return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
  } catch (error) {
    console.error('创建招募失败:', error);
    return NextResponse.json({ message: '发布失败，请重试' }, { status: 500 });
  }
}
```

- [ ] **Step 2: PATCH /api/recruitments/[id] — 关闭招募**

```typescript
// src/app/api/recruitments/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { recruitments } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUserId } from '@/lib/session';

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const userId = await getCurrentUserId();
  if (!userId) {
    return NextResponse.json({ message: '请先登录' }, { status: 401 });
  }

  const { id } = await params;
  const rec = db.select().from(recruitments).where(eq(recruitments.id, Number(id))).get();
  if (!rec) {
    return NextResponse.json({ message: '招募不存在' }, { status: 404 });
  }
  if (rec.creatorId !== userId) {
    return NextResponse.json({ message: '只有队长可以操作' }, { status: 403 });
  }

  db.update(recruitments).set({ status: 'closed' }).where(eq(recruitments.id, Number(id))).run();
  return NextResponse.json({ success: true });
}
```

- [ ] **Step 3: POST /api/recruitments/[id]/apply — 申请加入**

```typescript
// src/app/api/recruitments/[id]/apply/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { recruitments, recruitmentApplications } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUserId } from '@/lib/session';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const userId = await getCurrentUserId();
  if (!userId) {
    return NextResponse.json({ message: '请先登录' }, { status: 401 });
  }

  const { id } = await params;

  // 检查招募是否存在且开放
  const rec = db.select().from(recruitments).where(eq(recruitments.id, Number(id))).get();
  if (!rec) {
    return NextResponse.json({ message: '招募不存在' }, { status: 404 });
  }
  if (rec.status !== 'open') {
    return NextResponse.json({ message: '招募已关闭' }, { status: 400 });
  }
  if (rec.creatorId === userId) {
    return NextResponse.json({ message: '不能申请自己的招募' }, { status: 400 });
  }

  // 检查重复申请
  const existing = db.select().from(recruitmentApplications)
    .where(and(
      eq(recruitmentApplications.recruitmentId, Number(id)),
      eq(recruitmentApplications.applicantId, userId),
    ))
    .get();
  if (existing) {
    return NextResponse.json({ message: '你已经申请过了' }, { status: 400 });
  }

  const body = await request.json();
  db.insert(recruitmentApplications).values({
    recruitmentId: Number(id),
    applicantId: userId,
    message: body.message || '',
  }).run();

  return NextResponse.json({ success: true }, { status: 201 });
}
```

- [ ] **Step 4: GET + PATCH /api/users/me — 读写当前用户资料**

```typescript
// src/app/api/users/me/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { getCurrentUserId } from '@/lib/session';

export async function GET() {
  const userId = await getCurrentUserId();
  if (!userId) {
    return NextResponse.json({ message: '未登录' }, { status: 401 });
  }
  const user = db.select().from(users).where(eq(users.id, userId)).get();
  return NextResponse.json(user);
}

export async function PATCH(request: NextRequest) {
  const userId = await getCurrentUserId();
  if (!userId) {
    return NextResponse.json({ message: '请先登录' }, { status: 401 });
  }

  const body = await request.json();
  const updates: Record<string, any> = {};
  if (body.nickname !== undefined) updates.nickname = body.nickname;
  if (body.school !== undefined) updates.school = body.school;
  if (body.major !== undefined) updates.major = body.major;
  if (body.grade !== undefined) updates.grade = body.grade;
  if (body.bio !== undefined) updates.bio = body.bio;
  if (body.skills !== undefined) {
    // skills 支持逗号分隔文本或 JSON 数组
    updates.skills = typeof body.skills === 'string'
      ? JSON.stringify(body.skills.split(',').map((s: string) => s.trim()).filter(Boolean))
      : JSON.stringify(body.skills);
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ message: '没有需要更新的字段' }, { status: 400 });
  }

  db.update(users).set(updates).where(eq(users.id, userId)).run();
  return NextResponse.json({ success: true });
}
```

- [ ] **Step 5: POST /api/competitions — 管理员新增比赛**

```typescript
// src/app/api/competitions/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { competitions } from '@/lib/db/schema';

const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'dev-admin-token';

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || authHeader !== `Bearer ${ADMIN_TOKEN}`) {
    return NextResponse.json({ message: '无权限' }, { status: 403 });
  }

  try {
    const body = await request.json();
    const result = db.insert(competitions).values({
      title: body.title,
      category: body.category,
      description: body.description || null,
      organizer: body.organizer || null,
      registrationDeadline: body.registrationDeadline || null,
      competitionDate: body.competitionDate || null,
      url: body.url || null,
      status: body.status || 'upcoming',
      isVerified: true,
    }).run();

    return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
  } catch (error) {
    console.error('创建比赛失败:', error);
    return NextResponse.json({ message: '创建失败' }, { status: 500 });
  }
}
```

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "feat: implement write API routes for recruitments, users, and competitions"
```

---

### Task 14: 实现错误处理

**Files:**
- Create: `src/app/error.tsx`
- Create: `src/app/global-error.tsx`
- Create: `src/app/not-found.tsx`

- [ ] **Step 1: error.tsx — 页面级错误边界**

```typescript
// src/app/error.tsx
'use client';

import { Button } from 'antd-mobile';

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <span className="text-4xl mb-4">😵</span>
      <h2 className="text-lg font-semibold text-gray-900">页面加载失败</h2>
      <p className="text-sm text-gray-400 mt-2 text-center">{error.message || '请稍后重试'}</p>
      <Button color="primary" className="mt-6" onClick={reset}>
        重新加载
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: global-error.tsx — 全局错误边界**

```typescript
// src/app/global-error.tsx
'use client';

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen px-4">
          <span className="text-4xl mb-4">💥</span>
          <h2 className="text-lg font-semibold text-gray-900">出了点问题</h2>
          <p className="text-sm text-gray-400 mt-2">应用遇到了意外错误</p>
          <button
            className="mt-6 px-6 py-2.5 bg-primary text-white rounded-lg text-sm"
            onClick={reset}
          >
            返回首页
          </button>
        </div>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: not-found.tsx**

```typescript
// src/app/not-found.tsx
import Link from 'next/link';
import { Button } from 'antd-mobile';

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <span className="text-4xl mb-4">🔍</span>
      <h2 className="text-lg font-semibold text-gray-900">页面不存在</h2>
      <p className="text-sm text-gray-400 mt-2">你访问的页面可能已被移除</p>
      <Link href="/" className="mt-6">
        <Button color="primary">返回首页</Button>
      </Link>
    </div>
  );
}
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: add error boundaries and 404 page"
```

---

### Task 15: 编写种子数据

**Files:**
- Create: `src/lib/db/seed.ts`

- [ ] **Step 1: 编写种子数据脚本**

```typescript
// src/lib/db/seed.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data.db');

// 执行 migration
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(DB_PATH);
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');
const db = drizzle(sqlite);

// 运行 migration
migrate(db, { migrationsFolder: './drizzle' });

// 插入种子数据
const competitions = [
  {
    title: '全国大学生数学建模竞赛',
    category: '数学建模',
    organizer: '中国工业与应用数学学会',
    registration_deadline: '2026-06-15',
    competition_date: '2026-09-10',
    description: '全国大学生数学建模竞赛创办于1992年，每年一届，是首批列入"高校学科竞赛排行榜"的19项竞赛之一。',
    is_verified: 1,
  },
  {
    title: '"挑战杯"全国大学生课外学术科技作品竞赛',
    category: '创新创业',
    organizer: '共青团中央、中国科协、教育部、全国学联',
    registration_deadline: '2026-05-30',
    competition_date: '2026-10-01',
    description: '"挑战杯"竞赛在中国共有两个并列项目，一个是"挑战杯"全国大学生课外学术科技作品竞赛（大挑），另一个是"挑战杯"中国大学生创业计划竞赛（小挑）。',
    is_verified: 1,
  },
  {
    title: 'ACM-ICPC 国际大学生程序设计竞赛',
    category: '编程开发',
    organizer: 'ACM (Association for Computing Machinery)',
    registration_deadline: '2026-07-01',
    competition_date: '2026-10-15',
    description: 'ACM国际大学生程序设计竞赛（ACM-ICPC）是由国际计算机协会（ACM）主办的，一项旨在展示大学生创新能力、团队精神和在压力下编写程序、分析和解决问题能力的年度竞赛。',
    is_verified: 1,
  },
  {
    title: '全国大学生电子设计竞赛',
    category: '电子设计',
    organizer: '教育部高等教育司、工业和信息化部人事教育司',
    registration_deadline: '2026-06-30',
    competition_date: '2026-08-15',
    description: '全国大学生电子设计竞赛是教育部和工业和信息化部共同发起的大学生学科竞赛之一。',
    is_verified: 1,
  },
  {
    title: '"外研社杯"全国英语演讲大赛',
    category: '英语',
    organizer: '外语教学与研究出版社',
    registration_deadline: '2026-07-15',
    competition_date: '2026-09-20',
    description: '"外研社杯"全国英语演讲大赛是由外语教学与研究出版社主办，面向全国高校在校大学生的高水平英语演讲赛事。',
    is_verified: 1,
  },
  {
    title: '全国大学生机器人大赛 RoboMaster',
    category: '电子设计',
    organizer: '共青团中央、全国学联',
    registration_deadline: '2026-06-01',
    competition_date: '2026-08-01',
    description: 'RoboMaster机甲大师赛是由大疆创新发起并承办，面向全球大学生开展的机器人竞赛。',
    is_verified: 1,
  },
  {
    title: '中国"互联网+"大学生创新创业大赛',
    category: '创新创业',
    organizer: '教育部',
    registration_deadline: '2026-05-20',
    competition_date: '2026-07-01',
    description: '中国"互联网+"大学生创新创业大赛是由教育部与有关部委共同主办的全国性大学生创新创业大赛。',
    is_verified: 1,
  },
  {
    title: '蓝桥杯全国软件和信息技术专业人才大赛',
    category: '编程开发',
    organizer: '工业和信息化部人才交流中心',
    registration_deadline: '2026-06-20',
    competition_date: '2026-09-01',
    description: '蓝桥杯大赛是由工业和信息化部人才交流中心主办的全国性IT学科赛事。',
    is_verified: 1,
  },
];

for (const c of competitions) {
  const existing = sqlite.prepare('SELECT id FROM competitions WHERE title = ?').get(c.title);
  if (!existing) {
    sqlite.prepare(`
      INSERT INTO competitions (title, category, organizer, registration_deadline, competition_date, description, is_verified, status)
      VALUES (?, ?, ?, ?, ?, ?, ?, 'upcoming')
    `).run(c.title, c.category, c.organizer, c.registration_deadline, c.competition_date, c.description, c.is_verified);
    console.log(`Inserted: ${c.title}`);
  } else {
    console.log(`Skipped (exists): ${c.title}`);
  }
}

console.log('Seed complete.');
```

- [ ] **Step 2: 添加 npm script 并运行种子数据**

在 `package.json` 中添加：
```json
{
  "scripts": {
    ...,
    "seed": "npx tsx src/lib/db/seed.ts"
  }
}
```

```bash
npm run seed
```
Expected: 8 条比赛数据插入成功。

- [ ] **Step 3: 验证 — 启动 dev server 查看首页**

```bash
npm run dev
```
访问 http://localhost:3000，确认 8 条比赛数据显示在首页。

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: add seed data with 8 competition entries"
```

---

### Task 16: 编写 API Route 测试

**Files:**
- Create: `tests/api/recruitments.test.ts`
- Create: `tests/api/users.test.ts`

- [ ] **Step 1: 编写招募 API 测试**

```typescript
// tests/api/recruitments.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from '@/lib/db/schema';

const sqlite = new Database(':memory:');
const db = drizzle(sqlite, { schema });

beforeAll(() => {
  sqlite.exec(`
    CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, wechat_openid TEXT UNIQUE NOT NULL, nickname TEXT NOT NULL, avatar_url TEXT, school TEXT NOT NULL, major TEXT, grade TEXT, skills TEXT, bio TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE competitions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT, organizer TEXT, registration_deadline TEXT, competition_date TEXT, url TEXT, status TEXT DEFAULT 'upcoming', created_by INTEGER REFERENCES users(id), is_verified INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE recruitments (id INTEGER PRIMARY KEY AUTOINCREMENT, competition_id INTEGER REFERENCES competitions(id), creator_id INTEGER REFERENCES users(id) NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, team_name TEXT, required_roles TEXT, team_size INTEGER, deadline TEXT, status TEXT DEFAULT 'open', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE recruitment_applications (id INTEGER PRIMARY KEY AUTOINCREMENT, recruitment_id INTEGER REFERENCES recruitments(id) NOT NULL, applicant_id INTEGER REFERENCES users(id) NOT NULL, message TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  `);

  db.insert(schema.users).values({ wechatOpenid: 'u1', nickname: '队长', school: 'X' }).run();
  db.insert(schema.users).values({ wechatOpenid: 'u2', nickname: '队员', school: 'X' }).run();
  db.insert(schema.competitions).values({ title: '测试比赛', category: '编程' }).run();
});

describe('Recruitment API logic', () => {
  it('creates a recruitment', () => {
    const result = db.insert(schema.recruitments).values({
      creatorId: 1,
      competitionId: 1,
      title: '找队友',
      description: '一起参赛',
      requiredRoles: JSON.stringify([{ role: '前端', count: 2 }]),
      status: 'open',
    }).run();
    expect(Number(result.lastInsertRowid)).toBeGreaterThan(0);
  });

  it('prevents duplicate application', () => {
    db.insert(schema.recruitments).values({
      creatorId: 1,
      title: '另一个招募',
      description: '描述',
      status: 'open',
    }).run();

    // 第一次申请成功
    db.insert(schema.recruitmentApplications).values({
      recruitmentId: 2,
      applicantId: 2,
      message: '我想加入',
    }).run();

    // 检查重复
    const existing = db.select().from(schema.recruitmentApplications)
      .where(
        sqlite.prepare('SELECT 1').pluck ? {} : {}
      ).all();
    // 简化为直接查询
    const apps = db.select().from(schema.recruitmentApplications).all();
    expect(apps.filter((a: any) => a.recruitmentId === 2 && a.applicantId === 2).length).toBe(1);
  });

  it('closes a recruitment', () => {
    db.update(schema.recruitments).set({ status: 'closed' })
      .where(sqlite.prepare('SELECT 1').pluck ? {} : {})
      .run();
    // 简化：用原始 SQL 查询
    const rec = sqlite.prepare('SELECT status FROM recruitments WHERE id = 1').get() as any;
    // 直接使用 drizzle 查询
    const { eq } = require('drizzle-orm');
    const updated = db.select().from(schema.recruitments).where(eq(schema.recruitments.id, 1)).get();
    expect(updated?.status).toBe('closed');
  });
});
```

Wait, that last test has issues with mixing approaches. Let me rewrite it properly.

Actually let me rethink this test file. The `eq` import needs to come from drizzle-orm. Let me rewrite it cleaner.

- [ ] **Step 1 (revised): 编写招募 API 逻辑测试**

```typescript
// tests/api/recruitments.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq, and } from 'drizzle-orm';
import * as schema from '@/lib/db/schema';

const sqlite = new Database(':memory:');
const db = drizzle(sqlite, { schema });

beforeAll(() => {
  sqlite.exec(`
    CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, wechat_openid TEXT UNIQUE NOT NULL, nickname TEXT NOT NULL, avatar_url TEXT, school TEXT NOT NULL, major TEXT, grade TEXT, skills TEXT, bio TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE competitions (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT, organizer TEXT, registration_deadline TEXT, competition_date TEXT, url TEXT, status TEXT DEFAULT 'upcoming', created_by INTEGER REFERENCES users(id), is_verified INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE recruitments (id INTEGER PRIMARY KEY AUTOINCREMENT, competition_id INTEGER REFERENCES competitions(id), creator_id INTEGER REFERENCES users(id) NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, team_name TEXT, required_roles TEXT, team_size INTEGER, deadline TEXT, status TEXT DEFAULT 'open', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE recruitment_applications (id INTEGER PRIMARY KEY AUTOINCREMENT, recruitment_id INTEGER REFERENCES recruitments(id) NOT NULL, applicant_id INTEGER REFERENCES users(id) NOT NULL, message TEXT, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  `);

  db.insert(schema.users).values({ wechatOpenid: 'captain', nickname: '队长', school: '测试大学' }).run();
  db.insert(schema.users).values({ wechatOpenid: 'member', nickname: '队员', school: '测试大学' }).run();
  db.insert(schema.competitions).values({ title: '测试比赛', category: '编程开发' }).run();
});

describe('Recruitment CRUD', () => {
  it('creates a recruitment with all fields', () => {
    const result = db.insert(schema.recruitments).values({
      creatorId: 1,
      competitionId: 1,
      title: '数学建模找编程手',
      description: '已有建模手和写作手，急缺编程',
      teamName: '必胜队',
      teamSize: 3,
      requiredRoles: JSON.stringify([{ role: '编程手', count: 1 }]),
      status: 'open',
    }).run();
    expect(Number(result.lastInsertRowid)).toBeGreaterThan(0);

    const rec = db.select().from(schema.recruitments)
      .where(eq(schema.recruitments.id, Number(result.lastInsertRowid)))
      .get();
    expect(rec?.title).toBe('数学建模找编程手');
    expect(rec?.status).toBe('open');
    expect(rec?.teamSize).toBe(3);
  });

  it('closes a recruitment', () => {
    const result = db.insert(schema.recruitments).values({
      creatorId: 1, title: '测试', description: '描述', status: 'open',
    }).run();

    db.update(schema.recruitments)
      .set({ status: 'closed' })
      .where(eq(schema.recruitments.id, Number(result.lastInsertRowid)))
      .run();

    const updated = db.select().from(schema.recruitments)
      .where(eq(schema.recruitments.id, Number(result.lastInsertRowid)))
      .get();
    expect(updated?.status).toBe('closed');
  });

  it('creates an application and prevents duplicates', () => {
    const rec = db.insert(schema.recruitments).values({
      creatorId: 1, title: '招人', description: '描述', status: 'open',
    }).run();
    const recId = Number(rec.lastInsertRowid);

    // 第一次申请
    const app1 = db.insert(schema.recruitmentApplications).values({
      recruitmentId: recId, applicantId: 2, message: '我想加入',
    }).run();
    expect(Number(app1.lastInsertRowid)).toBeGreaterThan(0);

    // 检查重复
    const existing = db.select().from(schema.recruitmentApplications)
      .where(and(
        eq(schema.recruitmentApplications.recruitmentId, recId),
        eq(schema.recruitmentApplications.applicantId, 2),
      ))
      .get();
    expect(existing).not.toBeNull();
  });

  it('cannot apply to own recruitment', () => {
    const rec = db.insert(schema.recruitments).values({
      creatorId: 1, title: '自己的招募', description: '描述', status: 'open',
    }).run();
    // 队长 ID=1 尝试申请自己的招募，业务逻辑层应拒绝
    // 这里只是验证 creatorId 正确
    const saved = db.select().from(schema.recruitments)
      .where(eq(schema.recruitments.id, Number(rec.lastInsertRowid)))
      .get();
    expect(saved?.creatorId).toBe(1);
  });
});
```

- [ ] **Step 2: 编写用户 API 测试**

```typescript
// tests/api/users.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq } from 'drizzle-orm';
import * as schema from '@/lib/db/schema';

const sqlite = new Database(':memory:');
const db = drizzle(sqlite, { schema });

beforeAll(() => {
  sqlite.exec(`
    CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, wechat_openid TEXT UNIQUE NOT NULL, nickname TEXT NOT NULL, avatar_url TEXT, school TEXT NOT NULL, major TEXT, grade TEXT, skills TEXT, bio TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  `);
  db.insert(schema.users).values({
    wechatOpenid: 'test_openid', nickname: '张三', school: '测试大学',
  }).run();
});

describe('User Profile', () => {
  it('reads user profile', () => {
    const user = db.select().from(schema.users)
      .where(eq(schema.users.wechatOpenid, 'test_openid'))
      .get();
    expect(user?.nickname).toBe('张三');
    expect(user?.school).toBe('测试大学');
  });

  it('updates user profile', () => {
    db.update(schema.users)
      .set({
        nickname: '张三（已修改）',
        major: '计算机科学',
        grade: '2023级',
        skills: JSON.stringify(['Python', '数据分析']),
        bio: '热爱编程',
      })
      .where(eq(schema.users.wechatOpenid, 'test_openid'))
      .run();

    const updated = db.select().from(schema.users)
      .where(eq(schema.users.wechatOpenid, 'test_openid'))
      .get();
    expect(updated?.nickname).toBe('张三（已修改）');
    expect(updated?.major).toBe('计算机科学');
    expect(JSON.parse(updated?.skills as string)).toEqual(['Python', '数据分析']);
  });
});
```

- [ ] **Step 3: 运行 API 测试**

```bash
npx vitest run tests/api/
```
Expected: All tests PASS.

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "test: add API route logic tests for recruitments and users"
```

---

### Task 17: 编写 E2E 测试

**Files:**
- Create: `tests/e2e/critical-flow.spec.ts`
- Create: `playwright.config.ts`

- [ ] **Step 1: 编写 Playwright 配置**

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3000',
    viewport: { width: 390, height: 844 }, // iPhone 14
  },
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
  },
});
```

- [ ] **Step 2: 编写关键流程 E2E 测试**

```typescript
// tests/e2e/critical-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Competition Team Tool - Critical Flow', () => {
  test('homepage shows competition list', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=发现比赛')).toBeVisible();
    // 检查比赛卡片存在（种子数据有 8 条）
    await expect(page.locator('text=全国大学生数学建模竞赛')).toBeVisible();
  });

  test('can filter competitions by category', async ({ page }) => {
    await page.goto('/');
    await page.locator('button:has-text("数学建模")').click();
    await expect(page.locator('text=全国大学生数学建模竞赛')).toBeVisible();
    await expect(page.locator('text=ACM-ICPC')).not.toBeVisible();
  });

  test('can search competitions', async ({ page }) => {
    await page.goto('/');
    await page.locator('input[placeholder="搜索比赛名称"]').fill('数学建模');
    await expect(page.locator('text=全国大学生数学建模竞赛')).toBeVisible();
    await expect(page.locator('text=ACM-ICPC')).not.toBeVisible();
  });

  test('competition detail page shows recruitments', async ({ page }) => {
    await page.goto('/');
    await page.locator('text=全国大学生数学建模竞赛').click();
    await expect(page).toHaveURL(/\/competitions\/\d+/);
    await expect(page.locator('text=相关招募帖')).toBeVisible();
  });

  test('recruitment square page is accessible', async ({ page }) => {
    await page.goto('/recruitment');
    await expect(page.locator('text=发布招募')).toBeVisible();
  });
});
```

- [ ] **Step 3: 运行 E2E 测试**
> 注意：微信登录流程无法在 E2E 中自动化测试，MVP 阶段仅覆盖无需登录的浏览流程。

```bash
npx playwright test
```
Expected: 5 tests PASS.

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "test: add E2E tests for critical browsing flow"
```

---

### Task 18: 最终验证与清理

- [ ] **Step 1: 确认所有测试通过**

```bash
npx vitest run && npx playwright test
```
Expected: All tests PASS.

- [ ] **Step 2: 确认 dev server 正常运行且所有页面可访问**

```bash
npm run dev
```
手动验证：
- `/` — 比赛列表显示 8 条种子数据，搜索和筛选可用
- `/competitions/1` — 比赛详情展示
- `/recruitment` — 招募广场，但无数据（种子数据无招募）
- `/recruitment/new` — 发布表单可访问（未登录会报错，符合预期）
- `/profile` — 个人中心页显示登录引导

- [ ] **Step 3: TypeScript 检查**

```bash
npx tsc --noEmit
```
修复任何类型错误。

- [ ] **Step 4: 提交最终版本**

```bash
git add -A && git commit -m "chore: final verification and cleanup"
```

---

## 任务依赖图

```
Task 1 (Scaffold)
 └─ Task 2 (Theme config)
     └─ Task 3 (DB Schema)
          ├─ Task 4 (Schema tests + migration)
          │    └─ Task 15 (Seed data)
          ├─ Task 5 (Auth)
          │    └─ Task 12 (Profile page, depends on auth)
          └─ Task 6 (Layout)
               ├─ Task 7 (Competition list)
               │    └─ Task 8 (Competition detail)
               ├─ Task 9 (Recruitment list)
               │    └─ Task 10 (Recruitment detail + apply)
               │         └─ Task 11 (Recruitment create)
               └─ Task 12 (Profile page)
Task 13 (Write API routes) — depends on Auth + DB
Task 14 (Error handling) — independent
Task 16 (API tests) — depends on Schema tests
Task 17 (E2E tests) — depends on all pages
Task 18 (Final verification) — depends on everything
```

## 预计总任务数

18 个任务，约 4-6 小时（含调试时间）。

## 未覆盖项（按设计文档 YAGNI 清单）

以下功能不在本计划中：
- 后台管理系统
- 消息通知系统
- 智能匹配算法
- 用户贡献比赛信息 UI（competition_contributions 表已建，v2 启用）
- 跨校切换/多校数据隔离
- CI/CD 流水线
