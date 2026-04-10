# Telemetry Dashboard - Entry Points & URLs

## Local Development

**Start server:**
```bash
cd /Users/angelhermon/.paperclip/instances/telemetry-dashboard
npm install
npm run dev
```

**Access at:** http://localhost:3000/dashboard

## Web Routes (Frontend)

All routes are in the `/dashboard` namespace and require the App Router.

| Route | Component | File | Features |
|-------|-----------|------|----------|
| `/dashboard` | Main Dashboard | `app/dashboard/page.tsx` | KPIs, pie chart, bar charts, analytics |
| `/dashboard/sessions` | Sessions List | `app/dashboard/sessions/page.tsx` | Pagination, filters, table, 5s polling |
| `/dashboard/sessions/[id]` | Session Detail | `app/dashboard/sessions/[id]/page.tsx` | Timeline, tool inspector, metadata, 2s polling |
| `/dashboard/metrics` | Analytics | `app/dashboard/metrics/page.tsx` | Same as dashboard + time range selector |
| `/dashboard/live` | Live Feed | `app/dashboard/live/page.tsx` | Real-time events, 2s polling, active counter |

## API Routes (Backend)

All API routes return JSON with no-cache headers.

| Route | Method | File | Returns |
|-------|--------|------|---------|
| `/api/sessions` | GET | `app/api/sessions/route.ts` | SessionListResponse |
| `/api/sessions/[id]` | GET | `app/api/sessions/[id]/route.ts` | SessionDetailResponse |
| `/api/metrics` | GET | `app/api/metrics/route.ts` | MetricsResponse |
| `/api/live` | GET | `app/api/live/route.ts` | LiveFeedResponse |

### API Query Parameters

**GET /api/sessions**
```
?page=1              # Page number (default: 1)
&pageSize=20         # Items per page (default: 20, max: 100)
&status=active       # Filter: active|completed|failed (optional)
&userId=user-123     # Filter by user ID (optional)
```

**GET /api/metrics**
```
?fromDate=1234567890 # Unix timestamp start (optional)
&toDate=1234567890   # Unix timestamp end (optional)
```

**GET /api/live**
```
# No parameters
```

## React Components

Components are in `/components` and are client-rendered.

| Component | File | Props | Used In |
|-----------|------|-------|---------|
| SessionList | `components/SessionList.tsx` | None (uses hook) | Sessions page |
| Timeline | `components/Timeline.tsx` | `tools: Tool[]`, `startTime: number` | Session detail |
| ToolInspector | `components/ToolInspector.tsx` | `tools: Tool[]` | Session detail |
| MetricsPanel | `components/MetricsPanel.tsx` | `metrics: MetricsResponse \| null`, `isLoading: boolean` | Dashboard, Metrics page |
| LiveFeed | `components/LiveFeed.tsx` | None (uses hook) | Live page |

## SWR Hooks

Hooks are in `/lib/hooks` and handle data fetching with polling.

| Hook | File | Returns | Polling |
|------|------|---------|---------|
| useSessions | `lib/hooks/useSessions.ts` | { sessions[], total, page, pageSize, totalPages, isLoading, isError, mutate } | 5s |
| useSessionDetail | `lib/hooks/useSessionDetail.ts` | { session, isLoading, isError, mutate } | 2s |
| useMetrics | `lib/hooks/useMetrics.ts` | { metrics, isLoading, isError, mutate } | 5s |
| useLiveFeed | `lib/hooks/useLiveFeed.ts` | { events[], activeSessionCount, isLoading, isError, mutate } | 2s |

### Hook Usage Example

```typescript
import { useSessions } from '@/lib/hooks/useSessions'

export function MyComponent() {
  const { sessions, totalPages, isLoading } = useSessions(page, pageSize, filters)
  
  if (isLoading) return <div>Loading...</div>
  return <div>{sessions.map(s => <div key={s.id}>{s.userEmail}</div>)}</div>
}
```

## Type Definitions

All types are in `lib/types/telemetry.ts`:

```typescript
// Session entities
Session
Tool

// API responses
SessionListResponse
SessionDetailResponse
MetricsResponse
ToolMetric
ErrorMetric
HourlyMetric

// Live feed
LiveFeedResponse
LiveSessionEvent
LiveSessionEvent['type']  // 'session_start' | 'session_end' | 'tool_start' | 'tool_end'

// Filters
SessionFilter
```

## Sidebar Navigation

The sidebar is in `app/layout.tsx` with these links:

```
Dashboard  → /dashboard
Sessions   → /dashboard/sessions
Metrics    → /dashboard/metrics
Live Feed  → /dashboard/live
```

## Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| package.json | Dependencies & scripts | Root |
| tsconfig.json | TypeScript config (strict mode) | Root |
| next.config.js | Next.js config | Root |
| tailwind.config.ts | Tailwind CSS theme | Root |
| postcss.config.js | PostCSS plugins | Root |

## Environment Setup

**Required environment variable:**
```bash
NODE_ENV=development  # or production
```

**Optional:**
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
```

See `env.example` for template.

## Development Commands

```bash
npm run dev           # Start dev server (localhost:3000)
npm run build         # Build for production
npm start             # Run production build
npm run lint          # Run ESLint
npm run type-check    # Run TypeScript compiler
```

## File Structure Quick Reference

```
telemetry-dashboard/
├── app/                       # Next.js App Router
│   ├── api/                   # API endpoints
│   ├── dashboard/             # Page routes
│   ├── layout.tsx             # Root layout
│   └── globals.css            # Global styles
├── components/                # React components
├── lib/
│   ├── hooks/                 # SWR data hooks
│   └── types/telemetry.ts     # Type definitions
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── Dockerfile
├── README.md
├── QUICKSTART.md
└── PROJECT_SUMMARY.txt
```

## Common Development Tasks

### Add a new page
1. Create file: `app/dashboard/mypage/page.tsx`
2. Export default React component
3. Sidebar automatically picks it up if you add the link

### Add a new API endpoint
1. Create file: `app/api/myendpoint/route.ts`
2. Export `GET`, `POST`, etc. functions
3. Return `NextResponse.json(data)`

### Add a new hook
1. Create file: `lib/hooks/useMyData.ts`
2. Use `useSWR()` for polling
3. Export hook function

### Update Tailwind theme
Edit `tailwind.config.ts` and restart dev server

### Change polling intervals
Edit the `refreshInterval` in `/lib/hooks/*.ts` files (milliseconds)

## Debugging

**View network requests:**
- Open DevTools (F12)
- Go to Network tab
- Interact with dashboard
- Watch API calls to `/api/sessions`, `/api/metrics`, etc.

**View real-time updates:**
- Open Console (F12)
- SWR will show "revalidating" messages

**Mock data location:**
- Sessions: `app/api/sessions/route.ts` - `generateMockSessions()`
- Detail: `app/api/sessions/[id]/route.ts` - `generateMockSession()`
- Metrics: `app/api/metrics/route.ts`
- Live: `app/api/live/route.ts` - `generateMockLiveEvents()`

## Production Deployment

### Vercel (Recommended)
```bash
vercel
# Follow prompts
```

### Docker
```bash
docker build -t telemetry-dashboard .
docker run -p 3000:3000 telemetry-dashboard
```

### Traditional Node
```bash
npm run build
npm start
# Runs on port 3000
```

## Troubleshooting

**Port 3000 in use?**
```bash
PORT=3001 npm run dev
```

**Styles not loading?**
```bash
npm run build
```

**TypeScript errors?**
```bash
npm run type-check
```

**Fresh install needed?**
```bash
rm -rf node_modules .next
npm install
npm run dev
```
