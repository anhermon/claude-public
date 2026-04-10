import { NextRequest, NextResponse } from 'next/server'
import { MetricsResponse } from '@/lib/types/telemetry'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const fromDate = parseInt(searchParams.get('fromDate') || '0', 10)
    const toDate = parseInt(searchParams.get('toDate') || Date.now().toString(), 10)

    // Fetch metrics from FastAPI backend
    const backendUrl = new URL('http://localhost:5001/metrics')
    backendUrl.searchParams.append('fromDate', fromDate.toString())
    backendUrl.searchParams.append('toDate', toDate.toString())

    const backendResponse = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!backendResponse.ok) {
      throw new Error(`Backend returned ${backendResponse.status}`)
    }

    const response = await backendResponse.json() as MetricsResponse

    return NextResponse.json(response, {
      headers: {
        'Cache-Control': 'no-store, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Error fetching metrics:', error)
    return NextResponse.json(
      { error: 'Failed to fetch metrics from backend' },
      { status: 500 }
    )
  }
}
