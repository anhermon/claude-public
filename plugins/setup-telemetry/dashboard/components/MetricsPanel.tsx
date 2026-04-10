'use client'

import React, { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { MetricsResponse } from '@/lib/types/telemetry'
import { Activity, BarChart2, AlertTriangle, Zap } from 'lucide-react'

interface MetricsPanelProps {
  metrics: MetricsResponse | null
  isLoading: boolean
}

export function MetricsPanel({ metrics, isLoading }: MetricsPanelProps) {
  if (isLoading || !metrics) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-24 mb-3" />
              <div className="h-8 bg-slate-200 rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const formatDuration = (ms: number) => {
    if (!ms) return '0ms'
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  // tool_usage is a dict {toolName: count} - backend returns toolMetrics array
  const toolMetricsData = useMemo(() => {
    const tools = metrics.toolMetrics || []
    return tools
      .sort((a, b) => (b.count || 0) - (a.count || 0))
      .slice(0, 10)
      .map((tool) => ({
        name: tool.name || 'Unknown',
        count: tool.count || 0,
      }))
  }, [metrics.toolMetrics])

  const statusData = useMemo(() => {
    const items = [
      { name: 'Active', value: metrics.activeSessions || 0, color: '#3b82f6' },
      { name: 'Completed', value: metrics.completedSessions || 0, color: '#22c55e' },
      { name: 'Failed', value: metrics.failedSessions || 0, color: '#ef4444' },
    ].filter((d) => d.value > 0)
    return items
  }, [metrics.activeSessions, metrics.completedSessions, metrics.failedSessions])

  const errorData = useMemo(() => {
    return (metrics.errorBreakdown || []).slice(0, 5)
  }, [metrics.errorBreakdown])

  const statCards = [
    {
      label: 'Total Sessions',
      value: (metrics.totalSessions ?? 0).toLocaleString(),
      icon: <Activity className="w-6 h-6 text-blue-500" />,
      accent: 'border-blue-200 bg-blue-50/30',
    },
    {
      label: 'Active Sessions',
      value: (metrics.activeSessions ?? 0).toLocaleString(),
      icon: <Zap className="w-6 h-6 text-emerald-500" />,
      accent: 'border-emerald-200 bg-emerald-50/30',
    },
    {
      label: 'Avg Event Duration',
      value: formatDuration(metrics.averageSessionDuration ?? 0),
      icon: <BarChart2 className="w-6 h-6 text-slate-500" />,
      accent: 'border-slate-200',
    },
    {
      label: 'Error Events',
      value: (metrics.errorBreakdown?.reduce((s, e) => s + e.count, 0) ?? 0).toLocaleString(),
      icon: <AlertTriangle className="w-6 h-6 text-red-400" />,
      accent: 'border-red-200 bg-red-50/20',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Big Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div
            key={card.label}
            className={`bg-white border rounded-lg p-6 ${card.accent}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">{card.label}</p>
                <p className="text-3xl font-bold text-slate-900 mt-2 tabular-nums">{card.value}</p>
              </div>
              <div className="mt-1">{card.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Session Status Distribution */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Session Status</h3>
          {statusData.length > 0 ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => value.toLocaleString()} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-3">
                {statusData.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: entry.color }} />
                    <span className="text-sm text-slate-600">{entry.name}</span>
                    <span className="text-sm font-semibold text-slate-900 ml-auto pl-4">
                      {entry.value.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
              No session data yet
            </div>
          )}
        </div>

        {/* Top Tools */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Top Tools by Usage</h3>
          {toolMetricsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={toolMetricsData}
                layout="vertical"
                margin={{ left: 80, right: 24, top: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis dataKey="name" type="category" width={76} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value: number) => [value.toLocaleString(), 'Uses']} />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 3, 3, 0]} name="Uses" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
              No tool usage data yet
            </div>
          )}
        </div>

        {/* Error Breakdown */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Error Breakdown</h3>
          {errorData.length > 0 ? (
            <div className="space-y-4">
              {errorData.map((error, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-slate-700 font-mono">
                      {error.errorType || 'Unknown'}
                    </span>
                    <div className="text-right">
                      <span className="text-sm font-semibold text-slate-900">{error.count.toLocaleString()}</span>
                      <span className="text-xs text-slate-500 ml-1">({(error.percentage || 0).toFixed(1)}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5">
                    <div
                      className="bg-red-400 h-1.5 rounded-full transition-all"
                      style={{ width: `${Math.min(error.percentage || 0, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
              No errors recorded
            </div>
          )}
        </div>

        {/* Session Totals Summary */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Session Summary</h3>
          <div className="space-y-3">
            {[
              { label: 'Total Sessions', value: (metrics.totalSessions ?? 0).toLocaleString() },
              { label: 'Active', value: (metrics.activeSessions ?? 0).toLocaleString() },
              { label: 'Completed', value: (metrics.completedSessions ?? 0).toLocaleString() },
              { label: 'Failed', value: (metrics.failedSessions ?? 0).toLocaleString() },
              { label: 'Avg Duration', value: formatDuration(metrics.averageSessionDuration ?? 0) },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-1 border-b border-slate-100 last:border-0">
                <span className="text-sm text-slate-600">{label}</span>
                <span className="text-sm font-semibold text-slate-900 tabular-nums">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
