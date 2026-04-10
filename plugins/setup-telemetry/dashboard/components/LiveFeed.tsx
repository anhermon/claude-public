'use client'

import React from 'react'
import Link from 'next/link'
import { useLiveFeed } from '@/lib/hooks/useLiveFeed'
import { Loader2, Terminal, Clock } from 'lucide-react'

export function LiveFeed() {
  const { activeSessions, activeSessionCount, isLoading, isError } = useLiveFeed()

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const formatAge = (timestamp: number) => {
    const diff = Date.now() - timestamp
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    if (seconds < 60) return `${seconds}s ago`
    if (minutes < 60) return `${minutes}m ago`
    return `${Math.floor(minutes / 60)}h ago`
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Live Session Feed</h2>
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-sm font-medium text-blue-900">
            {activeSessionCount} Active
          </span>
        </div>
      </div>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          Failed to connect to backend. Retrying every 3 seconds.
        </div>
      )}

      {isLoading && activeSessions.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400 mr-2" />
          <span className="text-slate-500">Connecting to live feed...</span>
        </div>
      ) : activeSessions.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <Terminal className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="font-medium text-slate-500">No active sessions</p>
          <p className="text-sm mt-1">Start a Claude Code session to see data here.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {activeSessions.map((session) => (
            <Link
              key={session.id}
              href={`/dashboard/sessions/${session.id}`}
              className="block border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50/30 transition-all"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0 animate-pulse" />
                  <div className="min-w-0">
                    <p className="font-mono text-sm font-medium text-slate-900 truncate">
                      {session.id}
                    </p>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        started {formatAge(session.startTime)}
                      </span>
                      <span className="text-xs text-slate-400">
                        {formatDate(session.startTime)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex-shrink-0 flex items-center gap-2">
                  <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    active
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {activeSessions.length > 0 && (
        <p className="text-xs text-slate-400 text-center">
          Showing up to 5 active sessions — polling every 3s
        </p>
      )}
    </div>
  )
}
