import { useState, useCallback } from 'react'
import { api, Session, Message } from '../api/client'

export function useChat() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSession, setActiveSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadSessions = useCallback(async () => {
    try {
      const data = await api.listSessions()
      setSessions(data)
    } catch (e: any) {
      setError(e.message)
    }
  }, [])

  const newSession = useCallback(async () => {
    try {
      const session = await api.createSession()
      setSessions(prev => [session, ...prev])
      setActiveSession(session)
      setMessages([])
      return session
    } catch (e: any) {
      setError(e.message)
      return null
    }
  }, [])

  const selectSession = useCallback(async (session: Session) => {
    setActiveSession(session)
    setError(null)
    try {
      const msgs = await api.getMessages(session.id)
      setMessages(msgs)
    } catch (e: any) {
      setError(e.message)
    }
  }, [])

  const deleteSession = useCallback(async (sessionId: string) => {
    await api.deleteSession(sessionId)
    setSessions(prev => prev.filter(s => s.id !== sessionId))
    if (activeSession?.id === sessionId) {
      setActiveSession(null)
      setMessages([])
    }
  }, [activeSession])

  const sendMessage = useCallback(async (content: string) => {
    if (!activeSession) return
    setError(null)

    const optimisticUser: Message = {
      id: `temp-${Date.now()}`,
      session_id: activeSession.id,
      role: 'user',
      content,
      sources: [],
      artifact: null,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimisticUser])
    setLoading(true)

    try {
      const resp = await api.sendMessage(activeSession.id, content)
      setMessages(prev => [...prev.filter(m => m.id !== optimisticUser.id), { ...optimisticUser, id: `user-${Date.now()}` }, resp.message])
      // Update session title in sidebar
      setSessions(prev => prev.map(s => s.id === activeSession.id ? { ...s, title: resp.message.content.slice(0, 50) || s.title } : s))
    } catch (e: any) {
      setMessages(prev => prev.filter(m => m.id !== optimisticUser.id))
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [activeSession])

  return { sessions, activeSession, messages, loading, error, loadSessions, newSession, selectSession, deleteSession, sendMessage }
}
