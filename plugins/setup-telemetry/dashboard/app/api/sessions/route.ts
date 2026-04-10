import { NextRequest, NextResponse } from 'next/server'
import { SessionListResponse } from '@/lib/types/telemetry'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('pageSize') || '20', 10)
    const status = searchParams.get('status')

    // Validate pagination
    if (page < 1 || pageSize < 1 || pageSize > 100) {
      return NextResponse.json(
        { error: 'Invalid pagination parameters' },
        { status: 400 }
      )
    }

    // Fetch sessions from FastAPI backend
    const skip = (page - 1) * pageSize
    const backendUrl = new URL('http://localhost:5001/sessions')
    backendUrl.searchParams.append('skip', skip.toString())
    backendUrl.searchParams.append('limit', pageSize.toString())
    if (status) backendUrl.searchParams.append('status', status)

    const backendResponse = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!backendResponse.ok) {
      throw new Error(`Backend returned ${backendResponse.status}`)
    }

    const backendSessions = await backendResponse.json() as Array<{
      id: string
      created_at: string
      ended_at: string | null
      custom_data: Record<string, any> | null
      event_count: number
      tool_use_count: number
      error_count: number
      total_duration_ms: number
    }>

    // Transform backend sessions to dashboard format
    const sessions = backendSessions.map((session) => ({
      id: session.id,
      userId: session.custom_data?.user_id || 'unknown',
      userEmail: session.custom_data?.user_email || 'unknown@example.com',
      status: (session.ended_at ? 'completed' : 'active') as 'active' | 'completed' | 'failed',
      startTime: new Date(session.created_at).getTime(),
      endTime: session.ended_at ? new Date(session.ended_at).getTime() : undefined,
      duration: session.total_duration_ms,
      tools: [],
      inputTokens: 0,
      outputTokens: 0,
      totalCost: 0,
    }))

    // Get total count
    const countUrl = new URL('http://localhost:5001/sessions/count')
    if (status) countUrl.searchParams.append('status', status)

    const countResponse = await fetch(countUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const countData = countResponse.ok ? (await countResponse.json() as { count: number }) : { count: 0 }
    const total = countData.count
    const totalPages = Math.ceil(total / pageSize)

    const response: SessionListResponse = {
      sessions,
      total,
      page,
      pageSize,
      totalPages,
    }

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Error fetching sessions:', error)
    return NextResponse.json(
      { error: 'Failed to fetch sessions from backend' },
      { status: 500 }
    )
  }
}
