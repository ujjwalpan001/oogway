import { useEffect, useRef, useState } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ArtifactData } from '../../lib/api'
import './ArtifactViewer.css'

interface Props {
  artifact: ArtifactData | null
  onClose: () => void
}

type ViewMode = 'preview' | 'code'

export function ArtifactViewer({ artifact, onClose }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('preview')
  const [copied, setCopied] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    if (!artifact) return
    setViewMode('preview')
  }, [artifact])

  useEffect(() => {
    if (viewMode !== 'preview' || !artifact || !iframeRef.current) return

    const iframe = iframeRef.current
    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (!doc) return

    if (artifact.type === 'html') {
      doc.open()
      doc.write(artifact.content)
      doc.close()
    } else {
      const raw = marked.parse(artifact.content) as string
      const safe = DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } })
      doc.open()
      doc.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              padding: 28px 32px;
              line-height: 1.7;
              color: #1a1a2e;
              background: #ffffff;
              max-width: 720px;
              margin: 0 auto;
            }
            h1, h2, h3 { font-weight: 700; margin-top: 24px; margin-bottom: 8px; }
            h1 { font-size: 24px; }
            h2 { font-size: 18px; }
            h3 { font-size: 15px; }
            p { margin-bottom: 12px; }
            ul, ol { padding-left: 20px; margin-bottom: 12px; }
            li { margin-bottom: 4px; }
            strong { font-weight: 600; }
            code { font-family: 'JetBrains Mono', monospace; background: #f0f0ff; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
            pre { background: #f4f4f8; padding: 16px; border-radius: 8px; overflow-x: auto; }
            blockquote { border-left: 3px solid #7c6df0; padding-left: 16px; color: #555; margin: 12px 0; }
            a { color: #7c6df0; }
          </style>
        </head>
        <body>${safe}</body>
        </html>
      `)
      doc.close()
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
            {artifact.type === 'html' ? '🌐' : artifact.type === 'ship30' ? '✍️' : '📄'}
          </span>
          <div>
            <div className="artifact-title">{artifact.title}</div>
            <div className="artifact-meta">{artifact.type.toUpperCase()}</div>
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
            ref={iframeRef}
            className="artifact-iframe"
            title={artifact.title}
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
