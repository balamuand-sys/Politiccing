import { useState } from 'react'
import { X, Globe, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

interface ScrapingProgressProps {
  onClose: () => void
  onDone: () => void
}

type Phase = 'config' | 'waiting_login' | 'scraping' | 'done' | 'error'

interface LogEntry {
  type: string
  message?: string
  title?: string
  current?: number
  total?: number
}

export default function ScrapingProgress({ onClose, onDone }: ScrapingProgressProps) {
  const [phase, setPhase] = useState<Phase>('config')
  const [portalUrl, setPortalUrl] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [log, setLog] = useState<LogEntry[]>([])
  const [downloaded, setDownloaded] = useState(0)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const addLog = (entry: LogEntry) => setLog((l) => [...l, entry])

  async function handleStartBrowser() {
    if (!portalUrl.trim()) return
    try {
      const res = await api.post('/scraping/start', { portal_url: portalUrl })
      setSessionId(res.data.session_id)
      setPhase('waiting_login')
    } catch (e: unknown) {
      setError((e as Error).message)
      setPhase('error')
    }
  }

  async function handleContinue() {
    if (!sessionId) return
    try {
      await api.post(`/scraping/continue/${sessionId}`)
      setPhase('scraping')

      const evtSource = new EventSource(`/api/scraping/stream/${sessionId}`)
      evtSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          addLog(data)
          if (data.type === 'progress') {
            setTotal(data.total || 0)
          }
          if (data.type === 'file_downloaded' || data.type === 'saved') {
            setDownloaded((d) => d + 1)
          }
          if (data.type === 'done') {
            setPhase('done')
            evtSource.close()
            onDone()
          }
          if (data.type === 'error') {
            setError(data.message)
            setPhase('error')
            evtSource.close()
          }
        } catch {}
      }
      evtSource.onerror = () => {
        setError('Tilkoblingen til serveren ble brutt')
        setPhase('error')
        evtSource.close()
      }
    } catch (e: unknown) {
      setError((e as Error).message)
      setPhase('error')
    }
  }

  return (
    <div className="p-6 space-y-5 w-full max-w-lg">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Globe size={20} className="text-hoyre-blue" />
          Skrap fra ACOS Møteportal
        </h2>
        <button onClick={onClose} className="btn-ghost p-1">
          <X size={18} />
        </button>
      </div>

      {phase === 'config' && (
        <div className="space-y-4">
          <div>
            <label className="label">Møteportal-URL</label>
            <input
              type="url"
              className="input"
              placeholder="https://kommune.no/politikk/moter"
              value={portalUrl}
              onChange={(e) => setPortalUrl(e.target.value)}
            />
          </div>
          <p className="text-sm text-gray-500">
            En nettleser åpnes automatisk. Du logger inn med BankID manuelt, og klikker "Fortsett" her etterpå.
          </p>
          <button
            className="btn-primary w-full"
            onClick={handleStartBrowser}
            disabled={!portalUrl.trim()}
          >
            Åpne nettleser
          </button>
        </div>
      )}

      {phase === 'waiting_login' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <Loader2 size={20} className="text-hoyre-blue animate-spin flex-shrink-0" />
            <div className="text-sm">
              <p className="font-medium text-blue-900 dark:text-blue-200">Venter på innlogging</p>
              <p className="text-blue-700 dark:text-blue-300 mt-1">
                Logg inn med BankID i nettleservinduet som åpnet seg. Klikk "Fortsett" når du er inne.
              </p>
            </div>
          </div>
          <button className="btn-primary w-full" onClick={handleContinue}>
            Fortsett — innlogging ferdig
          </button>
        </div>
      )}

      {phase === 'scraping' && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Loader2 size={16} className="animate-spin text-hoyre-blue" />
            <span>Skraper møteportal...</span>
          </div>
          {total > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{downloaded} dokumenter lastet ned</span>
                <span>{total} møter totalt</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-hoyre-blue h-2 rounded-full transition-all"
                  style={{ width: total > 0 ? `${Math.min(100, (downloaded / total) * 100)}%` : '5%' }}
                />
              </div>
            </div>
          )}
          <div className="max-h-48 overflow-y-auto space-y-1 bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
            {log.slice(-20).map((entry, i) => (
              <div key={i} className="text-xs text-gray-600 dark:text-gray-400 font-mono">
                {entry.message || entry.title || entry.type}
              </div>
            ))}
          </div>
        </div>
      )}

      {phase === 'done' && (
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <CheckCircle size={40} className="text-green-500" />
          <p className="font-medium">Ferdig! {downloaded} dokumenter lagret i databasen.</p>
          <button className="btn-primary" onClick={onClose}>Lukk</button>
        </div>
      )}

      {phase === 'error' && (
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-red-700 dark:text-red-300">Feil oppstod</p>
              <p className="text-red-600 dark:text-red-400 mt-1">{error}</p>
            </div>
          </div>
          <button className="btn-secondary w-full" onClick={() => { setPhase('config'); setError(null) }}>
            Prøv igjen
          </button>
        </div>
      )}
    </div>
  )
}
