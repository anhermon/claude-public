import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') || '5'

    const backendUrl = new URL('http://localhost:5001/sessions')
    backendUrl.searchParams.append('status', 'active')
    backendUrl.searchParams.append('limit', limit)

    const backendResponse = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!backendResponse.ok) {
      throw new Error(`Backend returned ${backendResponse.status}`)
    }

    const data = await backendResponse.json()

    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'no-store, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Error fetching live feed:', error)
    return NextResponse.json(
      { error: 'Failed to fetch live feed from backend' },
      { status: 500 }
    )
  }
}
