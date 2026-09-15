import { useState, useEffect } from 'react'
import { api, UserData } from '../../lib/api'
import './SettingsModal.css'

interface SettingsModalProps {
  user: UserData
  onClose: () => void
  onUpdate: (user: UserData) => void
}

export function SettingsModal({ user, onClose, onUpdate }: SettingsModalProps) {
  const [claudeKey, setClaudeKey] = useState(user.claude_api_key || '')
  const [openaiKey, setOpenaiKey] = useState(user.openai_api_key || '')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      const updatedUser = await api.updateSettings({
        claude_api_key: claudeKey,
        openai_api_key: openaiKey
      })
      onUpdate(updatedUser)
      setMessage('Settings saved successfully!')
      setTimeout(() => onClose(), 1500)
    } catch (err: any) {
      setMessage(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="settings-backdrop" onClick={onClose}>
      <div className="settings-modal" onClick={e => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Account Settings</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSave} className="settings-form">
          <div className="settings-section">
            <h3>API Keys</h3>
            <p className="settings-desc">Configure your LLM providers. These keys are securely encrypted in the database.</p>
            
            <div className="settings-group">
              <label>Anthropic (Claude) API Key</label>
              <input 
                type="password" 
                value={claudeKey} 
                onChange={e => setClaudeKey(e.target.value)} 
                placeholder="sk-ant-..."
              />
              <span className="help-text">Primary model (Claude 3.5 Sonnet).</span>
            </div>

            <div className="settings-group">
              <label>Local Ollama Fallback</label>
              <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.9rem', color: '#8b8b9c' }}>
                If Claude is unavailable or no key is provided, the system will automatically fall back to your local Ollama instance (`llama3.2:3b`). No API key required.
              </div>
            </div>

            <div className="settings-group">
              <label>OpenAI API Key</label>
              <input 
                type="password" 
                value={openaiKey} 
                onChange={e => setOpenaiKey(e.target.value)} 
                placeholder="sk-..."
              />
              <span className="help-text">Used for GPT-4o (Coming soon)</span>
            </div>
          </div>

          {message && (
            <div className={`settings-message ${message.includes('Error') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}

          <div className="settings-footer">
            <button type="button" className="btn-cancel" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-save" disabled={loading}>
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
