'use client'

import React, { useMemo } from 'react'
import { Tool } from '@/lib/types/telemetry'

interface TimelineProps {
  tools: Tool[]
  startTime: number
}

export function Timeline({ tools, startTime }: TimelineProps) {
  const stats = useMemo(() => {
    if (tools.length === 0) {
      return { minTime: 0, maxTime: 0, totalDuration: 0, range: 0 }
    }

    const minTime = startTime
    const maxTime = Math.max(...tools.map((t) => t.endTime || t.startTime + t.duration))
    const totalDuration = maxTime - minTime
    const range = Math.max(totalDuration, 1000)

    return { minTime, maxTime, totalDuration, range }
  }, [tools, startTime])

  const getToolColor = (status: Tool['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'running':
        return 'bg-blue-500'
      case 'pending':
        return 'bg-slate-400'
      case 'failed':
        return 'bg-red-500'
    }
  }

  const getPositionPercent = (timestamp: number) => {
    if (stats.range === 0) return 0
    return ((timestamp - stats.minTime) / stats.range) * 100
  }

  const getWidthPercent = (duration: number) => {
    if (stats.range === 0) return 0
    const width = (duration / stats.range) * 100
    return Math.max(width, 1)
  }

  const sortedTools = [...tools].sort((a, b) => a.startTime - b.startTime)

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Execution Timeline</h3>
          <p className="text-sm text-slate-600">
            Total Duration: {formatTime(stats.totalDuration)}
          </p>
        </div>

        {sortedTools.length === 0 ? (
          <div className="text-center py-8 text-slate-500">No tools executed yet</div>
        ) : (
          <div className="space-y-2">
            {/* Time axis */}
            <div className="flex items-end h-8">
              <div className="flex-1 relative h-full">
                <div className="absolute inset-0 flex justify-between text-xs text-slate-500 px-1">
                  <span>0ms</span>
                  <span>{formatTime(stats.range / 4)}</span>
                  <span>{formatTime(stats.range / 2)}</span>
                  <span>{formatTime((stats.range * 3) / 4)}</span>
                  <span>{formatTime(stats.range)}</span>
                </div>
              </div>
            </div>

            {/* Grid lines */}
            <div className="relative h-px bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200" />

            {/* Tool bars */}
            <div className="space-y-3">
              {sortedTools.map((tool, index) => {
                const startPercent = getPositionPercent(tool.startTime)
                const widthPercent = getWidthPercent(tool.duration)

                return (
                  <div key={tool.id} className="relative">
                    <div className="flex items-center h-10">
                      {/* Tool name */}
                      <div className="w-32 flex-shrink-0 pr-4">
                        <p className="text-sm font-medium text-slate-900 truncate">{tool.name}</p>
                        <p className="text-xs text-slate-500">{formatTime(tool.duration)}</p>
                      </div>

                      {/* Timeline container */}
                      <div className="flex-1 relative h-full bg-slate-50 rounded border border-slate-200">
                        {/* Bar */}
                        <div
                          className={`absolute top-1 bottom-1 rounded transition-all ${getToolColor(
                            tool.status
                          )} cursor-pointer hover:shadow-md`}
                          style={{
                            left: `${startPercent}%`,
                            width: `${widthPercent}%`,
                            minWidth: '8px',
                          }}
                          title={`${tool.name}: ${tool.status} (${formatTime(tool.duration)})`}
                        >
                          <div className="absolute inset-0 flex items-center justify-center">
                            {widthPercent > 8 && (
                              <span className="text-xs font-bold text-white truncate px-1">
                                {tool.name.slice(0, 3).toUpperCase()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Status indicator */}
                      <div className="w-20 flex-shrink-0 pl-4">
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                            tool.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : tool.status === 'running'
                                ? 'bg-blue-100 text-blue-800'
                                : tool.status === 'failed'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-slate-100 text-slate-800'
                          }`}
                        >
                          {tool.status}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Tool details table */}
      {sortedTools.length > 0 && (
        <div className="mt-8">
          <h4 className="text-sm font-semibold text-slate-900 mb-4">Tool Details</h4>
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">Tool</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">Duration</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">Start</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">End</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-900">Tokens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {sortedTools.map((tool) => (
                  <tr key={tool.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-medium text-slate-900">{tool.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          tool.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : tool.status === 'running'
                              ? 'bg-blue-100 text-blue-800'
                              : tool.status === 'failed'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-slate-100 text-slate-800'
                        }`}
                      >
                        {tool.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatTime(tool.duration)}</td>
                    <td className="px-4 py-3 text-slate-600 text-xs">
                      {formatTime(tool.startTime - stats.minTime)}
                    </td>
                    <td className="px-4 py-3 text-slate-600 text-xs">
                      {formatTime((tool.endTime || tool.startTime + tool.duration) - stats.minTime)}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {(tool.inputTokens || 0) + (tool.outputTokens || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
