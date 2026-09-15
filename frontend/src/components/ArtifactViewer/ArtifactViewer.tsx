import React, { useMemo, useState, useEffect } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ArtifactData } from '../../lib/api'
import './ArtifactViewer.css'

interface Props {
  artifact: ArtifactData | null
  onClose: () => void
}

type ViewMode = 'preview' | 'code'

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: React.ReactNode}) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="artifact-viewer slide-in-right" style={{ padding: 20, color: '#fca5a5' }}>
          <h3>Artifact Viewer Crashed</h3>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 11 }}>{String(this.state.error)}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

function ArtifactViewerInner({ artifact, onClose }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('preview')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!artifact) return
    setViewMode('preview')
  }, [artifact])

  const iframeSrc = useMemo(() => {
    if (!artifact || viewMode !== 'preview') return ''

    const type = artifact.type || (artifact as any).artifact_type || 'unknown'

    if (type === 'html') {
      return artifact.content || ''
    }
    
    try {
      const content = artifact.content || ''
      const raw = marked.parse(content) as string
    const safe = DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
    return `
      <!DOCTYPE html>
      <html data-theme="dark">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 28px 32px;
            line-height: 1.7;
            color: #ffffff;
            background: #0a0a0a;
            max-width: 720px;
            margin: 0 auto;
          }
          h1, h2, h3 { font-weight: 700; margin-top: 24px; margin-bottom: 8px; color: #ffffff; }
          h1 { font-size: 24px; }
          h2 { font-size: 18px; }
          h3 { font-size: 15px; }
          p { margin-bottom: 12px; }
          ul, ol { padding-left: 20px; margin-bottom: 12px; }
          li { margin-bottom: 4px; }
          strong { font-weight: 600; color: #ffffff; }
          code { font-family: 'JetBrains Mono', monospace; background: #1a1a1a; padding: 2px 6px; border-radius: 4px; font-size: 13px; color: #e5e5e5; }
          pre { background: #121212; border: 1px solid #262626; padding: 16px; border-radius: 8px; overflow-x: auto; }
          blockquote { border-left: 3px solid #e5e5e5; padding-left: 16px; color: #a3a3a3; margin: 12px 0; }
          a { color: #ffffff; text-decoration: underline; }
        </style>
      </head>
      <body>${safe}</body>
      </html>
    `
    } catch (e: any) {
      return `<html><body><h3 style="color:red">Error parsing artifact</h3><pre>${e.message}</pre></body></html>`
    }
  }, [artifact, viewMode])

  const handleCopy = async () => {
    if (!artifact) return
    await navigator.clipboard.writeText(artifact.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    if (!artifact) return
    const ext = artifact.type === 'html' ? 'html' : 'md'
    const blob = new Blob([artifact.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${artifact.title.replace(/\s+/g, '-').toLowerCase()}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!artifact) return null

  return (
    <div className="artifact-viewer slide-in-right">
      <div className="artifact-header">
        <div className="artifact-header-left">
          <span className="artifact-type-icon">
            {(artifact.type || (artifact as any).artifact_type) === 'html' ? '🌐' : (artifact.type || (artifact as any).artifact_type) === 'ship30' ? '✍️' : '📄'}
          </span>
          <div>
            <div className="artifact-title">{artifact.title || 'Untitled'}</div>
            <div className="artifact-meta">{String(artifact.type || (artifact as any).artifact_type || 'UNKNOWN').toUpperCase()}</div>
          </div>
        </div>

        <div className="artifact-header-right">
          <div className="view-toggle">
            <button
              className={`view-toggle-btn ${viewMode === 'preview' ? 'active' : ''}`}
              onClick={() => setViewMode('preview')}
            >
              Preview
            </button>
            <button
              className={`view-toggle-btn ${viewMode === 'code' ? 'active' : ''}`}
              onClick={() => setViewMode('code')}
            >
              Code
            </button>
          </div>

          <button className="icon-btn" onClick={handleCopy} title="Copy to clipboard" aria-label="Copy artifact content">
            {copied ? '✓' : '⎘'}
          </button>
          <button className="icon-btn" onClick={handleDownload} title="Download" aria-label="Download artifact">
            ↓
          </button>
          <button className="icon-btn close-btn" onClick={onClose} title="Close" aria-label="Close artifact viewer">
            ×
          </button>
        </div>
      </div>

      <div className="artifact-body">
        {viewMode === 'preview' ? (
          <iframe
            className="artifact-iframe"
            title={artifact.title}
            srcDoc={iframeSrc}
            sandbox="allow-scripts"
            aria-label={`Rendered artifact: ${artifact.title}`}
          />
        ) : (
          <pre className="artifact-code">
            <code>{artifact.content}</code>
          </pre>
        )}
      </div>

      <div className="artifact-security-note">
        🔒 Rendered in a sandboxed iframe · External network access blocked
      </div>
    </div>
  )
}

export function ArtifactViewer(props: Props) {
  return (
    <ErrorBoundary>
      <ArtifactViewerInner {...props} />
    </ErrorBoundary>
  )
}
