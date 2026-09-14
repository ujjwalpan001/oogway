import { useEffect, useState } from 'react'
import { api, HealthData } from '../../lib/api'
import './ModelBadge.css'

interface Props {
  modelProvider: string
  modelName: string
}

export function ModelBadge({ modelProvider, modelName }: Props) {
  const [health, setHealth] = useState<HealthData | null>(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => null)
    const interval = setInterval(() => {
      api.health().then(setHealth).catch(() => null)
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const isOnline = health?.status !== 'error'
  const displayModel = modelName.length > 22 ? modelName.slice(0, 22) + '…' : modelName

  return (
    <div className="model-badge-wrap">
      <span className={`badge ${modelProvider === 'groq' ? 'badge-groq' : 'badge-ollama'}`}>
        <span className={`status-dot ${isOnline ? 'dot-online' : 'dot-offline'}`} />
        {modelProvider === 'groq' ? '⚡' : '🦙'} {displayModel}
      </span>

      {health && (
        <div className="health-tooltip" role="tooltip">
          <div className="health-row">
            <span>Database</span>
            <span className={health.checks.database === 'ok' ? 'check-ok' : 'check-err'}>
              {health.checks.database === 'ok' ? '✓' : '✗'}
            </span>
          </div>
          <div className="health-row">
            <span>ChromaDB</span>
            <span className={health.checks.chromadb?.startsWith('ok') ? 'check-ok' : 'check-err'}>
              {health.checks.chromadb?.startsWith('ok') ? '✓' : '✗'}
            </span>
          </div>
          <div className="health-row">
            <span>LLM</span>
            <span className={health.checks.llm === 'ok' ? 'check-ok' : 'check-err'}>
              {health.checks.llm === 'ok' ? '✓' : '✗'}
            </span>
          </div>
          <div className="health-divider" />
          <div className="health-chromadb-detail">{health.checks.chromadb}</div>
        </div>
      )}
    </div>
  )
}
