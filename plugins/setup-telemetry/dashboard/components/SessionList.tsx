'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useSessions } from '@/lib/hooks/useSessions'
import { Session, SessionFilter } from '@/lib/types/telemetry'
import { ChevronLeft, ChevronRight, Loader2, Terminal, ArrowRight } from 'lucide-react'

export function SessionList() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<'active' | 'completed' | 'failed' | undefined>()

  const filters: SessionFilter = {
    status: statusFilter,
  }

  const { sessions, totalPages, isLoading } = useSessions(page, 20, filters)

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`
  }

  const getStatusBadgeColor = (status: Session['status']) => {
    switch (status) {
      case 'active':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
    }
  }

  const filterButtons = [
    { label: 'All', value: undefined, active: 'bg-slate-900 text-white' },
    { label: 'Active', value: 'active' as const, active: 'bg-blue-600 text-white' },
    { label: 'Completed', value: 'completed' as const, active: 'bg-green-600 text-white' },
    { label: 'Failed', value: 'failed' as const, active: 'bg-red-600 text-white' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Sessions</h1>
        <div className="flex gap-2">
          {filterButtons.map(({ label, value, active }) => (
            <button
              key={label}
              onClick={() => {
                setStatusFilter(value)
                setPage(1)
              }}
              className={`px-4 py-2 rounded text-sm font-medium transition ${
                statusFilter === value
                  ? active
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {isLoading && sessions.length === 0 ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400 mr-2" />
          <span className="text-slate-500">Loading sessions...</span>
        </div>
      ) : (
        <>
          {sessions.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-slate-200 rounded-lg">
              <Terminal className="w-10 h-10 mx-auto mb-3 text-slate-300" />
              <p className="font-medium text-slate-500">No sessions yet.</p>
              <p className="text-sm text-slate-400 mt-1">
                {statusFilter
                  ? 'Try a different filter or wait for new activity.'
                  : 'Start a Claude Code session to see data here.'}
              </p>
            </div>
          ) : (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold text-slate-700">Session ID</th>
                    <th className="px-6 py-3 text-left font-semibold text-slate-700">Status</th>
                    <th className="px-6 py-3 text-left font-semibold text-slate-700">Started</th>
                    <th className="px-6 py-3 text-left font-semibold text-slate-700">Duration</th>
                    <th className="px-6 py-3 text-right font-semibold text-slate-700"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sessions.map((session) => (
                    <tr
                      key={session.id}
                      className="hover:bg-slate-50 transition-colors group cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <Link
                          href={`/dashboard/sessions/${session.id}`}
                          className="font-mono text-blue-600 hover:text-blue-700 text-xs font-medium group-hover:underline"
                        >
                          {session.id}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(
                            session.status
                          )}`}
                        >
                          {session.status === 'active' && (
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                          )}
                          {session.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-xs tabular-nums">
                        {formatDate(session.startTime)}
                      </td>
                      <td className="px-6 py-4 text-slate-600 text-xs tabular-nums">
                        {session.duration ? formatDuration(session.duration) : (
                          <span className="text-blue-500 font-medium">Ongoing</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          href={`/dashboard/sessions/${session.id}`}
                          className="inline-flex items-center gap-1 text-xs text-slate-400 group-hover:text-blue-500 transition-colors"
                        >
                          View
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Page {page} of {totalPages || 1}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="flex items-center gap-1.5 px-3 py-2 text-sm bg-slate-100 text-slate-700 rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-200 transition"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages || 1, page + 1))}
                disabled={!totalPages || page >= totalPages}
                className="flex items-center gap-1.5 px-3 py-2 text-sm bg-slate-100 text-slate-700 rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-200 transition"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
