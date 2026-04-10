'use client'

import useSWR from 'swr'
import { SessionDetailResponse } from '@/lib/types/telemetry'

const BACKEND_URL = 'http://localhost:5001'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function useSessionDetail(sessionId: string) {
  const { data, error, isLoading, mutate } = useSWR<SessionDetailResponse>(
    sessionId ? `${BACKEND_URL}/sessions/${encodeURIComponent(sessionId)}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 5000,
    }
  )

  return {
    session: data?.session ?? null,
    isLoading,
    isError: !!error,
    mutate,
  }
}
