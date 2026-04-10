'use client'

import { useState } from 'react'
import { useMetrics } from '@/lib/hooks/useMetrics'
import { MetricsPanel } from '@/components/MetricsPanel'

export default function MetricsPage() {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  const getFromDate = () => {
    const now = Date.now()
    switch (timeRange) {
      case '24h':
        return now - 24 * 60 * 60 * 1000
      case '7d':
        return now - 7 * 24 * 60 * 60 * 1000
      case '30d':
        return now - 30 * 24 * 60 * 60 * 1000
    }
  }

  const { metrics, isLoading } = useMetrics(getFromDate(), Date.now())

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Analytics & Metrics</h1>
          <p className="text-slate-600 mt-2">Detailed performance and usage analytics</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setTimeRange('24h')}
            className={`px-4 py-2 rounded font-medium transition ${
              timeRange === '24h'
                ? 'bg-slate-900 text-white'
                : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            24 Hours
          </button>
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-4 py-2 rounded font-medium transition ${
              timeRange === '7d'
                ? 'bg-slate-900 text-white'
                : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            7 Days
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-4 py-2 rounded font-medium transition ${
              timeRange === '30d'
                ? 'bg-slate-900 text-white'
                : 'bg-slate-200 text-slate-900 hover:bg-slate-300'
            }`}
          >
            30 Days
          </button>
        </div>
      </div>

      <MetricsPanel metrics={metrics} isLoading={isLoading} />
    </div>
  )
}
