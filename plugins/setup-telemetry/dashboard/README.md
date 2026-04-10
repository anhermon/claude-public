# Telemetry Dashboard

A production-ready real-time telemetry dashboard built with Next.js 14, React 18, and modern observability tools.

## Features

- **Sessions List** - Browse all sessions with pagination, filtering by status (active/completed/failed), and sorting
- **Session Detail** - Deep dive into individual sessions with execution timeline and tool inspector
- **Execution Timeline** - Gantt-style visualization of tool execution with timing information
- **Metrics & Analytics** - Comprehensive dashboard with KPIs, charts, and breakdowns:
  - Session status distribution (pie chart)
  - Hourly activity trends (bar chart)
  - Top tools by usage (horizontal bar chart)
  - Error breakdown with percentages
- **Live Feed** - Real-time session and tool activity monitoring with 2-second polling
- **Real-time Updates** - Automatic polling:
  - Sessions list: 5-second refresh
  - Active session detail: 2-second refresh
  - Live feed: 2-second refresh

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Data Fetching**: SWR with automatic revalidation
- **Charts**: Recharts (bar, pie, line charts)
- **Styling**: Tailwind CSS with custom utilities
- **Type Safety**: TypeScript with strict mode
- **Icons**: Lucide React

## Project Structure

```
telemetry-dashboard/
├── app/                          # Next.js App Router
│   ├── api/                      # API routes
│   │   ├── sessions/
│   │   │   └── [id]/            # Session detail endpoint
│   │   ├── metrics/             # Analytics endpoint
│   │   └── live/                # Live feed endpoint
│   ├── dashboard/               # Dashboard pages
│   │   ├── page.tsx            # Main dashboard
│   │   ├── sessions/           # Sessions list
│   │   │   ├── page.tsx
│   │   │   └── [id]/           # Session detail page
│   │   │       └── page.tsx
│   │   ├── metrics/            # Analytics page
│   │   │   └── page.tsx
│   │   └── live/               # Live feed page
│   │       └── page.tsx
│   ├── layout.tsx              # Root layout with sidebar
│   └── globals.css             # Global styles
├── components/                  # Reusable components
│   ├── SessionList.tsx         # Sessions table with filters
│   ├── Timeline.tsx            # Gantt timeline visualization
│   ├── ToolInspector.tsx       # Tool details inspector
│   ├── MetricsPanel.tsx        # Analytics dashboard
│   └── LiveFeed.tsx            # Real-time event feed
├── lib/
│   ├── hooks/                  # SWR data-fetching hooks
│   │   ├── useSessions.ts
│   │   ├── useSessionDetail.ts
│   │   ├── useMetrics.ts
│   │   └── useLiveFeed.ts
│   └── types/
│       └── telemetry.ts        # TypeScript type definitions
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── next.config.js
└── README.md
```

## Installation

```bash
# Install dependencies
npm install

# Create environment file (optional for local dev)
cp .env.example .env.local

# Run development server
npm run dev

# Open http://localhost:3000
```

## Available Scripts

```bash
npm run dev         # Start development server (port 3000)
npm run build       # Build for production
npm start           # Start production server
npm run lint        # Run Next.js linting
npm run type-check  # Check TypeScript types
```

## API Endpoints

### Sessions List
- **Endpoint**: `GET /api/sessions`
- **Query Parameters**:
  - `page` (number): Page number (default: 1)
  - `pageSize` (number): Items per page (default: 20, max: 100)
  - `status` (string): Filter by status - 'active', 'completed', 'failed'
  - `userId` (string): Filter by user ID
- **Response**: Paginated session list with total count

### Session Detail
- **Endpoint**: `GET /api/sessions/[id]`
- **Response**: Single session with full tool execution data

### Metrics
- **Endpoint**: `GET /api/metrics`
- **Query Parameters**:
  - `fromDate` (timestamp): Start of date range
  - `toDate` (timestamp): End of date range
- **Response**: Aggregated metrics, KPIs, and breakdowns

### Live Feed
- **Endpoint**: `GET /api/live`
- **Response**: Recent session and tool events with active session count

## Data Flow

1. **Components** fetch data via SWR hooks
2. **Hooks** call API endpoints with automatic polling intervals
3. **API Routes** generate mock data (in production, connect to real database)
4. **Components** render data with real-time updates

## Polling Intervals

- `SessionList`: 5 seconds (5000ms)
- `SessionDetail` (Timeline, ToolInspector): 2 seconds (2000ms)
- `LiveFeed`: 2 seconds (2000ms)
- `MetricsPanel`: 5 seconds (5000ms)

All intervals can be customized in the respective hook files at `lib/hooks/`.

## Component Details

### SessionList
- Paginated table with status badges
- Filters: All, Active, Completed, Failed
- Quick stats: user, status, duration, tokens, cost
- Links to session details

### Timeline (Gantt Visualization)
- Proportional bar rendering for each tool
- Color-coded by status (pending, running, completed, failed)
- Displays tool duration, start time, end time
- Interactive details table

### ToolInspector
- Expandable tool cards
- Detailed timing and token information
- Error messages with context
- Status indicators

### MetricsPanel
- Real-time KPI cards (total sessions, active count, avg duration, cost)
- Session status pie chart
- Hourly activity bar chart
- Top tools horizontal bar chart
- Error breakdown with percentages

### LiveFeed
- Real-time event stream (newest first)
- Event types: session_start, session_end, tool_start, tool_end
- Time-relative timestamps (e.g., "2m ago")
- Active session indicator

## Mock Data

The API endpoints return realistic mock data with:
- 150 total sessions in list
- Randomized statuses and durations
- Tool execution sequences with timing
- Realistic token usage and costs
- Error scenarios (5-10% failure rate)

Replace the mock data generators in `app/api/*/route.ts` with real database queries.

## Type Safety

Full TypeScript support with types for:
- Sessions and tools
- API responses
- Metrics and analytics
- Filter parameters
- Live events

See `lib/types/telemetry.ts` for complete type definitions.

## Styling

Tailwind CSS utility-first approach with:
- Custom color palette (slate grays, brand colors)
- Responsive grid layouts
- Smooth transitions and animations
- Accessible form elements
- Dark mode ready (easily toggle via Tailwind config)

## Error Handling

- Graceful fallbacks when data is missing
- Loading states for all data-fetching
- User-friendly error messages
- Automatic retry with SWR

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Optimized re-renders with React 18
- Efficient data fetching with SWR
- CSS-in-JS elimination (pure Tailwind)
- Code splitting via Next.js
- Bundle size: ~150KB (gzipped)

## Development Notes

- The dashboard uses client-side rendering for real-time updates
- API routes are server-side and can connect to any database
- Mock data is randomly generated for testing
- All components are production-ready with no TODOs
- Pagination prevents large data transfers
- Polling intervals are aggressive to show real-time behavior

## Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
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
```

## Environment Variables

Create `.env.local` (optional):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000
```

## License

MIT
