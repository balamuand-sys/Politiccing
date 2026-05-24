import { useState, useEffect, useCallback } from 'react'
import { Search, Upload, Globe, Filter, X } from 'lucide-react'
import { api } from '@/lib/api'
import DocumentCard from '@/components/documents/DocumentCard'
import UploadZone from '@/components/documents/UploadZone'
import ScrapingProgress from '@/components/documents/ScrapingProgress'
import { cn } from '@/lib/utils'

interface Doc {
  id: number
  title: string
  meeting_date?: string
  committee?: string
  document_type?: string
  source?: string
  created_at: string
}

const DOC_TYPES = [
  { value: '', label: 'Alle typer' },
  { value: 'innkalling', label: 'Innkalling' },
  { value: 'saksdokument', label: 'Saksdokument' },
  { value: 'protokoll', label: 'Protokoll' },
  { value: 'vedlegg', label: 'Vedlegg' },
]

export default function DocumentLibrary() {
  const [docs, setDocs] = useState<Doc[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState(false)
  const [docType, setDocType] = useState('')
  const [committee, setCommittee] = useState('')
  const [committees, setCommittees] = useState<string[]>([])
  const [showUpload, setShowUpload] = useState(false)
  const [showScraping, setShowScraping] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    fetchDocs()
    api.get('/documents/committees/list')
      .then((r) => setCommittees(r.data))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docType, committee])

  async function fetchDocs() {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (docType) params.document_type = docType
      if (committee) params.committee = committee
      const res = await api.get('/documents', { params })
      setDocs(res.data)
    } catch {} finally {
      setLoading(false)
    }
  }

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchMode(false)
      fetchDocs()
      return
    }
    setSearchMode(true)
    setLoading(true)
    try {
      const res = await api.get('/documents/search', { params: { q: searchQuery } })
      // Search returns {document_id, title, ...} format - deduplicate by doc ID
      const seen = new Set<number>()
      const deduped = res.data
        .filter((r: {document_id: number}) => {
          if (seen.has(r.document_id)) return false
          seen.add(r.document_id)
          return true
        })
        .map((r: {document_id: number; title: string; meeting_date?: string; committee?: string; chunk_text: string}) => ({
          id: r.document_id,
          title: r.title,
          meeting_date: r.meeting_date,
          committee: r.committee,
          created_at: '',
        }))
      setDocs(deduped)
    } catch {} finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery])

  function clearSearch() {
    setSearchQuery('')
    setSearchMode(false)
    fetchDocs()
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dokumentbibliotek</h1>
          <p className="text-sm text-gray-500 mt-0.5">{docs.length} dokumenter</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => setShowScraping(true)}>
            <Globe size={15} />
            Skrap møteportal
          </button>
          <button className="btn-primary" onClick={() => setShowUpload(true)}>
            <Upload size={15} />
            Last opp PDF
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            className="input pl-9 pr-9"
            placeholder="Semantisk søk: «alle saker om barnehage de siste 2 årene»..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          {searchQuery && (
            <button className="absolute right-2 top-1/2 -translate-y-1/2 btn-ghost p-1" onClick={clearSearch}>
              <X size={14} />
            </button>
          )}
        </div>
        <button className="btn-primary px-4" onClick={handleSearch}>Søk</button>
        <button
          className={cn('btn-secondary', showFilters && 'bg-hoyre-blue-pale dark:bg-hoyre-blue/20 border-hoyre-blue')}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter size={15} />
          Filter
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-3 mb-4 p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <div className="flex flex-col gap-1">
            <label className="label text-xs">Dokumenttype</label>
            <select
              className="input text-sm py-1.5"
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
            >
              {DOC_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          {committees.length > 0 && (
            <div className="flex flex-col gap-1">
              <label className="label text-xs">Utvalg</label>
              <select
                className="input text-sm py-1.5"
                value={committee}
                onChange={(e) => setCommittee(e.target.value)}
              >
                <option value="">Alle utvalg</option>
                {committees.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}
          {(docType || committee) && (
            <button
              className="btn-ghost self-end"
              onClick={() => { setDocType(''); setCommittee('') }}
            >
              <X size={14} />
              Nullstill filter
            </button>
          )}
        </div>
      )}

      {searchMode && (
        <div className="mb-3 text-sm text-gray-500 flex items-center gap-2">
          <Search size={13} />
          Semantisk søkeresultat for «{searchQuery}»
          <button className="text-hoyre-blue hover:underline text-xs" onClick={clearSearch}>Vis alle</button>
        </div>
      )}

      {/* Document grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : docs.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <div className="text-4xl mb-3">📄</div>
          <p className="font-medium">Ingen dokumenter ennå</p>
          <p className="text-sm mt-1">Last opp en PDF eller skrap fra møteportalen</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {docs.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} />
          ))}
        </div>
      )}

      {/* Modals */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md">
            <UploadZone onUploaded={fetchDocs} onClose={() => setShowUpload(false)} />
          </div>
        </div>
      )}

      {showScraping && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-lg">
            <ScrapingProgress onClose={() => setShowScraping(false)} onDone={fetchDocs} />
          </div>
        </div>
      )}
    </div>
  )
}
