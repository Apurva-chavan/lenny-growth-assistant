import { useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { api, HealthStatus, Message } from './api/client'
import Sidebar from './components/Sidebar'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import ArtifactViewer from './components/ArtifactViewer'
import EmptyState from './components/EmptyState'

export default function App() {
  const { sessions, activeSession, messages, loading, error, loadSessions, newSession, selectSession, deleteSession, sendMessage } = useChat()
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [activeArtifact, setActiveArtifact] = useState<{ type: 'html' | 'markdown'; content: string } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadSessions()
    api.health().then(setHealth).catch(() => {})
  }, [loadSessions])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleNewSession = async () => {
    setActiveArtifact(null)
    await newSession()
  }

  const handleViewArtifact = (msg: Message) => {
    if (msg.artifact) setActiveArtifact(msg.artifact)
  }

  const showArtifactPanel = !!activeArtifact

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        onNew={handleNewSession}
        onSelect={s => { setActiveArtifact(null); selectSession(s) }}
        onDelete={deleteSession}
        provider={health?.llm_provider ?? '…'}
      />

      {/* Main chat area */}
      <div className={`flex flex-col flex-1 min-w-0 ${showArtifactPanel ? 'w-1/2' : 'w-full'}`}>
        {/* Top bar */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-950 flex-shrink-0">
          <h2 className="text-sm font-medium text-gray-300 truncate">
            {activeSession?.title ?? 'Lenny Growth Assistant'}
          </h2>
          <div className="flex items-center gap-3">
            {health && (
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${health.db_connected ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-xs text-gray-500">
                  {health.index_chunks} chunks · {health.llm_provider}
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
          {!activeSession ? (
            <EmptyState onNewChat={handleNewSession} />
          ) : messages.length === 0 && !loading ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 text-sm">Send a message to get started</p>
            </div>
          ) : (
            messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} onViewArtifact={handleViewArtifact} />
            ))
          )}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-lenny-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">L</div>
              <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1 items-center h-5">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="mx-auto max-w-md bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-sm text-red-300">
              ⚠️ {error}
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        {/* Input */}
        {activeSession && <ChatInput onSend={sendMessage} disabled={loading} />}
      </div>

      {/* Artifact panel */}
      {showArtifactPanel && activeArtifact && (
        <div className="w-1/2 flex-shrink-0 border-l border-gray-800">
          <ArtifactViewer artifact={activeArtifact} onClose={() => setActiveArtifact(null)} />
        </div>
      )}
    </div>
  )
}
