import { useEffect, useState } from 'react'
import { api, SessionOut } from '../../lib/api'
import './SessionSidebar.css'

interface Props {
  activeSessionId: string | null
  onSelectSession: (id: string) => void
  onNewSession: () => void
}

export function SessionSidebar({ activeSessionId, onSelectSession, onNewSession }: Props) {
  const [sessions, setSessions] = useState<SessionOut[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [activeSessionId])

  const loadSessions = async () => {
    try {
      const data = await api.listSessions()
      setSessions(data)
    } catch {
      // silently fail — sidebar is non-critical
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await api.deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (activeSessionId === id) {
      onNewSession()
    }
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    const now = new Date()
    const diffH = (now.getTime() - d.getTime()) / 3600000
    if (diffH < 1) return 'Just now'
    if (diffH < 24) return `${Math.floor(diffH)}h ago`
    if (diffH < 48) return 'Yesterday'
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }

  return (
    <aside className="session-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="20" fill="url(#sb-grad)" />
            <path d="M12 20c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="20" cy="20" r="3" fill="white" />
            <defs>
              <linearGradient id="sb-grad" x1="0" y1="0" x2="40" y2="40">
                <stop offset="0%" stopColor="#7c6df0" />
                <stop offset="100%" stopColor="#4f46e5" />
              </linearGradient>
            </defs>
          </svg>
          <span className="sidebar-brand-name">Lenny AI</span>
        </div>
        <button
          className="new-chat-btn"
          onClick={onNewSession}
          aria-label="New conversation"
          title="New conversation"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <div className="sidebar-content">
        {loading ? (
          <div className="sidebar-loading">
            {[1, 2, 3].map((i) => (
              <div key={i} className="session-skeleton" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="sidebar-empty">
            <p>No conversations yet</p>
            <button className="btn btn-primary" onClick={onNewSession}>
              Start chatting
            </button>
          </div>
        ) : (
          <ul className="session-list">
            {sessions.map((s) => (
              <li
                key={s.id}
                className={`session-item ${s.id === activeSessionId ? 'session-active' : ''}`}
                onClick={() => onSelectSession(s.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelectSession(s.id)}
                aria-label={`Open conversation: ${s.title}`}
                aria-current={s.id === activeSessionId ? 'true' : undefined}
              >
                <div className="session-icon">💬</div>
                <div className="session-info">
                  <div className="session-title">{s.title}</div>
                  <div className="session-meta">{formatDate(s.updated_at)}</div>
                </div>
                <button
                  className="session-delete"
                  onClick={(e) => handleDelete(e, s.id)}
                  aria-label={`Delete conversation: ${s.title}`}
                  title="Delete"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-footer-text">
          Grounded in 269 Lenny episodes
        </div>
      </div>
    </aside>
  )
}
