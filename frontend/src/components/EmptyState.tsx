interface Props {
  onNewChat: () => void
}

export default function EmptyState({ onNewChat }: Props) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
      <div className="w-16 h-16 rounded-2xl bg-lenny-500 flex items-center justify-center text-white text-3xl font-bold mb-6">
        L
      </div>
      <h1 className="text-2xl font-bold text-white mb-2">Lenny Growth Assistant</h1>
      <p className="text-gray-400 max-w-md mb-8 text-sm leading-relaxed">
        Ask product and growth questions grounded in Lenny's Podcast transcripts.
        Get essays, reports, and rendered artifacts — all sourced from real episodes.
      </p>
      <div className="grid grid-cols-1 gap-3 w-full max-w-sm">
        {[
          { icon: '💬', label: 'Grounded Q&A', desc: 'Answers cited to specific episodes' },
          { icon: '✍️', label: 'Ship 30 Essays', desc: 'Say "write an essay about..."' },
          { icon: '📄', label: 'Artifacts', desc: 'Say "create a markdown report..."' },
        ].map(item => (
          <div key={item.label} className="flex items-center gap-3 bg-gray-800 rounded-xl p-3 text-left">
            <span className="text-2xl">{item.icon}</span>
            <div>
              <p className="text-sm font-medium text-white">{item.label}</p>
              <p className="text-xs text-gray-500">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={onNewChat}
        className="mt-8 px-6 py-3 bg-lenny-500 hover:bg-lenny-600 text-white rounded-xl font-medium transition-colors"
      >
        Start a new chat
      </button>
    </div>
  )
}
