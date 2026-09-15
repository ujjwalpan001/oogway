import { useState, useEffect, useCallback } from 'react'
import { SessionSidebar } from './components/SessionSidebar/SessionSidebar'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { ChatInput } from './components/ChatPanel/ChatInput'
import { ArtifactViewer } from './components/ArtifactViewer/ArtifactViewer'
import { ModelBadge } from './components/ModelBadge/ModelBadge'
import { Login } from './components/Login/Login'
import { SettingsModal } from './components/SettingsModal/SettingsModal'
import { useChat } from './hooks/useChat'
import { api, ArtifactData, UserData } from './lib/api'
import './App.css'

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [modelProvider, setModelProvider] = useState('claude')
  const [modelName, setModelName] = useState('claude-3-5-sonnet-20240620')
  const [openArtifact, setOpenArtifact] = useState<ArtifactData | null>(null)
  const [sessionKey, setSessionKey] = useState(0)
  const [user, setUser] = useState<UserData | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [isAppLoading, setIsAppLoading] = useState(true)
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const { messages, isLoading, isHistoryLoading, sendMessage, loadHistory, cancelStream, clearMessages } = useChat(sessionId)

  const createNewSession = useCallback(async () => {
    try {
      const session = await api.createSession()
      setSessionId(session.id)
      setModelProvider(session.model_provider)
      setModelName(session.model_name)
      clearMessages()
      setOpenArtifact(null)
      setSessionKey((k) => k + 1)
    } catch (err) {
      console.error('Failed to create session:', err)
    }
  }, [clearMessages])

  const handleSelectSession = useCallback(async (id: string) => {
    setSessionId(id)
    setOpenArtifact(null)
    setSidebarOpen(false)
    await loadHistory(id)
  }, [loadHistory])

  const handleSend = useCallback(async (text: string, skill: string | null) => {
    if (!sessionId) {
      const session = await api.createSession(text.slice(0, 40))
      setSessionId(session.id)
      setModelProvider(session.model_provider)
      setModelName(session.model_name)
      await new Promise((r) => setTimeout(r, 50))
      sendMessage(text, skill, session.id)
    } else {
      sendMessage(text, skill)
    }
  }, [sessionId, sendMessage])

  useEffect(() => {
    api.getMe()
      .then((me) => {
        setUser(me)
      })
      .catch(() => {
        setUser(null)
      })
      .finally(() => {
        setIsAppLoading(false)
      })

    api.health().then((h) => {
      setModelProvider(h.provider)
      setModelName(h.model)
    }).catch(() => null)
  }, [])

  const handleLogout = async () => {
    await api.logout().catch(() => {})
    setUser(null)
    setSessionId(null)
  }

  const handleArtifactOpen = useCallback((artifact: ArtifactData) => {
    setOpenArtifact(artifact)
  }, [])

  if (isAppLoading) {
    return <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>Loading...</div>
  }

  if (!user) {
    return <Login onLogin={setUser} />
  }

  return (
    <div className={`app-layout ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <SessionSidebar
        activeSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewSession={createNewSession}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-area">
        <header className="app-header">
          <div className="header-left">
            <button 
              className="sidebar-toggle-btn" 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              title="Toggle History"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            </button>
            {sessionId && (
              <span className="header-session-label">
                {messages.length > 0
                  ? messages[0]?.content.slice(0, 48) + (messages[0]?.content.length > 48 ? '…' : '')
                  : 'New conversation'}
              </span>
            )}
          </div>
          <div className="header-right" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button 
              className="theme-toggle-btn"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              title="Toggle Theme"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <ModelBadge modelProvider={modelProvider} modelName={modelName} />
            <button 
              className="btn btn-surface" 
              onClick={() => setShowSettings(true)}
            >
              Settings
            </button>
            <button 
              className="btn btn-ghost" 
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </header>

        <div className="chat-area">
          <div className="chat-column">
            <ChatPanel
              messages={messages}
              isLoadingHistory={isHistoryLoading}
              onArtifactOpen={handleArtifactOpen}
              onSendMessage={(text) => handleSend(text, selectedSkill)}
            />
            <ChatInput
              selectedSkill={selectedSkill}
              onSkillChange={setSelectedSkill}
              onSend={handleSend}
              onCancel={cancelStream}
              isLoading={isLoading}
              disabled={false}
            />
          </div>

          {openArtifact && (
            <ArtifactViewer
              artifact={openArtifact}
              onClose={() => setOpenArtifact(null)}
            />
          )}

          {showSettings && (
            <SettingsModal 
              user={user} 
              onClose={() => setShowSettings(false)}
              onUpdate={setUser}
            />
          )}
        </div>
      </div>
    </div>
  )
}
