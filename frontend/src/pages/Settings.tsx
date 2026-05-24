import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Key, Globe, User, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface SettingsData {
  api_key_set: boolean
  api_key_masked: string
  portal_url: string
  user_name: string
  party: string
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [portalUrl, setPortalUrl] = useState('')
  const [userName, setUserName] = useState('')
  const [party, setParty] = useState('Høyre')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [saved, setSaved] = useState(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get('/settings')
      .then((r) => {
        setSettings(r.data)
        setPortalUrl(r.data.portal_url || '')
        setUserName(r.data.user_name || '')
        setParty(r.data.party || 'Høyre')
      })
      .catch(() => {})
  }, [])

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const body: Record<string, string> = {
        portal_url: portalUrl,
        user_name: userName,
        party,
      }
      if (apiKey) body.api_key = apiKey

      await api.post('/settings', body)
      setSaved(true)
      setApiKey('')

      // Refresh
      const r = await api.get('/settings')
      setSettings(r.data)

      setTimeout(() => setSaved(false), 3000)
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function handleTestApi() {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await api.post('/settings/test-api')
      setTestResult({ ok: true, message: `Tilkobling OK — svar: "${res.data.response}"` })
    } catch (e: unknown) {
      setTestResult({ ok: false, message: (e as Error).message })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SettingsIcon size={24} className="text-hoyre-blue" />
          Innstillinger
        </h1>
        <p className="text-sm text-gray-500 mt-1">Konfigurer API-nøkkel og personlig informasjon</p>
      </div>

      <div className="space-y-6">
        {/* API Key */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Key size={16} className="text-hoyre-blue" />
            Anthropic API-nøkkel
          </h2>
          {settings?.api_key_set && (
            <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-3 py-2">
              <CheckCircle size={14} />
              API-nøkkel er satt: <code className="font-mono">{settings.api_key_masked}</code>
            </div>
          )}
          <div>
            <label className="label">
              {settings?.api_key_set ? 'Ny API-nøkkel (la stå tom for å beholde eksisterende)' : 'API-nøkkel'}
            </label>
            <input
              type="password"
              className="input font-mono"
              placeholder="sk-ant-api03-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoComplete="off"
            />
            <p className="text-xs text-gray-500 mt-1">
              Hent nøkkel på{' '}
              <span className="text-hoyre-blue">console.anthropic.com</span>
              {' '}→ API Keys. Lagres i <code className="font-mono text-xs">~/.politikerapp/.env</code>
            </p>
          </div>
          <button
            className="btn-secondary"
            onClick={handleTestApi}
            disabled={testing || (!settings?.api_key_set && !apiKey)}
          >
            {testing ? (
              <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            ) : (
              <CheckCircle size={14} />
            )}
            Test API-tilkobling
          </button>
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

        {/* Portal URL */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Globe size={16} className="text-hoyre-blue" />
            ACOS Møteportal
          </h2>
          <div>
            <label className="label">Møteportal-URL</label>
            <input
              type="url"
              className="input"
              placeholder="https://www.kommune.no/politikk/moter"
              value={portalUrl}
              onChange={(e) => setPortalUrl(e.target.value)}
            />
          </div>
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
          <p className="text-xs text-gray-500">
            Brukes i AI-generering for å personalisere taler og leserinnlegg.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300 flex items-start gap-2">
            <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
            {error}
          </div>
        )}

        <button
          className="btn-primary w-full py-2.5"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : saved ? (
            <>
              <CheckCircle size={16} />
              Lagret!
            </>
          ) : (
            'Lagre innstillinger'
          )}
        </button>

        {/* Info box */}
        <div className="bg-hoyre-blue-pale dark:bg-hoyre-blue/10 border border-hoyre-blue/20 rounded-xl p-4 text-sm">
          <p className="font-medium text-hoyre-blue mb-1">Personvern</p>
          <p className="text-gray-600 dark:text-gray-400">
            All data lagres lokalt på din Mac i <code className="font-mono text-xs">~/politikerapp/</code>.
            API-nøkkelen lagres i <code className="font-mono text-xs">~/.politikerapp/.env</code> og sendes
            kun direkte til Anthropic. Ingen data sendes til skyen.
          </p>
        </div>
      </div>
    </div>
  )
}
