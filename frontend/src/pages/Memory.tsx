import { useState, useEffect } from 'react'
import { Plus, Trash2, Sparkles, Search, Mic, FileText, Brain } from 'lucide-react'
import * as Tabs from '@radix-ui/react-tabs'
import { api } from '@/lib/api'
import { cn, truncate } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

interface StyleExample {
  id: number
  content_type: string
  example_text: string
  created_at: string
}

interface PoliticalContext {
  id: number
  topic: string
  stance: string
  notes?: string
}

interface SearchResult {
  document_id: number
  title: string
  chunk_text: string
  score: number
  meeting_date?: string
  committee?: string
}

export default function Memory() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Brain size={24} className="text-hoyre-blue" />
          Kontekst og hukommelse
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Lagre din skrivestil, politiske standpunkter og søk på tvers av alle dokumenter
        </p>
      </div>

      <Tabs.Root defaultValue="style">
        <Tabs.List className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
          {[
            { value: 'style', label: 'Min skrivestil' },
            { value: 'political', label: 'Politiske standpunkter' },
            { value: 'search', label: 'Søk i saker' },
          ].map(({ value, label }) => (
            <Tabs.Trigger
              key={value}
              value={value}
              className={cn(
                'px-5 py-3 text-sm font-medium border-b-2 transition-colors',
                'data-[state=active]:border-hoyre-blue data-[state=active]:text-hoyre-blue',
                'data-[state=inactive]:border-transparent data-[state=inactive]:text-gray-500 data-[state=inactive]:hover:text-gray-700 dark:data-[state=inactive]:hover:text-gray-300',
              )}
            >
              {label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        <Tabs.Content value="style"><StyleMemoryTab /></Tabs.Content>
        <Tabs.Content value="political"><PoliticalContextTab /></Tabs.Content>
        <Tabs.Content value="search"><SemanticSearchTab /></Tabs.Content>
      </Tabs.Root>
    </div>
  )
}

function StyleMemoryTab() {
  const [examples, setExamples] = useState<StyleExample[]>([])
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [newType, setNewType] = useState<'tale' | 'leserinnlegg'>('tale')
  const [newText, setNewText] = useState('')

  useEffect(() => {
    api.get('/memory/style').then((r) => setExamples(r.data)).catch(() => {})
  }, [])

  async function addExample() {
    if (!newText.trim()) return
    try {
      const res = await api.post('/memory/style', { content_type: newType, example_text: newText })
      setExamples((prev) => [res.data, ...prev])
      setNewText('')
      setShowAdd(false)
    } catch {}
  }

  async function deleteExample(id: number) {
    await api.delete(`/memory/style/${id}`)
    setExamples((prev) => prev.filter((e) => e.id !== id))
  }

  async function analyzeStyle() {
    setAnalyzing(true)
    setAnalysis(null)
    try {
      const res = await api.post('/memory/style/analyze')
      setAnalysis(res.data.analysis)
    } catch (e: unknown) {
      setAnalysis('Feil: ' + (e as Error).message)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{examples.length} lagrede eksempler</p>
        <div className="flex gap-2">
          <button className="btn-secondary text-xs" onClick={analyzeStyle} disabled={analyzing || examples.length === 0}>
            <Sparkles size={13} />
            {analyzing ? 'Analyserer...' : 'Analyser min stil'}
          </button>
          <button className="btn-primary text-xs" onClick={() => setShowAdd(!showAdd)}>
            <Plus size={13} />
            Legg til eksempel
          </button>
        </div>
      </div>

      {showAdd && (
        <div className="card p-4 space-y-3">
          <div className="flex gap-2">
            {(['tale', 'leserinnlegg'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setNewType(t)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                  newType === t
                    ? 'bg-hoyre-blue text-white border-transparent'
                    : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400',
                )}
              >
                {t === 'tale' ? <Mic size={11} /> : <FileText size={11} />}
                {t === 'tale' ? 'Tale' : 'Leserinnlegg'}
              </button>
            ))}
          </div>
          <textarea
            className="input min-h-32 text-sm"
            placeholder="Lim inn en tale eller et leserinnlegg her..."
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
          />
          <div className="flex gap-2">
            <button className="btn-primary text-sm" onClick={addExample}>Lagre</button>
            <button className="btn-secondary text-sm" onClick={() => setShowAdd(false)}>Avbryt</button>
          </div>
        </div>
      )}

      {analysis && (
        <div className="card p-4 bg-hoyre-blue-pale dark:bg-hoyre-blue/10 border-hoyre-blue/30">
          <div className="flex items-center gap-2 mb-2 font-medium text-sm">
            <Sparkles size={14} className="text-hoyre-blue" />
            Stilanalyse
          </div>
          <p className="text-sm whitespace-pre-wrap">{analysis}</p>
        </div>
      )}

      <div className="space-y-3">
        {examples.map((ex) => (
          <div key={ex.id} className="card p-4 group">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={cn(
                    'badge',
                    ex.content_type === 'tale'
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                      : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
                  )}>
                    {ex.content_type === 'tale' ? <Mic size={10} className="mr-1" /> : <FileText size={10} className="mr-1" />}
                    {ex.content_type === 'tale' ? 'Tale' : 'Leserinnlegg'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(ex.created_at).toLocaleDateString('nb-NO')}
                  </span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                  {ex.example_text}
                </p>
              </div>
              <button
                onClick={() => deleteExample(ex.id)}
                className="btn-ghost p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PoliticalContextTab() {
  const [items, setItems] = useState<PoliticalContext[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [topic, setTopic] = useState('')
  const [stance, setStance] = useState('')
  const [notes, setNotes] = useState('')
  const [editId, setEditId] = useState<number | null>(null)

  useEffect(() => {
    api.get('/memory/political-context').then((r) => setItems(r.data)).catch(() => {})
  }, [])

  async function save() {
    if (!topic.trim() || !stance.trim()) return
    try {
      if (editId) {
        const res = await api.put(`/memory/political-context/${editId}`, { topic, stance, notes })
        setItems((prev) => prev.map((i) => i.id === editId ? res.data : i))
      } else {
        const res = await api.post('/memory/political-context', { topic, stance, notes })
        setItems((prev) => [...prev, res.data])
      }
      setTopic(''); setStance(''); setNotes(''); setShowAdd(false); setEditId(null)
    } catch {}
  }

  function startEdit(item: PoliticalContext) {
    setTopic(item.topic); setStance(item.stance); setNotes(item.notes || '')
    setEditId(item.id); setShowAdd(true)
  }

  async function del(id: number) {
    await api.delete(`/memory/political-context/${id}`)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{items.length} standpunkter</p>
        <button className="btn-primary text-xs" onClick={() => { setShowAdd(!showAdd); setEditId(null); setTopic(''); setStance(''); setNotes('') }}>
          <Plus size={13} />
          Legg til standpunkt
        </button>
      </div>

      {showAdd && (
        <div className="card p-4 space-y-3">
          <div>
            <label className="label">Tema</label>
            <input className="input" placeholder="f.eks. Eiendomsskatt" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
          <div>
            <label className="label">Standpunkt</label>
            <input className="input" placeholder="f.eks. Høyre vil fjerne eiendomsskatten" value={stance} onChange={(e) => setStance(e.target.value)} />
          </div>
          <div>
            <label className="label">Notater (valgfritt)</label>
            <textarea className="input text-sm" rows={2} placeholder="Utdypende notater..." value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary text-sm" onClick={save}>{editId ? 'Oppdater' : 'Lagre'}</button>
            <button className="btn-secondary text-sm" onClick={() => { setShowAdd(false); setEditId(null) }}>Avbryt</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.id} className="card p-4 group flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="font-medium text-sm">{item.topic}</div>
              <div className="text-sm text-hoyre-blue mt-0.5">{item.stance}</div>
              {item.notes && <div className="text-xs text-gray-500 mt-1">{item.notes}</div>}
            </div>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="btn-ghost p-1 text-xs" onClick={() => startEdit(item)}>Rediger</button>
              <button className="btn-ghost p-1 text-gray-400 hover:text-red-500" onClick={() => del(item.id)}>
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-6">
            Ingen standpunkter ennå. Legg til dine politiske posisjoner for å forbedre AI-genereringen.
          </p>
        )}
      </div>
    </div>
  )
}

function SemanticSearchTab() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)

  async function search() {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await api.get('/memory/search', { params: { q: query, top_k: 15 } })
      setResults(res.data)
    } catch {} finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            className="input pl-9"
            placeholder="Finn alle saker om skole, barnehage, økonomi..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
          />
        </div>
        <button className="btn-primary" onClick={search} disabled={loading}>
          {loading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Search size={15} />}
          Søk
        </button>
      </div>

      <div className="space-y-3">
        {results.map((r, i) => (
          <div
            key={i}
            className="card p-4 cursor-pointer hover:border-hoyre-blue/40 transition-colors"
            onClick={() => navigate(`/documents/${r.document_id}`)}
          >
            <div className="font-medium text-sm mb-1">{r.title}</div>
            {r.meeting_date && (
              <div className="text-xs text-gray-500 mb-2">{r.meeting_date} {r.committee && `— ${r.committee}`}</div>
            )}
            <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3">
              {truncate(r.chunk_text, 200)}
            </p>
            <div className="mt-2 text-xs text-gray-400">
              Relevans: {Math.round(r.score * 100)}%
            </div>
          </div>
        ))}
        {results.length === 0 && query && !loading && (
          <p className="text-sm text-gray-400 text-center py-6">Ingen treff. Prøv et annet søkeuttrykk.</p>
        )}
      </div>
    </div>
  )
}
