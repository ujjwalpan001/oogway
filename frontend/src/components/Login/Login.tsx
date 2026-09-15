import { useState, useEffect } from 'react'
import { api, setSessionToken, UserData } from '../../lib/api'
import './Login.css'

interface LoginProps {
  onLogin: (user: UserData) => void
}

const BACKGROUNDS = ['/bg-1.jpg', '/bg-2.jpg', '/bg-3.jpg']

export function Login({ onLogin }: LoginProps) {
  const [bgIndex, setBgIndex] = useState(0)
  const [isRegistering, setIsRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setBgIndex((prev) => (prev + 1) % BACKGROUNDS.length)
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const data = isRegistering 
        ? await api.register({ email, password })
        : await api.login({ email, password })
        
      setSessionToken(data.session_token || null)
      onLogin(data)
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-left">
        <div className="login-hero-content">
          <div className="login-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#paint0_linear)"/>
              <path d="M2 17L12 22L22 17" stroke="url(#paint1_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="url(#paint2_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <defs>
                <linearGradient id="paint0_linear" x1="12" y1="2" x2="12" y2="12" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#8B5CF6" />
                  <stop offset="1" stopColor="#6D28D9" />
                </linearGradient>
                <linearGradient id="paint1_linear" x1="12" y1="17" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#8B5CF6" />
                  <stop offset="1" stopColor="#6D28D9" />
                </linearGradient>
                <linearGradient id="paint2_linear" x1="12" y1="12" x2="12" y2="17" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#8B5CF6" />
                  <stop offset="1" stopColor="#6D28D9" />
                </linearGradient>
              </defs>
            </svg>
            Lenny Growth Assistant
          </div>
          
          <div className="login-badge">
            <span className="badge-dot"></span>
            Lenny's Podcast Knowledge Base
          </div>

          <h1 className="login-heading">
            Master growth.<br/>
            <span className="text-gradient">Ace your interviews.</span>
          </h1>
          
          <p className="login-description">
            Chat with 269 episodes of Lenny's Podcast. Instantly search frameworks, 
            learn from top PMs, and generate Ship 30 for 30 essays in seconds.
          </p>

          <div className="login-features">
            <div className="feature-item">
              <span className="feature-icon">🎙️</span>
              <div>
                <strong>269+ Episodes</strong>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">⚡</span>
              <div>
                <strong>Instant RAG Search</strong>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🧠</span>
              <div>
                <strong>Claude 3.5 Sonnet</strong>
              </div>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🛡️</span>
              <div>
                <strong>Local Fallback Mode</strong>
              </div>
            </div>
          </div>
        </div>
        
        {BACKGROUNDS.map((bg, idx) => (
          <div 
            key={bg}
            className={`login-background ${idx === bgIndex ? 'active' : ''}`}
            style={{ backgroundImage: `url(${bg})` }}
          />
        ))}

        <div className="carousel-indicators">
          {BACKGROUNDS.map((_, idx) => (
            <button
              key={idx}
              className={`carousel-dot ${idx === bgIndex ? 'active' : ''}`}
              onClick={() => setBgIndex(idx)}
              aria-label={`Go to slide ${idx + 1}`}
            />
          ))}
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-wrapper">
          <h2 className="form-title">{isRegistering ? 'Create an account' : 'Welcome back'}</h2>
          <p className="form-subtitle">
            {isRegistering ? 'Sign up for your enterprise dashboard' : 'Sign in to your enterprise dashboard'}
          </p>

          <div className="fresh-db-alert">
            <div className="alert-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </div>
            <div className="alert-text">
              <strong>Fresh Database</strong>
              <p>The database has been securely wiped. Please create a new account to get started.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="input-group">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            <div className="input-group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Processing...' : (isRegistering ? 'Create Account' : 'Sign in to Dashboard')}
            </button>
          </form>

          <div className="toggle-auth">
            {isRegistering ? 'Already have an account?' : "Don't have an account?"}
            <button 
              type="button" 
              className="toggle-btn"
              onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
            >
              {isRegistering ? 'Sign in' : 'Create one'}
            </button>
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
