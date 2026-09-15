import { useState, useRef, useCallback } from 'react'
import { api, Citation, ArtifactData } from '../lib/api'

export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  citations: Citation[]
  artifact: ArtifactData | null
  isStreaming?: boolean
  skillBanner?: string
  error?: string
}

export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isHistoryLoading, setIsHistoryLoading] = useState(false)
  const abortRef = useRef<(() => void) | null>(null)

  const loadHistory = useCallback(async (sid: string) => {
    setIsHistoryLoading(true)
    try {
      const session = await api.getSession(sid)
      const msgs: ChatMessage[] = session.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations,
        artifact: m.artifact ? {
          type: (m.artifact as any).artifact_type || m.artifact.type,
          title: m.artifact.title,
          content: m.artifact.content,
        } : null,
      }))
      setMessages(msgs)
    } catch {
      setMessages([])
    } finally {
      setIsHistoryLoading(false)
    }
  }, [])

  const sendMessage = useCallback(
    async (text: string, skill: string | null = null, explicitSessionId: string | null = null) => {
      const targetSessionId = explicitSessionId || sessionId
      if (!targetSessionId || isLoading) return null

      const userMsgId = `user-${Date.now()}`
      const asstMsgId = `asst-${Date.now()}`

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: 'user', content: text, citations: [], artifact: null },
        { id: asstMsgId, role: 'assistant', content: '', citations: [], artifact: null, isStreaming: true },
      ])
      setIsLoading(true)

      let artifactOut: ArtifactData | null = null

      const abort = api.streamChat(
        targetSessionId,
        text,
        skill,
        (token) => {
          setMessages((prev) =>
            prev.map((m) => (m.id === asstMsgId ? { ...m, content: m.content + token } : m))
          )
        },
        (citations, artifact) => {
          artifactOut = artifact
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, isStreaming: false, citations, artifact }
                : m
            )
          )
          setIsLoading(false)
        },
        (errMsg) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId
                ? { ...m, isStreaming: false, content: '', error: errMsg }
                : m
            )
          )
          setIsLoading(false)
        },
        (skillName) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstMsgId ? { ...m, skillBanner: skillName } : m
            )
          )
        },
      )

      abortRef.current = abort
      return () => artifactOut
    },
    [sessionId, isLoading]
  )

  const cancelStream = useCallback(() => {
    abortRef.current?.()
    setIsLoading(false)
    setMessages((prev) =>
      prev.map((m) => (m.isStreaming ? { ...m, isStreaming: false } : m))
    )
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, isLoading, isHistoryLoading, sendMessage, loadHistory, cancelStream, clearMessages }
}
