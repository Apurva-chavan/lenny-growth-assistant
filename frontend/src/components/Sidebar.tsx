import { Session } from '../api/client'

interface Props {
  sessions: Session[]
  activeSession: Session | null
  onNew: () => void
  onSelect: (s: Session) => void
  onDelete: (id: string) => void
  provider: string
}

export default function Sidebar({ sessions, activeSession, onNew, onSelect, onDelete, provider }: Props) {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-lenny-500 flex items-center justify-center text-white font-bold text-sm">L</div>
          <span className="font-semibold text-white text-sm">Lenny Growth Assistant</span>
        </div>
        <button
          onClick={onNew}
          className="w-full py-2 px-3 bg-lenny-500 hover:bg-lenny-600 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + New Chat
        </button>
      </div>

      {/* Sessions list */}
      <nav className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-gray-500 text-xs text-center mt-4">No chats yet</p>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors ${
              activeSession?.id === s.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
            onClick={() => onSelect(s)}
          >
            <span className="truncate flex-1">{s.title}</span>
            <button
              onClick={e => { e.stopPropagation(); onDelete(s.id) }}
              className="opacity-0 group-hover:opacity-100 ml-1 text-gray-500 hover:text-red-400 transition-opacity text-xs"
              aria-label="Delete session"
            >
              ✕
            </button>
          </div>
        ))}
      </nav>

      {/* Provider badge */}
      <div className="p-3 border-t border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400"></div>
          <span className="text-xs text-gray-400">Model: <span className="text-gray-200">{provider}</span></span>
        </div>
      </div>
    </aside>
  )
}
