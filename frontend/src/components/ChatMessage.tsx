import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '../api/client'

interface Props {
  message: Message
  onViewArtifact: (msg: Message) => void
}

export default function ChatMessage({ message, onViewArtifact }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-lenny-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-1">
          L
        </div>
      )}

      <div className={`max-w-[75%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-lenny-500 text-white rounded-tr-sm'
              : 'bg-gray-800 text-gray-100 rounded-tl-sm'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-lenny text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Artifact button */}
        {message.artifact && (
          <button
            onClick={() => onViewArtifact(message)}
            className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-xs text-gray-300 transition-colors"
          >
            <span>{message.artifact.type === 'html' ? '🌐' : '📄'}</span>
            <span>View {message.artifact.type.toUpperCase()} Artifact</span>
            <span className="text-gray-500">→</span>
          </button>
        )}

        {/* Sources */}
        {!isUser && message.sources.length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </summary>
            <div className="mt-1 space-y-1">
              {message.sources.map((s, i) => (
                <div key={i} className="text-xs bg-gray-800 rounded px-2 py-1">
                  <span className="text-lenny-500 font-medium">{s.source}</span>
                  {s.url && (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="ml-1 text-gray-500 hover:text-gray-400">↗</a>
                  )}
                  <p className="text-gray-500 mt-0.5 line-clamp-2">{s.excerpt}</p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 text-xs font-bold flex-shrink-0 mt-1">
          U
        </div>
      )}
    </div>
  )
}
