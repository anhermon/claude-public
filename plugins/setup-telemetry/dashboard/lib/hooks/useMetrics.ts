'use client'

import useSWR from 'swr'
import { MetricsResponse } from '@/lib/types/telemetry'

const BACKEND_URL = 'http://localhost:5001'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function useMetrics(fromDate?: number, toDate?: number) {
  const { data, error, isLoading, mutate } = useSWR<MetricsResponse>(
    `${BACKEND_URL}/metrics`,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 5000,
    }
  )

  return {
    metrics: data ?? null,
    isLoading,
    isError: !!error,
    mutate,
  }
}
