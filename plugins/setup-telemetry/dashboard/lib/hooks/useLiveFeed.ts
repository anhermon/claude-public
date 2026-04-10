'use client'

import useSWR from 'swr'
import { SessionListResponse } from '@/lib/types/telemetry'

const BACKEND_URL = 'http://localhost:5001'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function useLiveFeed() {
  const { data, error, isLoading, mutate } = useSWR<SessionListResponse>(
    `${BACKEND_URL}/sessions?status=active&limit=5`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 3000,
    }
  )

  const activeSessions = data?.sessions ?? []

  return {
    activeSessions,
    activeSessionCount: activeSessions.length,
    isLoading,
    isError: !!error,
    mutate,
  }
}
