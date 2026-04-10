'use client'

import useSWR from 'swr'
import { SessionListResponse, SessionFilter } from '@/lib/types/telemetry'

const BACKEND_URL = 'http://localhost:5001'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function useSessions(
  page: number = 1,
  pageSize: number = 20,
  filters?: SessionFilter
) {
  const skip = (page - 1) * pageSize
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: pageSize.toString(),
  })

  if (filters?.status) params.append('status', filters.status)

  const { data, error, isLoading, mutate } = useSWR<SessionListResponse>(
    `${BACKEND_URL}/sessions?${params.toString()}`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 5000,
    }
  )

  return {
    sessions: data?.sessions ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? 1,
    pageSize: data?.pageSize ?? 20,
    totalPages: data?.totalPages ?? 1,
    isLoading,
    isError: !!error,
    mutate,
  }
}
