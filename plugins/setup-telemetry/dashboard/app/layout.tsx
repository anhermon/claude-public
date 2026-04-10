import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Telemetry Dashboard',
  description: 'Real-time session monitoring and analytics',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50">
        <div className="flex h-screen bg-slate-50">
          {/* Sidebar */}
          <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
            <div className="p-6 border-b border-slate-200">
              <h1 className="text-2xl font-bold text-slate-900">TelemetryOS</h1>
              <p className="text-sm text-slate-600 mt-1">Session Dashboard</p>
            </div>

            <nav className="flex-1 p-4 space-y-2">
              <a
                href="/dashboard"
                className="block px-4 py-3 rounded-lg text-slate-700 hover:bg-slate-100 transition font-medium"
              >
                Dashboard
              </a>
              <a
                href="/dashboard/sessions"
                className="block px-4 py-3 rounded-lg text-slate-700 hover:bg-slate-100 transition font-medium"
              >
                Sessions
              </a>
              <a
                href="/dashboard/metrics"
                className="block px-4 py-3 rounded-lg text-slate-700 hover:bg-slate-100 transition font-medium"
              >
                Metrics
              </a>
              <a
                href="/dashboard/live"
                className="block px-4 py-3 rounded-lg text-slate-700 hover:bg-slate-100 transition font-medium"
              >
                Live Feed
              </a>
            </nav>

            <div className="p-4 border-t border-slate-200">
              <div className="text-xs text-slate-600">
                <p>Polling: 5s (sessions)</p>
                <p>Polling: 2s (detail, live)</p>
              </div>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-auto">
            <div className="p-8">{children}</div>
          </main>
        </div>
      </body>
    </html>
  )
}
