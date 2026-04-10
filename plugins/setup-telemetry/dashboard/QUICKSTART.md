# Quick Start Guide

Get the telemetry dashboard running in 60 seconds.

## Prerequisites

- Node.js 18+ (includes npm)
- 200MB disk space

## Installation & Running

```bash
# 1. Navigate to project
cd /Users/angelhermon/.paperclip/instances/telemetry-dashboard

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Open browser
# http://localhost:3000/dashboard
```

The dashboard is now live with real-time data polling.

## What You'll See

### Sidebar Navigation
- Dashboard (analytics overview)
- Sessions (browsable list with filters)
- Metrics (detailed analytics)
- Live Feed (real-time event stream)

### Pages

1. **Dashboard** (`/dashboard`)
   - KPI cards: total sessions, active count, avg duration, cost
   - Session status pie chart
   - Hourly activity bar chart
   - Top tools by usage
   - Error breakdown

2. **Sessions** (`/dashboard/sessions`)
   - Paginated table (20 per page)
   - Status filters: All, Active, Completed, Failed
   - Quick stats: user, duration, tokens, cost
   - Click row to view session detail

3. **Session Detail** (`/dashboard/sessions/[id]`)
   - Full session timeline with Gantt bars
   - Tool execution inspector (expandable cards)
   - Detailed metrics and error info

4. **Metrics** (`/dashboard/metrics`)
   - Same as dashboard with time range selector
   - 24 Hours, 7 Days, 30 Days views

5. **Live Feed** (`/dashboard/live`)
   - Real-time event stream
   - Active session counter
   - Event types: session start/end, tool start/end
   - Auto-updates every 2 seconds

## Data & Polling

All data is **mocked** and randomly generated. Polling intervals:

| Feature | Interval |
|---------|----------|
| Sessions list | 5 seconds |
| Session detail | 2 seconds |
| Live feed | 2 seconds |
| Metrics | 5 seconds |

To connect real data, replace the mock generators in `app/api/*/route.ts`.

## Development Commands

```bash
npm run dev         # Start dev server (http://localhost:3000)
npm run build       # Production build
npm start           # Run production build
npm run lint        # Check code quality
npm run type-check  # Validate TypeScript
```

## File Locations

| Component | Path |
|-----------|------|
| API endpoints | `app/api/` |
| Pages | `app/dashboard/` |
| React components | `components/` |
| Data hooks | `lib/hooks/` |
| Type definitions | `lib/types/telemetry.ts` |
| Styles | `app/globals.css` + Tailwind |

## Browser Compatibility

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Common Issues

**Port already in use?**
```bash
# Use different port
PORT=3001 npm run dev
```

**Build errors?**
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

**Styles not loading?**
```bash
# Rebuild Tailwind
npm run build
```

## Deployment

### Vercel (1 click)
```bash
npm install -g vercel
vercel
```

### Docker
```bash
docker build -t telemetry-dashboard .
docker run -p 3000:3000 telemetry-dashboard
```

### Traditional Server
```bash
npm run build
npm start
```

## API Endpoints (Local)

If you want to call the APIs directly:

```bash
# Get sessions (page 1, 20 per page)
curl http://localhost:3000/api/sessions?page=1&pageSize=20

# Get session detail
curl http://localhost:3000/api/sessions/sess-000000

# Get metrics
curl http://localhost:3000/api/metrics

# Get live feed
curl http://localhost:3000/api/live
```

## Next Steps

1. Replace mock data in `app/api/*/route.ts` with real database queries
2. Add authentication/authorization as needed
3. Connect to your actual telemetry backend
4. Customize colors/theme in `tailwind.config.ts`
5. Deploy to Vercel or your preferred hosting

## Support

See `README.md` for full documentation.
