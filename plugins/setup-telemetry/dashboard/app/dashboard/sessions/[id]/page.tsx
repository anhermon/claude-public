'use client'

import { useSessionDetail } from '@/lib/hooks/useSessionDetail'
import Link from 'next/link'
import { Loader2, ArrowLeft, AlertCircle, Terminal, Clock, Zap, AlertTriangle } from 'lucide-react'

interface SessionDetailPageProps {
  params: {
    id: string
  }
}

export default function SessionDetailPage({ params }: SessionDetailPageProps) {
  const { session, isLoading, isError } = useSessionDetail(params.id)

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString([], {
      dateStyle: 'medium',
      timeStyle: 'medium',
    })
  }

  const formatDuration = (ms: number) => {
    if (!ms) return '—'
    if (ms < 1000) return `${Math.round(ms)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-slate-100 text-slate-800'
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/sessions" className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition">
          <ArrowLeft className="w-4 h-4" />
          Back to Sessions
        </Link>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400 mr-3" />
          <span className="text-slate-500">Loading session details...</span>
        </div>
      </div>
    )
  }

  if (isError || !session) {
    return (
      <div className="space-y-6">
        <Link href="/dashboard/sessions" className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition">
          <ArrowLeft className="w-4 h-4" />
          Back to Sessions
        </Link>
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-500">
          <AlertCircle className="w-8 h-8 text-red-300" />
          <p className="font-medium">Session not found or failed to load.</p>
          <p className="text-sm text-slate-400">Check the session ID and try again.</p>
        </div>
      </div>
    )
  }

  const tools = session.tools || []

  const statCards = [
    {
      label: 'Started',
      value: formatDate(session.startTime),
      icon: <Clock className="w-5 h-5 text-slate-400" />,
    },
    {
      label: 'Duration',
      value: session.duration ? formatDuration(session.duration) : 'Ongoing',
      icon: <Zap className="w-5 h-5 text-blue-400" />,
      valueClass: !session.duration ? 'text-blue-600' : undefined,
    },
    {
      label: 'Tools Used',
      value: tools.length.toLocaleString(),
      icon: <Terminal className="w-5 h-5 text-slate-400" />,
    },
    {
      label: 'Errors',
      value: tools.filter((t) => t.status === 'failed').length.toLocaleString(),
      icon: <AlertTriangle className="w-5 h-5 text-red-300" />,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Back nav */}
      <Link
        href="/dashboard/sessions"
        className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Sessions
      </Link>

      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Session ID</p>
            <h1 className="text-lg font-mono font-semibold text-slate-900 break-all">{params.id}</h1>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium flex-shrink-0 ${getStatusColor(
              session.status
            )}`}
          >
            {session.status === 'active' && (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            )}
            {session.status}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statCards.map((card) => (
            <div key={card.label} className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1.5">
                {card.icon}
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.label}</p>
              </div>
              <p className={`text-sm font-semibold text-slate-900 ${card.valueClass || ''}`}>
                {card.value}
              </p>
            </div>
          ))}
        </div>

        {session.errorMessage && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">Error</p>
            <p className="text-sm text-red-700 font-mono">{session.errorMessage}</p>
          </div>
        )}
      </div>

      {/* Event Timeline */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-4">Event Timeline</h2>

        {tools.length === 0 ? (
          <div className="text-center py-10 text-slate-400">
            <Terminal className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No tool events recorded for this session.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {[...tools]
              .sort((a, b) => a.startTime - b.startTime)
              .map((tool, index) => (
                <div
                  key={tool.id || index}
                  className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50 transition"
                >
                  {/* timeline dot */}
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-0.5 ${
                    tool.status === 'completed' ? 'bg-green-500' :
                    tool.status === 'failed' ? 'bg-red-500' :
                    tool.status === 'running' ? 'bg-blue-500 animate-pulse' :
                    'bg-slate-400'
                  }`} />

                  <div className="flex-1 min-w-0 flex items-center gap-3 flex-wrap">
                    {/* Tool name badge */}
                    <span className="inline-block px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-mono font-medium">
                      {tool.name}
                    </span>

                    {/* Timestamp */}
                    <span className="text-xs text-slate-400 tabular-nums">
                      {new Date(tool.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>

                    {/* Status badge */}
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                      tool.status === 'completed' ? 'bg-green-100 text-green-700' :
                      tool.status === 'failed' ? 'bg-red-100 text-red-700' :
                      tool.status === 'running' ? 'bg-blue-100 text-blue-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {tool.status}
                    </span>

                    {tool.error && (
                      <span className="text-xs text-red-600 font-mono truncate max-w-xs">
                        {tool.error}
                      </span>
                    )}
                  </div>

                  {/* Duration pill */}
                  <div className="flex-shrink-0">
                    <span className="inline-block px-2 py-0.5 bg-slate-50 border border-slate-200 rounded-full text-xs text-slate-500 tabular-nums">
                      {formatDuration(tool.duration)}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  )
}
