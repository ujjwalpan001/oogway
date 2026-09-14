const API_BASE = '/api'

export interface Citation {
  id: string
  episode_title: string
  guest: string
  chunk_text: string
  youtube_url: string
  relevance_score: number
}

export interface ArtifactData {
  type: string
  title: string
  content: string
}

export interface SessionOut {
  id: string
  title: string
  model_provider: string
  model_name: string
  created_at: string
  updated_at: string
}

export interface MessageOut {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  artifact: ArtifactData | null
  citations: Citation[]
}

export interface SessionWithMessages extends SessionOut {
  messages: MessageOut[]
}

export interface HealthData {
  status: string
  version: string
  provider: string
  model: string
  checks: Record<string, string>
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || body.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  createSession: (title = 'New conversation') =>
    request<SessionOut>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  listSessions: () => request<SessionOut[]>('/sessions'),

  getSession: (id: string) => request<SessionWithMessages>(`/sessions/${id}`),

  deleteSession: (id: string) =>
    fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' }),

  health: () => request<HealthData>('/health'),

  streamChat(
    sessionId: string,
    message: string,
    skill: string | null,
    onToken: (token: string) => void,
    onDone: (citations: Citation[], artifact: ArtifactData | null) => void,
    onError: (msg: string) => void,
    onSkillStart: (skill: string) => void,
  ): () => void {
    const controller = new AbortController()

    fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message, skill }),
      signal: controller.signal,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        onError(body.detail || body.error || `HTTP ${res.status}`)
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'token') onToken(event.content)
            else if (event.type === 'skill_start') onSkillStart(event.skill)
            else if (event.type === 'done') onDone(event.citations ?? [], event.artifact ?? null)
            else if (event.type === 'error') onError(event.message)
          } catch {
            // malformed line, skip
          }
        }
      }
    }).catch((err) => {
      if (err.name !== 'AbortError') onError(err.message)
    })

    return () => controller.abort()
  },
}
