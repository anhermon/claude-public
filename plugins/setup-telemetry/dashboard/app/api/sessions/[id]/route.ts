import { NextRequest, NextResponse } from 'next/server'
import { SessionDetailResponse } from '@/lib/types/telemetry'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params

    // Validate session ID format
    if (!id || typeof id !== 'string') {
      return NextResponse.json(
        { error: 'Invalid session ID' },
        { status: 400 }
      )
    }

    // Fetch session from FastAPI backend
    const backendUrl = `http://localhost:5001/sessions/${encodeURIComponent(id)}`

    const backendResponse = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!backendResponse.ok) {
      if (backendResponse.status === 404) {
        return NextResponse.json(
          { error: 'Session not found' },
          { status: 404 }
        )
      }
      throw new Error(`Backend returned ${backendResponse.status}`)
    }

    const response = await backendResponse.json() as SessionDetailResponse

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Error fetching session:', error)
    return NextResponse.json(
      { error: 'Failed to fetch session from backend' },
      { status: 500 }
    )
  }
}
