import { useState, useRef, useEffect } from 'react'

interface Props {
  onSend: (msg: string) => void
  disabled: boolean
}

const SUGGESTIONS = [
  'What is product-market fit and how do you know you have it?',
  'Write an essay about retention strategies for consumer apps',
  'Create a markdown report on growth frameworks from Lenny\'s podcast',
  'What do the best PMs have in common?',
  'Generate an HTML dashboard template for a growth metrics review',
]

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [value])

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="p-4 border-t border-gray-800 bg-gray-950">
      {/* Suggestion chips */}
      <div className="flex gap-2 mb-3 overflow-x-auto scrollbar-thin pb-1">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => { setValue(s); textareaRef.current?.focus() }}
            className="flex-shrink-0 text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded-full transition-colors"
          >
            {s.length > 45 ? s.slice(0, 45) + '…' : s}
          </button>
        ))}
      </div>

      <div className="flex gap-2 items-end bg-gray-800 rounded-xl p-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about product, growth, or say 'write an essay about...'"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 text-sm resize-none outline-none px-2 py-1 min-h-[36px]"
          aria-label="Chat input"
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          className="w-9 h-9 rounded-lg bg-lenny-500 hover:bg-lenny-600 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors flex-shrink-0"
          aria-label="Send message"
        >
          {disabled ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-xs text-gray-600 mt-2 text-center">
        Shift+Enter for new line · Answers grounded in Lenny's Podcast transcripts
      </p>
    </div>
  )
}
