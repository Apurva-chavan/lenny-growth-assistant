const BASE_URL = import.meta.env.VITE_API_URL ?? ''
const BASE = `${BASE_URL}/api/v1`

export interface Session {
  id: string
  title: string
  llm_provider: string
  created_at: string
  updated_at: string
}

export interface SourceRef {
  source: string
  url: string
  excerpt: string
}

export interface Artifact {
  type: 'html' | 'markdown'
  content: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sources: SourceRef[]
  artifact: Artifact | null
  created_at: string
}

export interface ChatResponse {
  message: Message
  intent: string
}

export interface HealthStatus {
  status: string
  llm_provider: string
  ollama_available: boolean | null
  index_chunks: number
  index_ready: boolean
  db_connected: boolean
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  health: () => request<HealthStatus>(`${BASE_URL}/health`),
  createSession: (title = 'New Chat') =>
    request<Session>(`${BASE}/sessions`, { method: 'POST', body: JSON.stringify({ title }) }),
  listSessions: () => request<Session[]>(`${BASE}/sessions`),
  deleteSession: (id: string) =>
    fetch(`${BASE}/sessions/${id}`, { method: 'DELETE' }),
  getMessages: (sessionId: string) =>
    request<Message[]>(`${BASE}/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: string, content: string) =>
    request<ChatResponse>(`${BASE}/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
}
