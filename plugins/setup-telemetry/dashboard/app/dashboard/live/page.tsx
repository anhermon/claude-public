'use client'

import { LiveFeed } from '@/components/LiveFeed'

export default function LivePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Live Monitoring</h1>
        <p className="text-slate-600 mt-2">Real-time session and tool activity feed</p>
      </div>

      <LiveFeed />
    </div>
  )
}
