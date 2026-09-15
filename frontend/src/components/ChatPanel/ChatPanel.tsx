import { useEffect, useRef } from 'react'
import { ChatMessage } from '../../hooks/useChat'
import { MessageBubble } from '../MessageBubble/MessageBubble'
import { ArtifactData } from '../../lib/api'
import './ChatPanel.css'

interface Props {
  messages: ChatMessage[]
  isLoadingHistory?: boolean
  onArtifactOpen: (artifact: ArtifactData) => void
  onSendMessage: (text: string, skill: string | null) => void
}

const SUGGESTED_QUESTIONS = [
  "What does Brian Chesky say about founder-led sales?",
  "How did Duolingo achieve viral growth?",
  "What is product-market fit and how do you know you have it?",
  "What growth loops work for B2B SaaS?",
]

export function ChatPanel({ messages, isLoadingHistory, onArtifactOpen, onSendMessage }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (isLoadingHistory) {
    return (
      <div className="chat-panel" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div className="chat-loading-spinner" style={{
          width: '32px', height: '32px', border: '3px solid var(--surface-glass-hover)', 
          borderTopColor: 'var(--accent-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite'
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  const isEmpty = messages.length === 0

  return (
    <div className="chat-panel">
      {isEmpty ? (
        <div className="chat-empty fade-in">
          <div className="empty-hero">
            <div className="empty-logo">
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="20" fill="url(#grad)" />
                <path d="M12 20c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="20" cy="20" r="3" fill="white" />
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="40" y2="40">
                    <stop offset="0%" stopColor="#7c6df0" />
                    <stop offset="100%" stopColor="#4f46e5" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1 className="empty-title">Lenny Growth Assistant</h1>
            <p className="empty-subtitle">
              Grounded in 269 episodes of Lenny's Podcast — ask anything about product, growth, and strategy.
            </p>
          </div>
          <div className="suggestion-grid">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                className="suggestion-card"
                onClick={() => onSendMessage(q, null)}
              >
                <span className="suggestion-icon">💡</span>
                <span>{q}</span>
              </button>
            ))}
          </div>
          <div className="skill-hints">
            <span className="skill-hint">
              <span className="skill-badge">✍️ Ship 30</span>
              Say "write a Ship 30 essay about..."
            </span>
            <span className="skill-hint">
              <span className="skill-badge">🎨 Artifact</span>
              Say "generate an HTML report on..."
            </span>
          </div>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onArtifactOpen={onArtifactOpen}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}
