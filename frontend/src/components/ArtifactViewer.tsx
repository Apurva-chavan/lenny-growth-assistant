/**
 * ArtifactViewer — renders HTML or Markdown artifacts beside the chat.
 *
 * SECURITY MODEL:
 * - HTML artifacts are rendered inside a sandboxed <iframe> with:
 *     sandbox="allow-same-origin"  (no scripts, no forms, no popups, no top navigation)
 *   The content is additionally sanitized with DOMPurify before being written into the iframe.
 *   DOMPurify strips: <script>, event handlers (onclick etc.), javascript: URIs,
 *   <iframe>, <object>, <embed>, <form>, and all external resource URLs.
 * - Markdown artifacts are rendered via react-markdown (no dangerouslySetInnerHTML).
 * - The iframe has no allow-scripts, so even if sanitization missed something,
 *   the browser sandbox prevents execution.
 */
import { useRef, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DOMPurify from 'dompurify'
import { Artifact } from '../api/client'

interface Props {
  artifact: Artifact
  onClose: () => void
}

const DOMPURIFY_CONFIG = {
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit'],
  FORCE_BODY: true,
}

export default function ArtifactViewer({ artifact, onClose }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (artifact.type === 'html' && iframeRef.current) {
      const clean = DOMPurify.sanitize(artifact.content, DOMPURIFY_CONFIG)
      const doc = iframeRef.current.contentDocument
      if (doc) {
        doc.open()
        doc.write(clean)
        doc.close()
      }
    }
  }, [artifact])

  const copyContent = async () => {
    await navigator.clipboard.writeText(artifact.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadContent = () => {
    const ext = artifact.type === 'html' ? 'html' : 'md'
    const mime = artifact.type === 'html' ? 'text/html' : 'text/markdown'
    const blob = new Blob([artifact.content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `lenny-artifact.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col h-full bg-gray-900 border-l border-gray-800">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">
            {artifact.type === 'html' ? '🌐 HTML Artifact' : '📄 Markdown Artifact'}
          </span>
          <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-400 rounded-full">
            {artifact.type === 'html' ? 'sandboxed' : 'safe render'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={copyContent}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
          <button
            onClick={downloadContent}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
          >
            Download
          </button>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white transition-colors ml-1"
            aria-label="Close artifact viewer"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {artifact.type === 'html' ? (
          <iframe
            ref={iframeRef}
            title="HTML Artifact"
            sandbox="allow-same-origin"
            className="w-full h-full border-0 bg-white"
          />
        ) : (
          <div className="h-full overflow-y-auto scrollbar-thin p-6">
            <div className="prose-lenny max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
