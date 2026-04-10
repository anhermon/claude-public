'use client'

import { useMetrics } from '@/lib/hooks/useMetrics'
import { MetricsPanel } from '@/components/MetricsPanel'

export default function DashboardPage() {
  const { metrics, isLoading } = useMetrics()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-2">Real-time telemetry overview and analytics</p>
      </div>

      <MetricsPanel metrics={metrics} isLoading={isLoading} />
    </div>
  )
}
