'use client'

import { SessionList } from '@/components/SessionList'

export default function SessionsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Sessions Management</h1>
        <p className="text-slate-600 mt-2">Browse and filter session records</p>
      </div>

      <SessionList />
    </div>
  )
}
