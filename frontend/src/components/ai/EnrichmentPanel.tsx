import { useState, useEffect } from 'react'
import { Scale, Newspaper, Building2, TrendingUp, BookOpen, Plus, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '@/lib/api'
import { enrichmentTypeLabel, cn } from '@/lib/utils'

interface Enrichment {
  id: number
  enrichment_type: string
  content: string
  source_url?: string
  source_title?: string
  created_at: string
}

interface EnrichmentPanelProps {
  documentId: number
}

const ENRICHMENT_TYPES = [
  { key: 'law', label: 'Lover', icon: Scale, color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' },
  { key: 'news', label: 'Nyheter', icon: Newspaper, color: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300' },
  { key: 'municipal_comparison', label: 'Andre kommuner', icon: Building2, color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' },
  { key: 'budget', label: 'Økonomi', icon: TrendingUp, color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' },
  { key: 'research', label: 'Forskning', icon: BookOpen, color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
] as const

function EnrichmentCard({ enrichment }: { enrichment: Enrichment }) {
  const [expanded, setExpanded] = useState(false)
  const meta = ENRICHMENT_TYPES.find((t) => t.key === enrichment.enrichment_type)
  const Icon = meta?.icon || BookOpen

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className={cn('badge', meta?.color)}>
            <Icon size={11} className="mr-1" />
            {enrichmentTypeLabel(enrichment.enrichment_type)}
          </span>
          <span className="text-xs text-gray-500">
            {new Date(enrichment.created_at).toLocaleDateString('nb-NO')}
          </span>
        </div>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {expanded && (
        <div className="p-3 pt-0 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed border-t border-gray-100 dark:border-gray-700/50">
          {enrichment.content}
        </div>
      )}
    </div>
  )
}

export default function EnrichmentPanel({ documentId }: EnrichmentPanelProps) {
  const [enrichments, setEnrichments] = useState<Enrichment[]>([])
  const [loading, setLoading] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get(`/documents/${documentId}/enrichments`)
      .then((r) => setEnrichments(r.data))
      .catch(() => {})
  }, [documentId])

  async function enrich(types: string[]) {
    setLoading(types)
    setError(null)
    try {
      const res = await api.post(`/documents/${documentId}/enrich`, { types })
      const newEnrichments = res.data.filter((e: Record<string, unknown>) => !e.error)
      setEnrichments((prev) => [...newEnrichments, ...prev])
      const errors = res.data.filter((e: Record<string, unknown>) => e.error)
      if (errors.length) {
        setError(errors.map((e: Record<string, unknown>) => e.error).join('\n'))
      }
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setLoading([])
    }
  }

  const existingTypes = new Set(enrichments.map((e) => e.enrichment_type))

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Berik dokument</h3>

      {/* Type buttons */}
      <div className="grid grid-cols-2 gap-2">
        {ENRICHMENT_TYPES.map(({ key, label, icon: Icon, color }) => {
          const has = existingTypes.has(key)
          const isLoading = loading.includes(key)
          return (
            <button
              key={key}
              onClick={() => enrich([key])}
              disabled={loading.length > 0}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all',
                has
                  ? 'border-transparent ' + color
                  : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-hoyre-blue hover:text-hoyre-blue',
                loading.length > 0 && 'opacity-60 cursor-not-allowed',
              )}
            >
              {isLoading ? (
                <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <Icon size={12} />
              )}
              {label}
              {has && !isLoading && <Plus size={10} className="ml-auto opacity-60" />}
            </button>
          )
        })}
        <button
          onClick={() => enrich(ENRICHMENT_TYPES.map((t) => t.key))}
          disabled={loading.length > 0}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border col-span-2',
            'bg-hoyre-blue text-white border-transparent hover:bg-hoyre-blue-dark',
            loading.length > 0 && 'opacity-60 cursor-not-allowed',
          )}
        >
          {loading.length > 0 ? (
            <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Plus size={12} />
          )}
          Berik med alt
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-xs text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Results */}
      {enrichments.length > 0 && (
        <div className="space-y-2">
          {enrichments.map((e) => (
            <EnrichmentCard key={e.id} enrichment={e} />
          ))}
        </div>
      )}

      {enrichments.length === 0 && loading.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">
          Ingen berikelser ennå. Klikk en knapp over for å hente informasjon.
        </p>
      )}
    </div>
  )
}
