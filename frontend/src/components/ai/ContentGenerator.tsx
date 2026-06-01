import { useState, useRef } from 'react'
import { Mic, FileText, RefreshCw, BookmarkPlus, Sparkles } from 'lucide-react'
import * as Slider from '@radix-ui/react-slider'
import { api, streamSSE } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ContentGeneratorProps {
  documentId: number
  contentType: 'tale' | 'leserinnlegg'
}

function taleLength(v: number): string {
  if (v <= 20) return '2-minutters innlegg'
  if (v <= 40) return '5-minutters innlegg'
  if (v <= 60) return '10-minutters tale'
  if (v <= 80) return '15-minutters tale'
  return '20-minutters tale'
}

function leserinnleggLength(v: number): string {
  const words = Math.round(150 + (800 - 150) * (v - 1) / 99)
  return `ca. ${words} ord`
}

function toneLabel(v: number): string {
  if (v <= 20) return 'Saklig og faktabasert'
  if (v <= 40) return 'Saklig med personlighet'
  if (v <= 60) return 'Balansert'
  if (v <= 80) return 'Engasjert'
  return 'Appellerende'
}

export default function ContentGenerator({ documentId, contentType }: ContentGeneratorProps) {
  const [length, setLength] = useState(50)
  const [sentiment, setSentiment] = useState(50)
  const [text, setText] = useState('')
  const [editedText, setEditedText] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedId, setSavedId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [savedAsExample, setSavedAsExample] = useState(false)
  const cancelRef = useRef<(() => void) | null>(null)
  const contentIdRef = useRef<number | null>(null)

  const icon = contentType === 'tale' ? <Mic size={14} /> : <FileText size={14} />
  const label = contentType === 'tale' ? 'Tale' : 'Leserinnlegg'

  function generate() {
    if (streaming) {
      cancelRef.current?.()
      return
    }
    setText('')
    setEditedText('')
    setError(null)
    setSavedAsExample(false)
    setStreaming(true)
    contentIdRef.current = null

    cancelRef.current = streamSSE(
      `/api/documents/${documentId}/generate`,
      (chunk) => {
        setText((t) => t + chunk)
        setEditedText((t) => t + chunk)
      },
      (meta) => {
        setStreaming(false)
        if (meta?.content_id) {
          contentIdRef.current = meta.content_id as number
          setSavedId(meta.content_id as number)
        }
      },
      (err) => {
        setError(err)
        setStreaming(false)
      },
      'POST',
      { content_type: contentType, length_setting: length, sentiment_setting: sentiment },
    )
  }

  async function saveAsExample() {
    if (!contentIdRef.current) return
    setSaving(true)
    try {
      await api.post(`/documents/content/${contentIdRef.current}/save-as-example`)
      setSavedAsExample(true)
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold flex items-center gap-2">
        {icon}
        {label}
      </h3>

      {/* Length slider */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Lengde</span>
          <span className="font-medium text-hoyre-blue">
            {contentType === 'tale' ? taleLength(length) : leserinnleggLength(length)}
          </span>
        </div>
        <div className="flex justify-between text-xs text-gray-400">
          <span>{contentType === 'tale' ? '2 min' : '150 ord'}</span>
          <span>{contentType === 'tale' ? '20 min' : '800 ord'}</span>
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
          <Slider.Thumb className="block w-5 h-5 bg-hoyre-blue border-2 border-white shadow-md rounded-full focus:outline-none cursor-grab" />
        </Slider.Root>
      </div>

      {/* Tone slider */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500">Tone</span>
          <span className="font-medium text-hoyre-blue">{toneLabel(sentiment)}</span>
        </div>
        <div className="flex justify-between text-xs text-gray-400">
          <span>Saklig</span>
          <span>Appellerende</span>
        </div>
        <Slider.Root
          className="relative flex items-center select-none touch-none w-full h-5"
          value={[sentiment]}
          min={1}
          max={100}
          step={1}
          onValueChange={([v]) => setSentiment(v)}
        >
          <Slider.Track className="bg-gray-200 dark:bg-gray-700 relative grow rounded-full h-2">
            <Slider.Range className="absolute bg-hoyre-blue rounded-full h-full" />
          </Slider.Track>
          <Slider.Thumb className="block w-5 h-5 bg-hoyre-blue border-2 border-white shadow-md rounded-full focus:outline-none cursor-grab" />
        </Slider.Root>
      </div>

      <div className="flex gap-2">
        <button
          className={cn('btn-primary flex-1', streaming && 'bg-red-600 hover:bg-red-700')}
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
              Generer {label.toLowerCase()}
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {text && (
        <div className="space-y-3">
          <textarea
            className="input min-h-[300px] resize-y text-sm leading-relaxed font-mono"
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            placeholder=""
          />
          {streaming && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <div className="w-3 h-3 border border-hoyre-blue border-t-transparent rounded-full animate-spin" />
              Genererer...
            </div>
          )}
          {!streaming && savedId && (
            <button
              className={cn('btn-secondary w-full', savedAsExample && 'opacity-60')}
              onClick={saveAsExample}
              disabled={saving || savedAsExample}
            >
              <BookmarkPlus size={14} />
              {savedAsExample ? 'Lagret som eksempel!' : saving ? 'Lagrer...' : 'Lagre som stileksempel'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
