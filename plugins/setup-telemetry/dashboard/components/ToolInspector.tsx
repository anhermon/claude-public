'use client'

import React from 'react'
import { Tool } from '@/lib/types/telemetry'
import { ChevronDown } from 'lucide-react'

interface ToolInspectorProps {
  tools: Tool[]
}

export function ToolInspector({ tools }: ToolInspectorProps) {
  const [expandedId, setExpandedId] = React.useState<string | null>(null)

  const sortedTools = [...tools].sort((a, b) => a.startTime - b.startTime)

  const getStatusColor = (status: Tool['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-50'
      case 'running':
        return 'text-blue-700 bg-blue-50'
      case 'pending':
        return 'text-slate-700 bg-slate-50'
      case 'failed':
        return 'text-red-700 bg-red-50'
    }
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-slate-900">Tool Inspector</h3>

      {sortedTools.length === 0 ? (
        <div className="text-center py-8 text-slate-500">No tools executed</div>
      ) : (
        <div className="space-y-2">
          {sortedTools.map((tool) => (
            <div
              key={tool.id}
              className={`border rounded-lg transition ${
                expandedId === tool.id
                  ? `border-slate-300 ${getStatusColor(tool.status)}`
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <button
                onClick={() => setExpandedId(expandedId === tool.id ? null : tool.id)}
                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-slate-50 transition"
              >
                <ChevronDown
                  className={`w-5 h-5 flex-shrink-0 transition-transform ${
                    expandedId === tool.id ? 'rotate-180' : ''
                  }`}
                />
                <div className="flex-1 text-left">
                  <p className="font-medium text-slate-900">{tool.name}</p>
                </div>
                <span
                  className={`inline-block px-3 py-1 rounded text-xs font-medium ${
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
                <span className="text-sm text-slate-600 ml-2">{formatDuration(tool.duration)}</span>
              </button>

              {expandedId === tool.id && (
                <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">Start Time</p>
                      <p className="text-sm text-slate-900 mt-1">{formatDate(tool.startTime)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">End Time</p>
                      <p className="text-sm text-slate-900 mt-1">{formatDate(tool.endTime)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">Duration</p>
                      <p className="text-sm text-slate-900 mt-1">{formatDuration(tool.duration)}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">Status</p>
                      <p className="text-sm text-slate-900 mt-1 capitalize">{tool.status}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">Input Tokens</p>
                      <p className="text-sm text-slate-900 mt-1">{tool.inputTokens || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-600 uppercase">Output Tokens</p>
                      <p className="text-sm text-slate-900 mt-1">{tool.outputTokens || 0}</p>
                    </div>
                  </div>

                  {tool.error && (
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      <p className="text-xs font-semibold text-red-800 uppercase">Error</p>
                      <p className="text-sm text-red-700 mt-1 font-mono">{tool.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
