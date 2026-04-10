export interface Tool {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime: number
  endTime: number
  duration: number
  error?: string
  inputTokens?: number
  outputTokens?: number
}

export interface Session {
  id: string
  userId: string
  userEmail: string
  status: 'active' | 'completed' | 'failed'
  startTime: number
  endTime?: number
  duration?: number
  tools: Tool[]
  inputTokens: number
  outputTokens: number
  totalCost: number
  errorMessage?: string
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface SessionDetailResponse {
  session: Session
}

export interface MetricsResponse {
  totalSessions: number
  activeSessions: number
  completedSessions: number
  failedSessions: number
  averageSessionDuration: number
  totalTokensUsed: number
  totalCost: number
  toolMetrics: ToolMetric[]
  errorBreakdown: ErrorMetric[]
  sessionsByHour: HourlyMetric[]
}

export interface ToolMetric {
  name: string
  count: number
  averageDuration: number
  failureRate: number
  averageCost: number
}

export interface ErrorMetric {
  errorType: string
  count: number
  percentage: number
}

export interface HourlyMetric {
  hour: number
  sessions: number
  avgDuration: number
}

export interface LiveSessionEvent {
  sessionId: string
  type: 'session_start' | 'session_end' | 'tool_start' | 'tool_end'
  timestamp: number
  data: {
    userId?: string
    userEmail?: string
    toolName?: string
    status?: string
    duration?: number
  }
}

export interface LiveFeedResponse {
  events: LiveSessionEvent[]
  activeSessionCount: number
}

export type SessionFilter = {
  status?: 'active' | 'completed' | 'failed'
  userId?: string
  fromDate?: number
  toDate?: number
}
