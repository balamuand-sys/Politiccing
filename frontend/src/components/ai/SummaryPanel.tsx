import { useState, useEffect, useRef } from 'react'
import { Sparkles, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import * as Slider from '@radix-ui/react-slider'
import { api, streamSSE } from '@/lib/api'
import { cn } from '@/lib/utils'

interface SummaryPanelProps {
  documentId: number
}

function lengthLabel(v: number): string {
  if (v <= 20) return '3 kulepunkter'
  if (v <= 40) return 'Kort sammendrag'
  if (v <= 60) return 'Middels detaljert'
  if (v <= 80) return 'Detaljert analyse'
  return 'Grundig analyse'
}

export default function SummaryPanel({ documentId }: SummaryPanelProps) {
  const [length, setLength] = useState(50)
  const [text, setText] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<{id: number; summary_text: string; length_setting: number; created_at: string}[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const cancelRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    fetchLatestSummary()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId])

  async function fetchLatestSummary() {
    try {
      const res = await api.get(`/documents/${documentId}/summaries`)
      setHistory(res.data)
      if (res.data.length > 0) {
        setText(res.data[0].summary_text)
        setLength(res.data[0].length_setting)
      }
    } catch {}
  }

  function generate() {
    if (streaming) {
      cancelRef.current?.()
      return
    }
    setText('')
    setError(null)
    setStreaming(true)

    cancelRef.current = streamSSE(
      `/api/documents/${documentId}/summarize`,
      (chunk) => setText((t) => t + chunk),
      () => {
        setStreaming(false)
        fetchLatestSummary()
      },
      (err) => {
        setError(err)
        setStreaming(false)
      },
      'POST',
      { length_setting: length },
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Sparkles size={16} className="text-hoyre-blue" />
          Oppsummering
        </h3>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{lengthLabel(length)}</span>
          <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{length}</span>
        </div>
      </div>

      {/* Slider */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Kortfattet</span>
          <span>Grundig</span>
        </div>
        <Slider.Root
          className="relative flex items-center select-none touch-none w-full h-5"
          value={[length]}
          min={1}
          max={100}
          step={1}
          onValueChange={([v]) => setLength(v)}
        >
          <Slider.Track className="bg-gray-200 dark:bg-gray-700 relative grow rounded-full h-2">
            <Slider.Range className="absolute bg-hoyre-blue rounded-full h-full" />
          </Slider.Track>
          <Slider.Thumb className="block w-5 h-5 bg-hoyre-blue border-2 border-white shadow-md rounded-full focus:outline-none focus:ring-2 focus:ring-hoyre-blue/40 cursor-grab" />
        </Slider.Root>
      </div>

      <button
        className={cn('btn-primary w-full', streaming && 'bg-red-600 hover:bg-red-700')}
        onClick={generate}
      >
        {streaming ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Avbryt
          </>
        ) : text ? (
          <>
            <RefreshCw size={14} />
            Regenerer
          </>
        ) : (
          <>
            <Sparkles size={14} />
            Generer oppsummering
          </>
        )}
      </button>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {text && (
        <div className="prose prose-sm dark:prose-invert max-w-none bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 streaming-text text-sm leading-relaxed">
          {text}
          {streaming && <span className="inline-block w-1.5 h-4 bg-hoyre-blue ml-0.5 animate-pulse rounded-sm" />}
        </div>
      )}

      {history.length > 1 && (
        <div>
          <button
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            onClick={() => setShowHistory(!showHistory)}
          >
            {showHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {history.length - 1} tidligere oppsummeringer
          </button>
          {showHistory && (
            <div className="mt-2 space-y-2">
              {history.slice(1).map((s) => (
                <div
                  key={s.id}
                  className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-xs text-gray-600 dark:text-gray-400 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => setText(s.summary_text)}
                >
                  <div className="text-gray-400 mb-1">Lengde: {s.length_setting} — {new Date(s.created_at).toLocaleDateString('nb-NO')}</div>
                  <div className="line-clamp-3">{s.summary_text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
