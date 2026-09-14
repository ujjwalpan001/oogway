import { useState, useEffect, useCallback } from 'react'
import { SessionSidebar } from './components/SessionSidebar/SessionSidebar'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { ChatInput } from './components/ChatPanel/ChatInput'
import { ArtifactViewer } from './components/ArtifactViewer/ArtifactViewer'
import { ModelBadge } from './components/ModelBadge/ModelBadge'
import { useChat } from './hooks/useChat'
import { api, ArtifactData } from './lib/api'
import './App.css'

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [modelProvider, setModelProvider] = useState('groq')
  const [modelName, setModelName] = useState('llama3-70b-8192')
  const [openArtifact, setOpenArtifact] = useState<ArtifactData | null>(null)
  const [sessionKey, setSessionKey] = useState(0)

  const { messages, isLoading, sendMessage, loadHistory, cancelStream, clearMessages } = useChat(sessionId)

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
    await loadHistory(id)
    setSessionKey((k) => k + 1)
  }, [loadHistory])

  const handleSend = useCallback(async (text: string, skill: string | null) => {
    if (!sessionId) {
      const session = await api.createSession(text.slice(0, 40))
      setSessionId(session.id)
      setModelProvider(session.model_provider)
      setModelName(session.model_name)
      setSessionKey((k) => k + 1)
      await new Promise((r) => setTimeout(r, 50))
      sendMessage(text, skill)
    } else {
      sendMessage(text, skill)
    }
  }, [sessionId, sendMessage])

  useEffect(() => {
    api.health().then((h) => {
      setModelProvider(h.provider)
      setModelName(h.model)
    }).catch(() => null)
  }, [])

  const handleArtifactOpen = useCallback((artifact: ArtifactData) => {
    setOpenArtifact(artifact)
  }, [])

  return (
    <div className="app-layout">
      <SessionSidebar
        key={sessionKey}
        activeSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewSession={createNewSession}
      />

      <div className="main-area">
        <header className="app-header">
          <div className="header-left">
            {sessionId && (
              <span className="header-session-label">
                {messages.length > 0
                  ? messages[0]?.content.slice(0, 48) + (messages[0]?.content.length > 48 ? '…' : '')
                  : 'New conversation'}
              </span>
            )}
          </div>
          <div className="header-right">
            <ModelBadge modelProvider={modelProvider} modelName={modelName} />
          </div>
        </header>

        <div className="chat-area">
          <div className="chat-column">
            <ChatPanel
              messages={messages}
              onArtifactOpen={handleArtifactOpen}
              onSendMessage={handleSend}
            />
            <ChatInput
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
        </div>
      </div>
    </div>
  )
}
