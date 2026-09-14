import { useMemo } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ChatMessage } from '../../hooks/useChat'
import { ArtifactData, Citation } from '../../lib/api'
import './MessageBubble.css'

marked.setOptions({ breaks: true, gfm: true })

interface Props {
  message: ChatMessage
  onArtifactOpen: (artifact: ArtifactData) => void
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="citation-card">
      <div className="citation-header">
        <span className="citation-guest">{citation.guest}</span>
        <span className="citation-score">{citation.relevance_score}% match</span>
      </div>
      <div className="citation-title">{citation.episode_title}</div>
      <p className="citation-excerpt">{citation.chunk_text}</p>
      {citation.youtube_url && (
        <a
          className="citation-link"
          href={citation.youtube_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          ▶ Watch episode
        </a>
      )}
    </div>
  )
}

function SkillBanner({ skill }: { skill: string }) {
  const label = skill === 'ship30' ? '✍️ Generating Ship 30 essay...' : '🎨 Generating artifact...'
  return <div className="skill-banner">{label}</div>
}

export function MessageBubble({ message, onArtifactOpen }: Props) {
  const renderedContent = useMemo(() => {
    if (!message.content) return ''
    const raw = marked.parse(message.content) as string
    return DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
  }, [message.content])

  const isUser = message.role === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'message-user' : 'message-assistant'} fade-in`}>
      {!isUser && (
        <div className="message-avatar">
          <svg width="20" height="20" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="20" fill="url(#av-grad)" />
            <path d="M12 20c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="20" cy="20" r="3" fill="white" />
            <defs>
              <linearGradient id="av-grad" x1="0" y1="0" x2="40" y2="40">
                <stop offset="0%" stopColor="#7c6df0" />
                <stop offset="100%" stopColor="#4f46e5" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      )}

      <div className="message-content-wrap">
        {message.skillBanner && <SkillBanner skill={message.skillBanner} />}

        {message.error ? (
          <div className="message-error">
            <span>⚠️</span> {message.error}
          </div>
        ) : isUser ? (
          <div className="message-bubble user-bubble">{message.content}</div>
        ) : (
          <div className="message-bubble assistant-bubble">
            {message.isStreaming && !message.content ? (
              <div className="typing-indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            ) : (
              <div
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: renderedContent }}
              />
            )}
          </div>
        )}

        {message.artifact && (
          <button
            className="artifact-preview-btn"
            onClick={() => onArtifactOpen(message.artifact!)}
          >
            <span className="artifact-icon">{message.artifact.type === 'html' ? '🌐' : '📄'}</span>
            <div className="artifact-preview-text">
              <span className="artifact-preview-title">{message.artifact.title}</span>
              <span className="artifact-preview-type">{message.artifact.type.toUpperCase()} Artifact — click to open</span>
            </div>
            <span className="artifact-preview-arrow">→</span>
          </button>
        )}

        {message.citations.length > 0 && (
          <details className="citations-section">
            <summary className="citations-toggle">
              📚 {message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
            </summary>
            <div className="citations-list">
              {message.citations.map((c) => (
                <CitationCard key={c.id} citation={c} />
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}
