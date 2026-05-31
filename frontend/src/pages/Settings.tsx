import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Key, User, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'

interface SettingsData {
  api_key_set: boolean
  voyage_key_set: boolean
  user_name: string
  party: string
  portal_url: string
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [userName, setUserName] = useState('')
  const [party, setParty] = useState('Høyre')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/settings').then((r) => {
      setSettings(r.data)
      setUserName(r.data.user_name || '')
      setParty(r.data.party || 'Høyre')
    }).catch(() => {})
  }, [])

  async function handleSave() {
    setSaving(true); setError(null); setSaved(false)
    try {
      await api.post('/settings', { user_name: userName, party })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function handleTestApi() {
    setTesting(true); setTestResult(null)
    try {
      const res = await api.post('/settings/test-api')
      setTestResult({ ok: true, message: `Tilkobling OK — svar: "${res.data.response}"` })
    } catch (e: unknown) {
      setTestResult({ ok: false, message: (e as Error).message })
    } finally {
      setTesting(false)
    }
  }

  const StatusBadge = ({ ok, label }: { ok: boolean; label: string }) => (
    <div className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 border ${
      ok
        ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
        : 'text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    }`}>
      {ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
      {label}: {ok ? 'Satt ✓' : 'Mangler'}
    </div>
  )

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SettingsIcon size={24} className="text-hoyre-blue" />
          Innstillinger
        </h1>
        <p className="text-sm text-gray-500 mt-1">Konfigurer appen og API-tilkoblinger</p>
      </div>

      <div className="space-y-6">

        {/* Environment variables status */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Key size={16} className="text-hoyre-blue" />
            API-nøkler (Vercel Environment Variables)
          </h2>
          <p className="text-sm text-gray-500">
            API-nøkler settes i Vercel-dashbordet, ikke her i appen. Gå til
            <a
              href="https://vercel.com/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              className="text-hoyre-blue hover:underline inline-flex items-center gap-1 ml-1"
            >
              vercel.com/dashboard <ExternalLink size={11} />
            </a>
            → ditt prosjekt → Settings → Environment Variables.
          </p>

          {settings && (
            <div className="space-y-2">
              <StatusBadge ok={settings.api_key_set} label="ANTHROPIC_API_KEY" />
              <StatusBadge ok={settings.voyage_key_set} label="VOYAGE_API_KEY" />
            </div>
          )}

          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 text-sm space-y-2 font-mono">
            <p className="font-sans text-xs text-gray-500 font-medium mb-2">Påkrevde env vars:</p>
            <div className="text-gray-700 dark:text-gray-300">ANTHROPIC_API_KEY=sk-ant-...</div>
            <div className="text-gray-700 dark:text-gray-300">VOYAGE_API_KEY=pa-...</div>
            <div className="text-gray-700 dark:text-gray-300">SUPABASE_URL=https://xxx.supabase.co</div>
            <div className="text-gray-700 dark:text-gray-300">SUPABASE_SERVICE_ROLE_KEY=eyJ...</div>
          </div>

          <div className="flex gap-2">
            <button
              className="btn-secondary"
              onClick={handleTestApi}
              disabled={testing}
            >
              {testing
                ? <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                : <CheckCircle size={14} />}
              Test Anthropic-tilkobling
            </button>
            <a
              href="https://console.anthropic.com/settings/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm"
            >
              <ExternalLink size={13} />
              Hent API-nøkkel
            </a>
          </div>

          {testResult && (
            <div className={`flex items-start gap-2 text-sm rounded-lg px-3 py-2 border ${
              testResult.ok
                ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                : 'text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            }`}>
              {testResult.ok ? <CheckCircle size={14} className="mt-0.5 flex-shrink-0" /> : <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />}
              {testResult.message}
            </div>
          )}
        </div>

        {/* User info */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <User size={16} className="text-hoyre-blue" />
            Personlig informasjon
          </h2>
          <div>
            <label className="label">Ditt navn</label>
            <input
              type="text"
              className="input"
              placeholder="Ola Nordmann"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Parti</label>
            <input
              type="text"
              className="input"
              value={party}
              onChange={(e) => setParty(e.target.value)}
            />
          </div>
          <p className="text-xs text-gray-500">Brukes i AI-generering for å personalisere taler og leserinnlegg.</p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300 flex items-start gap-2">
            <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <button className="btn-primary w-full py-2.5" onClick={handleSave} disabled={saving}>
          {saving
            ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            : saved
              ? <><CheckCircle size={16} />Lagret!</>
              : 'Lagre innstillinger'}
        </button>

        {/* Voyage AI info */}
        <div className="bg-hoyre-blue-pale dark:bg-hoyre-blue/10 border border-hoyre-blue/20 rounded-xl p-4 text-sm space-y-1">
          <p className="font-medium text-hoyre-blue">Voyage AI (semantisk søk)</p>
          <p className="text-gray-600 dark:text-gray-400">
            Voyage AI brukes for norsk semantisk søk og embedding av dokumenter.
            Hent gratis API-nøkkel på{' '}
            <a href="https://www.voyageai.com" target="_blank" rel="noopener noreferrer" className="text-hoyre-blue hover:underline inline-flex items-center gap-0.5">
              voyageai.com <ExternalLink size={10} />
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
