import { useState, useRef, useCallback } from 'react'
import './ChatInput.css'

interface Props {
  selectedSkill: string | null
  onSkillChange: (skill: string | null) => void
  onSend: (text: string, skill: string | null) => void
  onCancel: () => void
  isLoading: boolean
  disabled: boolean
}

const SKILL_OPTIONS = [
  { id: null, label: 'Chat', icon: '💬' },
  { id: 'ship30', label: 'Ship 30 Essay', icon: '✍️' },
  { id: 'artifact:markdown', label: 'Markdown Doc', icon: '📄' },
  { id: 'artifact:html', label: 'HTML Report', icon: '🌐' },
]

export function ChatInput({ selectedSkill, onSkillChange, onSend, onCancel, isLoading, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isSubmittingRef = useRef(false)

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [])

  const handleSubmit = () => {
    const text = value.trim()
    if (!text || isLoading || disabled || isSubmittingRef.current) return
    isSubmittingRef.current = true
    onSend(text, selectedSkill)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    setTimeout(() => {
      isSubmittingRef.current = false
    }, 500)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="chat-input-container">
      <div className="skill-selector">
        {SKILL_OPTIONS.map((opt) => (
          <button
            key={String(opt.id)}
            className={`skill-option ${selectedSkill === opt.id ? 'skill-option-active' : ''}`}
            onClick={() => onSkillChange(opt.id)}
          >
            <span>{opt.icon}</span>
            <span>{opt.label}</span>
          </button>
        ))}
      </div>

      <div className={`input-box ${isLoading ? 'input-box-loading' : ''}`}>
        <textarea
          ref={textareaRef}
          id="chat-input"
          className="chat-textarea"
          placeholder={isLoading ? 'Generating...' : 'Ask anything about product, growth, or strategy...'}
          value={value}
          onChange={(e) => {
            setValue(e.target.value)
            adjustHeight()
          }}
          onKeyDown={handleKeyDown}
          disabled={isLoading || disabled}
          rows={1}
          aria-label="Chat message input"
        />

        <div className="input-actions">
          {isLoading ? (
            <button
              className="stop-btn"
              onClick={onCancel}
              aria-label="Stop generating"
              title="Stop generating"
            >
              <span className="stop-icon" />
            </button>
          ) : (
            <button
              className="send-btn"
              onClick={handleSubmit}
              disabled={!value.trim() || disabled}
              aria-label="Send message"
              title="Send (Enter)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <p className="input-hint">
        Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line · Answers are grounded in Lenny's transcripts
      </p>
    </div>
  )
}
